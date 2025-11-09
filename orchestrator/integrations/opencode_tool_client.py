"""Client for executing OpenCode tools from the Python orchestrator.

When an OpenCode server URL is provided the client will attempt to execute tools
via the REST API. If the request fails (or the dependency is unavailable) it
falls back to the local :class:`ToolExecutor`.
"""

from __future__ import annotations

import logging
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlencode

try:  # pragma: no cover - optional dependency
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

from orchestrator.workers.tool_executor import ToolExecutor

LOGGER = logging.getLogger(__name__)


@dataclass
class ToolExecutionResult:
    """Standardised result for tool executions."""

    success: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    error: Optional[str] = None


class OpenCodeToolClient:
    """Executes tools on behalf of the orchestrator with optional HTTP routing."""

    def __init__(
        self,
        *,
        working_dir: Path,
        base_url: Optional[str] = None,
        session_id: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        executor: Optional[ToolExecutor] = None,
    ) -> None:
        self._working_dir = working_dir
        self._base_url = base_url
        self._session_id = session_id
        self._provider = provider
        self._model = model
        self._executor = executor or ToolExecutor(working_dir=working_dir)

    # ------------------------------------------------------------------ #
    # File helpers
    # ------------------------------------------------------------------ #
    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write a file on disk."""
        remote = self._call_remote_tool(
            "write",
            {
                "filePath": path,
                "content": content,
            },
        )
        if remote:
            metadata = remote.get("metadata", {}) if isinstance(remote, dict) else {}
            return {
                "success": True,
                "file_path": metadata.get("filepath", path),
                "size": len(content),
                "verified": True,
            }
        return self._executor.write_file(path, content)

    def read_file(self, path: str) -> Dict[str, Any]:
        """Read a file from disk."""
        remote = self._call_remote_tool(
            "read",
            {
                "filePath": path,
            },
            timeout=120,
        )
        if remote:
            output = remote.get("output") if isinstance(remote, dict) else ""
            metadata = remote.get("metadata", {}) if isinstance(remote, dict) else {}
            return {
                "content": output or "",
                "exists": True,
                "success": True,
                "size": len(output or ""),
                "preview": metadata.get("preview"),
            }
        return self._executor.read_file(path)

    def list_files(self, directory: str = ".", pattern: str = "*") -> Dict[str, Any]:
        """List files relative to the working directory."""
        remote = self._call_remote_tool(
            "list",
            {
                "path": str(Path(directory)),
                "ignore": [],
            },
            timeout=60,
        )
        if remote:
            output = remote.get("output") if isinstance(remote, dict) else ""
            metadata = remote.get("metadata", {}) if isinstance(remote, dict) else {}
            files = [
                line.strip()
                for line in (output or "").splitlines()[1:]
                if line.strip() and not line.strip().endswith("/")
            ]
            return {
                "files": files,
                "success": True,
                "count": len(files),
                "metadata": metadata,
            }
        return self._executor.list_files(directory, pattern)

    # ------------------------------------------------------------------ #
    # Shell helpers
    # ------------------------------------------------------------------ #
    def execute_bash(self, command: str, timeout: int = 60) -> ToolExecutionResult:
        """Execute a bash command."""
        remote = self._call_remote_tool(
            "bash",
            {
                "command": command,
                "description": command,
                "timeout": max(int(timeout * 1000), 0),
            },
            timeout=max(timeout, 60),
        )
        if remote:
            metadata = remote.get("metadata", {}) if isinstance(remote, dict) else {}
            stdout = metadata.get("output") or remote.get("output", "") if isinstance(remote, dict) else ""
            stderr = metadata.get("stderr", "")
            return ToolExecutionResult(
                success=not metadata.get("error"),
                stdout=stdout,
                stderr=stderr,
                returncode=metadata.get("exit", 0),
                error=metadata.get("error"),
            )

        result = self._executor.execute_bash(command, timeout=timeout)
        return ToolExecutionResult(
            success=result.get("success", False),
            stdout=result.get("stdout", ""),
            stderr=result.get("stderr", ""),
            returncode=result.get("returncode", 0),
            error=result.get("error"),
        )

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _call_remote_tool(
        self,
        tool: str,
        args: Dict[str, Any],
        timeout: int = 120,
    ) -> Optional[Dict[str, Any]]:
        if not self._base_url or not requests or not self._provider or not self._model:
            return None

        query = urlencode({"directory": str(self._working_dir)})
        url = f"{self._base_url.rstrip('/')}/experimental/tool/execute?{query}"

        payload = {
            "tool": tool,
            "provider": self._provider,
            "model": self._model,
            "args": args,
            "sessionID": self._session_id or "rozet-session",
            "agent": "build",
            "extra": {
                "providerID": self._provider,
                "modelID": self._model,
            },
        }

        try:
            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and data.get("success"):
                result_payload = data.get("result")
                if isinstance(result_payload, dict):
                    return result_payload
        except Exception as exc:  # pragma: no cover - network failure fallback
            LOGGER.debug("Falling back to local tool executor: %s", exc)
        return None

