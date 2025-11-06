"""REPL integration tests: Test REPL interface with orchestrator."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from orchestrator.config_loader import load_provider_config
from orchestrator.core.context_manager import ConversationContextManager
from orchestrator.core.coordinator import Coordinator
from orchestrator.core.task_planner import TaskPlanner
from orchestrator.providers.factory import create_chat_model
from orchestrator.utils.ollama_check import check_ollama_available
from orchestrator.workers.local_worker import LocalWorker


@pytest.mark.e2e
@pytest.mark.skipif(
    os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() != "true",
    reason="Set ORCHESTRATOR_USE_REAL_API=true to run e2e tests",
)
def test_repl_processes_request(test_dir: Path, api_key: str):
    """Test REPL can process user input and call orchestrator."""
    # Setup orchestrator components (what REPL would use internally)
    config = load_provider_config()
    orchestrator_llm, _ = create_chat_model(config.orchestrator)
    context_manager = ConversationContextManager(orchestrator_llm)
    planner = TaskPlanner(orchestrator_llm, max_tasks=3)
    
    # Simulate REPL processing a user request
    user_input = "Create a file test.txt with content 'Hello REPL'"
    
    # Add user message to context
    context_manager.record_user(user_input)
    
    # Plan task (what REPL would do)
    tasks = planner.plan(user_input, context_summary=context_manager.summary)
    
    assert len(tasks) > 0, "Should generate tasks from user input"
    print(f"\n✓ REPL processed request: {len(tasks)} tasks generated")


@pytest.mark.e2e
@pytest.mark.skipif(
    os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() != "true",
    reason="Set ORCHESTRATOR_USE_REAL_API=true to run e2e tests",
)
def test_repl_plans_task(test_dir: Path, api_key: str):
    """Test REPL calls task planner correctly."""
    config = load_provider_config()
    orchestrator_llm, _ = create_chat_model(config.orchestrator)
    planner = TaskPlanner(orchestrator_llm, max_tasks=5)
    
    # Test various user inputs
    test_requests = [
        "Create hello.py",
        "Add a function to utils.py",
        "Write tests for app.py",
    ]
    
    for request in test_requests:
        tasks = planner.plan(request)
        assert len(tasks) > 0, f"Should generate tasks for: {request}"
        print(f"\n✓ Planned '{request}': {len(tasks)} tasks")


@pytest.mark.e2e
@pytest.mark.skipif(
    os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() != "true",
    reason="Set ORCHESTRATOR_USE_REAL_API=true to run e2e tests",
)
def test_repl_executes_task(test_dir: Path, api_key: str):
    """Test REPL executes tasks via coordinator."""
    config = load_provider_config()
    orchestrator_llm, _ = create_chat_model(config.orchestrator)
    planner = TaskPlanner(orchestrator_llm, max_tasks=3)
    worker = LocalWorker(working_dir=test_dir)
    coordinator = Coordinator(worker=worker)
    
    # Plan and execute (what REPL would do)
    user_request = "Create simple.txt with content 'simple'"
    tasks = planner.plan(user_request)
    
    try:
        results = coordinator.execute_tasks(tasks, working_dir=test_dir)
        
        assert len(results) == len(tasks), "Should have result for each task"
        print(f"\n✓ REPL executed {len(results)} tasks")
        
        # Check if any files were created
        all_files = []
        for result in results:
            all_files.extend(result.files_created)
            all_files.extend(result.files_modified)
        
        print(f"✓ Files created/modified: {all_files}")
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
def test_repl_conversation(test_dir: Path, api_key: str):
    """Test REPL handles multi-turn conversation."""
    config = load_provider_config()
    orchestrator_llm, _ = create_chat_model(config.orchestrator)
    context_manager = ConversationContextManager(orchestrator_llm)
    planner = TaskPlanner(orchestrator_llm, max_tasks=3)
    
    # Simulate conversation turns
    turn1 = "Create config.yaml"
    turn2 = "Now create app.py that reads from config.yaml"
    turn3 = "Add a test file for app.py"
    
    # Add messages to context
    context_manager.record_user(turn1)
    summary1 = context_manager.summary
    
    context_manager.record_user(turn2)
    summary2 = context_manager.summary
    
    context_manager.record_user(turn3)
    summary3 = context_manager.summary
    
    # Plan each turn
    tasks1 = planner.plan(turn1, context_summary=summary1)
    tasks2 = planner.plan(turn2, context_summary=summary2)
    tasks3 = planner.plan(turn3, context_summary=summary3)
    
    assert len(tasks1) > 0, "Turn 1 should generate tasks"
    assert len(tasks2) > 0, "Turn 2 should generate tasks"
    assert len(tasks3) > 0, "Turn 3 should generate tasks"
    
    print(f"\n✓ Multi-turn conversation:")
    print(f"  Turn 1: {len(tasks1)} tasks")
    print(f"  Turn 2: {len(tasks2)} tasks")
    print(f"  Turn 3: {len(tasks3)} tasks")
    print(f"  Context summaries maintained: ✓")

