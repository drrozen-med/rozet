from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional

import pytest

from orchestrator.integrations.opencode_tool_client import OpenCodeToolClient


class _ToolServer(HTTPServer):
    last_payload: Optional[dict] = None


def _make_handler():
    class Handler(BaseHTTPRequestHandler):
        server: _ToolServer  # type: ignore[assignment]

        def do_POST(self):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else b"{}"
            payload = json.loads(body.decode("utf-8"))
            self.server.last_payload = payload

            tool = payload.get("tool")
            args = payload.get("args", {})

            if tool == "bash":
                result = {
                    "success": True,
                    "callID": payload.get("callID", "bash-call"),
                    "result": {
                        "output": "command output",
                        "metadata": {
                            "output": "command output",
                            "exit": 0,
                        },
                    },
                }
            else:
                result = {
                    "success": True,
                    "callID": payload.get("callID", "write-call"),
                    "result": {
                        "output": args.get("content", ""),
                        "metadata": {
                            "filepath": args.get("filePath"),
                        },
                    },
                }

            encoded = json.dumps(result).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, _format, *_args):  # pragma: no cover - silence noisy server logs
            return

    return Handler


@pytest.fixture()
def tool_server():
    server = _ToolServer(("127.0.0.1", 0), _make_handler())
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join(timeout=1)


def _client(tool_server: _ToolServer) -> OpenCodeToolClient:
    host, port = tool_server.server_address
    base_url = f"http://{host}:{port}"
    return OpenCodeToolClient(
        working_dir=Path(".").resolve(),
        base_url=base_url,
        session_id="integration-session",
        provider="openai",
        model="openai/gpt-4o-mini",
    )


def test_remote_write_routes_to_http(tool_server):
    client = _client(tool_server)
    result = client.write_file("demo.txt", "hello remote")

    assert result["success"]
    assert tool_server.last_payload is not None
    assert tool_server.last_payload["tool"] == "write"
    assert tool_server.last_payload["args"]["filePath"] == "demo.txt"


def test_remote_bash_routes_to_http(tool_server):
    client = _client(tool_server)
    result = client.execute_bash("echo 'hi'", timeout=30)

    assert result.success
    assert result.stdout == "command output"
    assert tool_server.last_payload is not None
    assert tool_server.last_payload["tool"] == "bash"
    assert tool_server.last_payload["args"]["command"] == "echo 'hi'"

