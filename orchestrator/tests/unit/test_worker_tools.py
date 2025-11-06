"""Unit tests for worker tool integration."""

from __future__ import annotations

from pathlib import Path

import pytest

from orchestrator.workers.local_worker import LocalWorker
from orchestrator.workers.tool_executor import ToolExecutor


def test_worker_initializes_with_tool_executor(test_dir: Path):
    """Test worker initializes with tool executor."""
    worker = LocalWorker(working_dir=test_dir)
    
    assert worker._tool_executor is not None
    assert isinstance(worker._tool_executor, ToolExecutor)
    assert worker._tool_executor.working_dir == test_dir


def test_worker_uses_provided_tool_executor(test_dir: Path):
    """Test worker can use a provided tool executor."""
    custom_executor = ToolExecutor(working_dir=test_dir)
    worker = LocalWorker(working_dir=test_dir, tool_executor=custom_executor)
    
    assert worker._tool_executor is custom_executor


def test_worker_prompt_includes_tool_instructions(test_dir: Path):
    """Test worker prompt includes tool usage instructions."""
    worker = LocalWorker(working_dir=test_dir)
    
    from orchestrator.core.task_planner import TaskSpec
    
    task = TaskSpec(
        task_id="T1",
        description="Test task",
        files=["test.py"],
        success_criteria=["File exists"],
    )
    
    prompt = worker._build_prompt(task)
    
    # Check that prompt includes tool instructions
    assert "AVAILABLE TOOLS:" in prompt
    assert "read_file" in prompt
    assert "write_file" in prompt
    assert "execute_bash" in prompt
    assert "list_files" in prompt
    assert "tools_used" in prompt


def test_worker_tool_executor_accessible(test_dir: Path):
    """Test worker's tool executor methods are accessible."""
    worker = LocalWorker(working_dir=test_dir)
    
    # Test that tool executor methods exist and are callable
    assert hasattr(worker._tool_executor, "read_file")
    assert hasattr(worker._tool_executor, "write_file")
    assert hasattr(worker._tool_executor, "execute_bash")
    assert hasattr(worker._tool_executor, "list_files")
    
    # Test that methods are callable
    assert callable(worker._tool_executor.read_file)
    assert callable(worker._tool_executor.write_file)
    assert callable(worker._tool_executor.execute_bash)
    assert callable(worker._tool_executor.list_files)


def test_worker_tool_executor_working_dir_matches(test_dir: Path):
    """Test worker and tool executor share the same working directory."""
    worker = LocalWorker(working_dir=test_dir)
    
    assert worker._working_dir == test_dir
    assert worker._tool_executor.working_dir == test_dir

