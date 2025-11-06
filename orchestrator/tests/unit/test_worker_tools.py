"""Unit tests for worker tool integration."""

from __future__ import annotations

from pathlib import Path
import json

import pytest

from orchestrator.workers.local_worker import LocalWorker
from orchestrator.workers.tool_executor import ToolExecutor
from orchestrator.core.task_planner import TaskSpec


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
    assert "TOOLS:" in prompt
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


def _make_simple_task() -> TaskSpec:
    return TaskSpec(
        task_id="T1",
        description="Test task",
        files=[],
        success_criteria=[],
    )


def test_worker_parses_plain_json_response(monkeypatch, test_dir: Path):
    """Worker should parse plain JSON responses."""
    worker = LocalWorker(working_dir=test_dir, verify_outputs=False)
    task = _make_simple_task()
    response = json.dumps(
        {
            "success": True,
            "files_modified": [],
            "files_created": [],
            "tests_run": [],
            "verification_passed": True,
            "errors": [],
            "logs": ""
        }
    )
    monkeypatch.setattr(worker, "_call_ollama", lambda prompt: response)
    result = worker.execute(task, working_dir=test_dir)
    assert result.success is True


def test_worker_parses_markdown_json_response(monkeypatch, test_dir: Path):
    """Worker should parse JSON embedded in markdown code fences."""
    worker = LocalWorker(working_dir=test_dir, verify_outputs=False)
    task = _make_simple_task()
    response = "Here you go:\n```json\n" + json.dumps(
        {
            "success": True,
            "files_modified": [],
            "files_created": [],
            "tests_run": [],
            "verification_passed": True,
            "errors": [],
            "logs": "Executed successfully"
        }
    ) + "\n```"
    monkeypatch.setattr(worker, "_call_ollama", lambda prompt: response)
    result = worker.execute(task, working_dir=test_dir)
    assert result.success is True
    assert "Executed successfully" in result.logs


def test_worker_handles_invalid_json_response(monkeypatch, test_dir: Path):
    """Worker should return failure when JSON cannot be parsed."""
    worker = LocalWorker(working_dir=test_dir, verify_outputs=False)
    task = _make_simple_task()
    response = "Oops, failed to produce JSON"
    monkeypatch.setattr(worker, "_call_ollama", lambda prompt: response)
    result = worker.execute(task, working_dir=test_dir)
    assert result.success is False
    assert any("Invalid JSON" in err for err in result.errors)

