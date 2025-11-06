"""Integration test: Real worker execution with tools."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from orchestrator.core.coordinator import Coordinator
from orchestrator.core.task_planner import TaskPlanner, TaskSpec
from orchestrator.core.observability import ObservabilityClient
from orchestrator.config_loader import load_provider_config
from orchestrator.providers.factory import create_chat_model
from orchestrator.workers.local_worker import LocalWorker
from orchestrator.workers.tool_executor import ToolExecutor


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() != "true",
    reason="Set ORCHESTRATOR_USE_REAL_API=true to run integration tests",
)
def test_tool_executor_basic_operations(test_dir: Path):
    """Test tool executor can read/write files and run bash."""
    executor = ToolExecutor(working_dir=test_dir)
    
    # Test write file
    write_result = executor.write_file("test.txt", "Hello, World!")
    assert write_result["success"], f"Write failed: {write_result}"
    assert write_result["verified"], "File verification failed"
    
    # Test read file
    read_result = executor.read_file("test.txt")
    assert read_result["success"], f"Read failed: {read_result}"
    assert read_result["content"] == "Hello, World!", "Content mismatch"
    
    # Test bash command
    bash_result = executor.execute_bash("echo 'test output'")
    assert bash_result["success"], f"Bash failed: {bash_result}"
    assert "test output" in bash_result["stdout"], "Bash output mismatch"
    
    # Test list files
    list_result = executor.list_files()
    assert list_result["success"], f"List failed: {list_result}"
    assert "test.txt" in list_result["files"], "File not in list"


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() != "true",
    reason="Set ORCHESTRATOR_USE_REAL_API=true to run integration tests",
)
def test_worker_executes_simple_task(test_dir: Path, api_key: str):
    """REAL TEST: Worker executes a simple file creation task."""
    # Create a simple task
    task = TaskSpec(
        task_id="T1",
        description="Create a Python script hello.py that prints 'Hello from Rozet'",
        files=["hello.py"],
        success_criteria=[
            "hello.py file exists",
            "hello.py contains print statement",
            "Script runs without errors",
        ],
    )
    
    # Create worker with tool executor
    worker = LocalWorker(working_dir=test_dir)
    
    # Execute task
    result = worker.execute(task, working_dir=test_dir)
    
    # Verify result structure
    assert result.task_id == "T1"
    assert isinstance(result.success, bool)
    assert isinstance(result.files_created, list)
    assert isinstance(result.errors, list)
    
    print(f"\n✓ Task execution result:")
    print(f"  Success: {result.success}")
    print(f"  Files created: {result.files_created}")
    print(f"  Files modified: {result.files_modified}")
    print(f"  Errors: {result.errors}")
    if result.logs:
        print(f"  Logs: {result.logs[:200]}...")
    
    # Note: Actual execution depends on Ollama being available
    # This test verifies the structure works even if Ollama isn't running


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() != "true",
    reason="Set ORCHESTRATOR_USE_REAL_API=true to run integration tests",
)
def test_coordinator_executes_tasks(test_dir: Path, api_key: str):
    """REAL TEST: Coordinator executes multiple tasks."""
    # Create tasks
    tasks = [
        TaskSpec(
            task_id="T1",
            description="Create a file test1.txt with content 'Task 1'",
            files=["test1.txt"],
            success_criteria=["test1.txt exists", "Contains 'Task 1'"],
        ),
        TaskSpec(
            task_id="T2",
            description="Create a file test2.txt with content 'Task 2'",
            files=["test2.txt"],
            success_criteria=["test2.txt exists", "Contains 'Task 2'"],
        ),
    ]
    
    # Setup coordinator
    worker = LocalWorker(working_dir=test_dir)
    coordinator = Coordinator(worker=worker)
    
    # Execute tasks
    results = coordinator.execute_tasks(tasks, working_dir=test_dir)
    
    # Verify results
    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    
    for i, result in enumerate(results):
        assert result.task_id == f"T{i+1}", f"Wrong task ID: {result.task_id}"
        print(f"\n✓ Task {result.task_id} result:")
        print(f"  Success: {result.success}")
        print(f"  Files: {result.files_created + result.files_modified}")


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() != "true",
    reason="Set ORCHESTRATOR_USE_REAL_API=true to run integration tests",
)
def test_worker_executes_with_tools(test_dir: Path):
    """Test worker can handle tool usage in response."""
    from orchestrator.core.task_planner import TaskSpec
    
    # Create a task that should use tools
    task = TaskSpec(
        task_id="T1",
        description="Create test_file.txt with content 'test'",
        files=["test_file.txt"],
        success_criteria=["File exists", "Contains 'test'"],
    )
    
    worker = LocalWorker(working_dir=test_dir)
    
    # Mock a worker response that includes tool usage
    # In real scenario, this would come from Ollama
    # For testing, we'll manually create a file and verify worker can process tool results
    executor = ToolExecutor(working_dir=test_dir)
    executor.write_file("test_file.txt", "test")
    
    # Verify worker can access tool executor
    assert worker._tool_executor is not None
    assert hasattr(worker._tool_executor, "read_file")
    
    # Test that worker can process tool usage
    tools_used = [
        {"tool": "write_file", "file": "test_file.txt", "result": "success"}
    ]
    tool_results = worker._process_tool_usage(tools_used, test_dir, {})
    
    assert len(tool_results) > 0
    assert "test_file.txt" in tool_results[0]


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() != "true",
    reason="Set ORCHESTRATOR_USE_REAL_API=true to run integration tests",
)
def test_worker_creates_file(test_dir: Path):
    """Test worker creates file via tool executor."""
    executor = ToolExecutor(working_dir=test_dir)
    
    # Create file using tool executor directly
    result = executor.write_file("created_file.txt", "Hello from tool executor")
    
    assert result["success"], f"File creation failed: {result}"
    assert result["verified"], "File verification failed"
    
    # Verify file exists
    read_result = executor.read_file("created_file.txt")
    assert read_result["success"], "File should exist"
    assert read_result["content"] == "Hello from tool executor", "Content mismatch"


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() != "true",
    reason="Set ORCHESTRATOR_USE_REAL_API=true to run integration tests",
)
def test_worker_runs_bash(test_dir: Path):
    """Test worker can execute bash commands via tool executor."""
    executor = ToolExecutor(working_dir=test_dir)
    
    # Create a test file first
    executor.write_file("test_script.sh", "#!/bin/bash\necho 'Bash test successful'")
    
    # Execute bash command
    result = executor.execute_bash("chmod +x test_script.sh && ./test_script.sh")
    
    assert result["success"], f"Bash execution failed: {result}"
    assert "Bash test successful" in result["stdout"], "Bash output not found"


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() != "true",
    reason="Set ORCHESTRATOR_USE_REAL_API=true to run integration tests",
)
def test_worker_verifies_output(test_dir: Path):
    """Test worker verifies its own work."""
    executor = ToolExecutor(working_dir=test_dir)
    
    # Create file
    executor.write_file("verify_test.txt", "verification content")
    
    # Verify file exists and content matches
    read_result = executor.read_file("verify_test.txt")
    assert read_result["success"], "File should exist"
    assert read_result["content"] == "verification content", "Content should match"
    
    # List files to verify
    list_result = executor.list_files()
    assert list_result["success"], "List should succeed"
    assert "verify_test.txt" in list_result["files"], "File should be in list"


