"""Integration tests for file locking with coordinator and workers."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from threading import Thread

import pytest

from orchestrator.core.coordinator import Coordinator, WorkerResult
from orchestrator.core.file_locking import FileLockManager
from orchestrator.core.task_planner import TaskSpec
from orchestrator.workers.local_worker import LocalWorker
from orchestrator.workers.tool_executor import ToolExecutor


@pytest.mark.integration
@pytest.mark.skip(reason="Requires Ollama and worker execution - test file locking separately")
def test_coordinator_uses_file_locking(tmp_path: Path):
    """Test that coordinator uses file locking when executing tasks."""
    tool_executor = ToolExecutor(working_dir=tmp_path)
    worker = LocalWorker(working_dir=tmp_path, tool_executor=tool_executor)
    lock_manager = FileLockManager()
    coordinator = Coordinator(
        worker=worker,
        file_lock_manager=lock_manager,
    )
    
    # Create a task that writes to a file
    task = TaskSpec(
        task_id="T1",
        description="Create test file",
        files=["test.txt"],
        success_criteria=["File test.txt exists"],
    )
    
    # Execute task
    results = coordinator.execute_tasks([task], working_dir=tmp_path)
    
    assert len(results) == 1
    assert results[0].success
    assert "test.txt" in results[0].files_created
    
    # Verify file was created
    test_file = tmp_path / "test.txt"
    assert test_file.exists()


@pytest.mark.integration
@pytest.mark.skip(reason="Requires Ollama and worker execution - test file locking separately")
def test_concurrent_tasks_same_file(tmp_path: Path):
    """Test that concurrent tasks on same file are serialized."""
    tool_executor = ToolExecutor(working_dir=tmp_path)
    worker = LocalWorker(working_dir=tmp_path, tool_executor=tool_executor)
    lock_manager = FileLockManager()
    coordinator = Coordinator(
        worker=worker,
        file_lock_manager=lock_manager,
    )
    
    # Create test file
    test_file = tmp_path / "concurrent.txt"
    test_file.write_text("0")
    
    # Create two tasks that modify the same file
    task1 = TaskSpec(
        task_id="T1",
        description="Increment value in file",
        files=["concurrent.txt"],
        success_criteria=["File contains incremented value"],
    )
    
    task2 = TaskSpec(
        task_id="T2",
        description="Increment value in file again",
        files=["concurrent.txt"],
        success_criteria=["File contains incremented value"],
    )
    
    # Execute concurrently
    results = []
    
    def execute_task(task):
        result = coordinator.execute_tasks([task], working_dir=tmp_path)
        results.extend(result)
    
    thread1 = Thread(target=execute_task, args=(task1,))
    thread2 = Thread(target=execute_task, args=(task2,))
    
    thread1.start()
    thread2.start()
    
    thread1.join()
    thread2.join()
    
    # Both tasks should complete
    assert len(results) == 2
    # File should exist and be valid
    assert test_file.exists()
    # No lock timeout errors
    assert all(not any("lock" in err.lower() for err in r.errors) for r in results)


@pytest.mark.integration
def test_lock_timeout_handling(tmp_path: Path):
    """Test that coordinator handles lock timeouts gracefully."""
    tool_executor = ToolExecutor(working_dir=tmp_path)
    worker = LocalWorker(working_dir=tmp_path, tool_executor=tool_executor)
    lock_manager = FileLockManager()
    coordinator = Coordinator(
        worker=worker,
        file_lock_manager=lock_manager,
    )
    
    test_file = tmp_path / "timeout.txt"
    test_file.write_text("initial")
    
    # Manually acquire lock
    lock = lock_manager.acquire_lock(str(test_file), timeout=1.0)
    
    # Create task that tries to access locked file
    task = TaskSpec(
        task_id="T1",
        description="Modify locked file",
        files=["timeout.txt"],
        success_criteria=["File modified"],
    )
    
    # Execute task (should timeout on lock)
    results = coordinator.execute_tasks([task], working_dir=tmp_path)
    
    # Task should fail with lock timeout
    assert len(results) == 1
    assert not results[0].success
    assert any("lock" in err.lower() for err in results[0].errors)
    
    # Release manual lock
    lock_manager.release_lock(str(test_file))

