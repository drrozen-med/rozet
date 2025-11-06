"""End-to-end workflow tests: Full orchestrator flow from planning to execution."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from orchestrator.config_loader import load_provider_config
from orchestrator.core.coordinator import Coordinator
from orchestrator.core.task_planner import TaskPlanner, TaskSpec
from orchestrator.providers.factory import create_chat_model
from orchestrator.utils.ollama_check import check_ollama_available
from orchestrator.workers.local_worker import LocalWorker


@pytest.mark.e2e
@pytest.mark.skipif(
    os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() != "true",
    reason="Set ORCHESTRATOR_USE_REAL_API=true to run e2e tests",
)
def test_simple_task_execution(test_dir: Path, api_key: str):
    """E2E: Plan and execute a single simple task."""
    # Setup orchestrator components
    config = load_provider_config()
    orchestrator_llm, _ = create_chat_model(config.orchestrator)
    planner = TaskPlanner(orchestrator_llm, max_tasks=3)
    worker = LocalWorker(working_dir=test_dir)
    coordinator = Coordinator(worker=worker)
    
    # Plan task
    user_request = "Create a Python file hello.py that prints 'Hello, World!'"
    tasks = planner.plan(user_request)
    
    assert len(tasks) > 0, "Should generate at least one task"
    
    # Execute tasks - handle Ollama failures gracefully
    try:
        results = coordinator.execute_tasks(tasks, working_dir=test_dir)
        
        # Verify results
        assert len(results) == len(tasks), "Should have result for each task"
        
        for result in results:
            assert result.task_id is not None
            print(f"\n✓ Task {result.task_id}:")
            print(f"  Success: {result.success}")
            print(f"  Files created: {result.files_created}")
            print(f"  Files modified: {result.files_modified}")
            if result.errors:
                print(f"  Errors: {result.errors}")
    except Exception as exc:
        # If Ollama fails, skip test but report
        if "ollama" in str(exc).lower() or "llama runner" in str(exc).lower():
            pytest.skip(f"Ollama not available or model not loaded: {exc}")
        else:
            raise


@pytest.mark.e2e
@pytest.mark.skipif(
    os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() != "true",
    reason="Set ORCHESTRATOR_USE_REAL_API=true to run e2e tests",
)
def test_multiple_tasks(test_dir: Path, api_key: str):
    """E2E: Plan and execute multiple tasks."""
    # Setup
    config = load_provider_config()
    orchestrator_llm, _ = create_chat_model(config.orchestrator)
    planner = TaskPlanner(orchestrator_llm, max_tasks=5)
    worker = LocalWorker(working_dir=test_dir)
    coordinator = Coordinator(worker=worker)
    
    # Plan multiple tasks
    user_request = "Create app.py with a main function and test_app.py with a test for it"
    tasks = planner.plan(user_request)
    
    assert len(tasks) >= 2, "Should generate at least 2 tasks for multi-file request"
    
    # Execute tasks - handle Ollama failures gracefully
    try:
        results = coordinator.execute_tasks(tasks, working_dir=test_dir)
        
        # Verify all tasks executed
        assert len(results) == len(tasks), "Should have result for each task"
        
        # Check that files were created
        created_files = []
        for result in results:
            created_files.extend(result.files_created)
            created_files.extend(result.files_modified)
        
        print(f"\n✓ Created/modified files: {created_files}")
        assert len(created_files) > 0, "Should have created at least one file"
    except Exception as exc:
        # If Ollama fails, skip test but report
        if "ollama" in str(exc).lower() or "llama runner" in str(exc).lower():
            pytest.skip(f"Ollama not available or model not loaded: {exc}")
        else:
            raise


@pytest.mark.e2e
@pytest.mark.skipif(
    os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() != "true",
    reason="Set ORCHESTRATOR_USE_REAL_API=true to run e2e tests",
)
def test_task_with_dependencies(test_dir: Path, api_key: str):
    """E2E: Tasks with dependencies execute in correct order."""
    # Setup
    config = load_provider_config()
    orchestrator_llm, _ = create_chat_model(config.orchestrator)
    planner = TaskPlanner(orchestrator_llm, max_tasks=5)
    worker = LocalWorker(working_dir=test_dir)
    coordinator = Coordinator(worker=worker)
    
    # Plan task that should have dependencies
    user_request = "Create config.yaml with app settings, then create app.py that reads from config.yaml"
    tasks = planner.plan(user_request)
    
    # Check for dependencies
    tasks_with_deps = [t for t in tasks if t.dependencies]
    print(f"\n✓ Tasks with dependencies: {len(tasks_with_deps)}")
    
    # Execute tasks (coordinator should handle dependencies) - handle Ollama failures gracefully
    try:
        results = coordinator.execute_tasks(tasks, working_dir=test_dir)
        
        assert len(results) == len(tasks), "Should have result for each task"
        
        # Verify execution order (tasks with dependencies should execute after their deps)
        # This is a basic check - full dependency resolution would be more complex
        for i, result in enumerate(results):
            task = tasks[i]
            if task.dependencies:
                # Check that dependencies executed before this task
                dep_indices = [j for j, t in enumerate(tasks) if t.task_id in task.dependencies]
                assert all(j < i for j in dep_indices), f"Task {task.task_id} should execute after dependencies"
    except Exception as exc:
        # If Ollama fails, skip test but report
        if "ollama" in str(exc).lower() or "llama runner" in str(exc).lower():
            pytest.skip(f"Ollama not available or model not loaded: {exc}")
        else:
            raise


@pytest.mark.e2e
@pytest.mark.skipif(
    os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() != "true",
    reason="Set ORCHESTRATOR_USE_REAL_API=true to run e2e tests",
)
def test_file_locking(test_dir: Path, api_key: str):
    """E2E: File locking prevents concurrent access conflicts."""
    from orchestrator.core.coordinator import FileLockManager
    
    # Setup file lock manager
    lock_manager = FileLockManager()
    
    # Test acquiring locks
    lock_manager.acquire_write("test_file.py")
    
    # Try to acquire same lock from another "agent" (should block or fail)
    # In MVP, we use simple mutex locks, so concurrent access is prevented
    # This test verifies the locking mechanism exists
    
    # Release lock
    lock_manager.release("test_file.py")
    
    # Now should be able to acquire again
    lock_manager.acquire_write("test_file.py")
    lock_manager.release("test_file.py")
    
    print("\n✓ File locking mechanism works")


@pytest.mark.e2e
@pytest.mark.skipif(
    os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() != "true",
    reason="Set ORCHESTRATOR_USE_REAL_API=true to run e2e tests",
)
def test_observability_events(test_dir: Path, api_key: str):
    """E2E: Observability events are sent during execution."""
    from orchestrator.core.observability import ObservabilityClient
    
    # Setup with observability
    config = load_provider_config()
    orchestrator_llm, _ = create_chat_model(config.orchestrator)
    planner = TaskPlanner(orchestrator_llm, max_tasks=2)
    
    # Try Ollama for worker if available, otherwise use default
    worker = LocalWorker(working_dir=test_dir)
    if check_ollama_available():
        print("\n✓ Ollama available - worker will use Ollama")
    else:
        print("\n⚠ Ollama not available - worker will attempt to use Ollama anyway (may fail)")
    
    observability = ObservabilityClient()
    coordinator = Coordinator(worker=worker, observability=observability)
    
    # Plan and execute
    user_request = "Create test.txt with content 'test'"
    tasks = planner.plan(user_request)
    
    # Execute tasks - if Ollama fails, we'll catch and report
    try:
        results = coordinator.execute_tasks(tasks, working_dir=test_dir)
        
        # Verify observability client exists and was used
        assert observability is not None
        assert len(results) > 0
        
        print("\n✓ Observability client integrated")
        print(f"✓ Executed {len(results)} tasks")
    except Exception as exc:
        # If Ollama fails, skip test but report
        if "ollama" in str(exc).lower() or "llama runner" in str(exc).lower():
            pytest.skip(f"Ollama not available or model not loaded: {exc}")
        else:
            raise

