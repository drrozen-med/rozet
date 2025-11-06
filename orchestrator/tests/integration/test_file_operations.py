"""Integration test: Real file operations.

These tests verify the orchestrator can actually read and write files.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from orchestrator.config_loader import load_provider_config
from orchestrator.core.task_planner import TaskPlanner
from orchestrator.providers.factory import create_chat_model


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() != "true",
    reason="Set ORCHESTRATOR_USE_REAL_API=true to run integration tests",
)
def test_plan_file_read_task(test_dir: Path, api_key: str):
    """Test planning a task that reads a file."""
    # Create test file
    test_file = test_dir / "test_config.yaml"
    test_file.write_text("""
orchestrator:
  provider: openai
  model: gpt-5-nano
""")
    
    config = load_provider_config()
    orchestrator_llm, system_prompt = create_chat_model(config.orchestrator)
    
    planner = TaskPlanner(
        llm=orchestrator_llm,
        system_prompt=system_prompt,
    )
    
    request = f"Read {test_file} and tell me what model is configured"
    
    tasks = planner.plan(request)
    
    # Verify task mentions the file
    all_files = [f for task in tasks for f in task.files]
    assert any(
        "test_config.yaml" in f or str(test_file) in f
        for f in all_files
    ), f"Should mention test file: {all_files}"
    
    print(f"\n✓ Planned file read task:")
    for task in tasks:
        print(f"  - {task.task_id}: {task.description}")
        if task.files:
            print(f"    Files: {task.files}")


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() != "true",
    reason="Set ORCHESTRATOR_USE_REAL_API=true to run integration tests",
)
def test_plan_file_write_task(test_dir: Path, api_key: str):
    """Test planning a task that writes a file."""
    config = load_provider_config()
    orchestrator_llm, system_prompt = create_chat_model(config.orchestrator)
    
    planner = TaskPlanner(
        llm=orchestrator_llm,
        system_prompt=system_prompt,
    )
    
    request = f"Create a Python script at {test_dir}/hello.py that prints 'Hello, World!'"
    
    tasks = planner.plan(request)
    
    # Verify task mentions creating/writing
    task_descriptions = " ".join([t.description.lower() for t in tasks])
    assert any(
        keyword in task_descriptions
        for keyword in ["create", "write", "script", "python"]
    ), f"Should mention creating/writing: {task_descriptions}"
    
    # Verify task mentions the file
    all_files = [f for task in tasks for f in task.files]
    assert any(
        "hello.py" in f.lower() or "hello" in f.lower()
        for f in all_files
    ), f"Should mention hello.py: {all_files}"
    
    print(f"\n✓ Planned file write task:")
    for task in tasks:
        print(f"  - {task.task_id}: {task.description}")
        if task.files:
            print(f"    Files: {task.files}")

