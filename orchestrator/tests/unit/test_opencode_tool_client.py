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


def test_opencode_tool_client_remote_read(monkeypatch, tmp_path):
    client = OpenCodeToolClient(
        working_dir=tmp_path,
        provider="openai",
        model="gpt-4o-mini",
        base_url="http://localhost:4096",
    )

    monkeypatch.setattr(client, "_call_remote_tool", lambda *args, **kwargs: {"output": "<file>content</file>"})

    def _fail_read(*_args, **_kwargs):
        raise RuntimeError("local read should not be called")

    monkeypatch.setattr(client._executor, "read_file", _fail_read)  # type: ignore[attr-defined]

    result = client.read_file("demo.txt")
    assert result["success"]
    assert result["content"].startswith("<file>")


def test_opencode_tool_client_remote_list(monkeypatch, tmp_path):
    client = OpenCodeToolClient(
        working_dir=tmp_path,
        provider="openai",
        model="gpt-4o-mini",
        base_url="http://localhost:4096",
    )

    fake_output = "path/\n  foo.txt\n  bar/\n    nested.txt\n"
    monkeypatch.setattr(
        client,
        "_call_remote_tool",
        lambda *args, **kwargs: {"output": fake_output, "metadata": {"count": 2}},
    )

    def _fail_list(*_args, **_kwargs):
        raise RuntimeError("local list should not be called")

    monkeypatch.setattr(client._executor, "list_files", _fail_list)  # type: ignore[attr-defined]

    result = client.list_files(".")
    assert result["success"]
    assert "foo.txt" in result["files"]
    assert "nested.txt" in result["files"]


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

