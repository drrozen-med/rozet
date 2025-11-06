"""Integration test: Real codebase summary scenario.

This test asks the orchestrator to summarize the orchestrator codebase itself.
It uses REAL LLM calls and REAL file operations.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from orchestrator.config_loader import load_provider_config
from orchestrator.core.context_manager import ConversationContextManager
from orchestrator.core.task_planner import TaskPlanner
from orchestrator.providers.factory import create_chat_model


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() != "true",
    reason="Set ORCHESTRATOR_USE_REAL_API=true to run integration tests",
)
def test_summarize_orchestrator_codebase(api_key: str):
    """REAL TEST: Ask orchestrator to summarize the orchestrator codebase.
    
    This test:
    1. Creates a real orchestrator instance
    2. Sends a real request to analyze the codebase
    3. Verifies the orchestrator actually reads files
    4. Verifies the response is accurate and useful
    """
    # Setup orchestrator
    config = load_provider_config()
    orchestrator_llm, system_prompt = create_chat_model(config.orchestrator)
    
    context_manager = ConversationContextManager(
        llm=orchestrator_llm,
        storage_path=Path("/tmp/test_orchestrator_context.jsonl"),
    )
    
    planner = TaskPlanner(
        llm=orchestrator_llm,
        system_prompt=system_prompt,
    )
    
    # Real request
    request = """
    Analyze the orchestrator codebase (orchestrator/ directory) and provide:
    1. Main components and their responsibilities
    2. How components interact
    3. Key design decisions
    4. Areas for improvement
    
    Focus on the core architecture, not implementation details.
    """
    
    # Plan tasks
    tasks = planner.plan(request)
    
    # Verify planning worked
    assert len(tasks) > 0, "Should have at least one task"
    assert len(tasks) <= 6, "Should not exceed max tasks"
    
    # Verify tasks are relevant
    task_descriptions = " ".join([t.description.lower() for t in tasks])
    assert any(
        keyword in task_descriptions
        for keyword in ["read", "analyze", "summarize", "file", "codebase"]
    ), f"Tasks should mention reading/analyzing: {task_descriptions}"
    
    # Verify task structure
    for task in tasks:
        assert task.task_id, f"Task {task} should have task_id"
        assert task.description, f"Task {task} should have description"
        assert isinstance(task.files, list), f"Task {task} should have files list"
        assert isinstance(task.success_criteria, list), f"Task {task} should have success_criteria"
    
    print(f"\n✓ Planned {len(tasks)} tasks:")
    for task in tasks:
        print(f"  - {task.task_id}: {task.description}")
        if task.files:
            print(f"    Files: {task.files}")
    
    # Test context management
    context_manager.add_message(request, f"Planned {len(tasks)} tasks")
    
    # Verify context was saved
    recent = context_manager.recent_messages
    assert len(recent) > 0, "Should have recent messages"
    
    print(f"\n✓ Context management working: {len(recent)} recent messages")


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() != "true",
    reason="Set ORCHESTRATOR_USE_REAL_API=true to run integration tests",
)
def test_plan_simple_file_operation(api_key: str):
    """REAL TEST: Plan a simple file operation task."""
    config = load_provider_config()
    orchestrator_llm, system_prompt = create_chat_model(config.orchestrator)
    
    planner = TaskPlanner(
        llm=orchestrator_llm,
        system_prompt=system_prompt,
    )
    
    request = "Create a Python script that reads config/providers.yaml and prints the orchestrator model name"
    
    tasks = planner.plan(request)
    
    # Verify planning
    assert len(tasks) >= 1, "Should have at least one task"
    
    # Verify task mentions relevant files
    all_files = [f for task in tasks for f in task.files]
    assert any(
        "providers.yaml" in f.lower() or "config" in f.lower()
        for f in all_files
    ), f"Should mention config file: {all_files}"
    
    # Verify success criteria
    all_criteria = [c for task in tasks for c in task.success_criteria]
    assert any(
        "print" in c.lower() or "output" in c.lower() or "model" in c.lower()
        for c in all_criteria
    ), f"Should have relevant success criteria: {all_criteria}"
    
    print(f"\n✓ Planned file operation task:")
    for task in tasks:
        print(f"  - {task.task_id}: {task.description}")
        if task.files:
            print(f"    Files: {task.files}")


if __name__ == "__main__":
    # Allow running directly for manual testing
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        os.environ["ORCHESTRATOR_USE_REAL_API"] = "true"
        pytest.main([__file__, "-v", "-s"])

