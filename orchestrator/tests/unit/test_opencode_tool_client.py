"""Tests for the OpenCode tool client and worker shim."""

from __future__ import annotations

from orchestrator.integrations.opencode_tool_client import OpenCodeToolClient
from orchestrator.workers.opencode_worker import OpenCodeToolWorker


def test_opencode_tool_client_write_and_read(tmp_path):
    client = OpenCodeToolClient(working_dir=tmp_path, provider="openai", model="gpt-4o-mini")

    write_result = client.write_file("demo.txt", "hello rozet")
    assert write_result["success"]

    read_result = client.read_file("demo.txt")
    assert read_result["success"]
    assert read_result["content"] == "hello rozet"


def test_opencode_worker_process_tool_usage(tmp_path):
    worker = OpenCodeToolWorker(working_dir=tmp_path, provider="openai", model="gpt-4o-mini")

    tools_used = [
        {"tool": "write_file", "file": "demo.txt", "content": "from worker"},
        {"tool": "list_files", "directory": ".", "pattern": "*.txt"},
        {"tool": "read_file", "file": "demo.txt"},
    ]
    result_data = {"success": True}

    logs = worker._process_tool_usage(tools_used, tmp_path, result_data)  # type: ignore[arg-type]

    assert (tmp_path / "demo.txt").read_text() == "from worker"
    assert any("write_file" in entry for entry in logs)
    assert result_data["success"] is True

