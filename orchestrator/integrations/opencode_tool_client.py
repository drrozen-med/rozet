"""Client for executing OpenCode tools from the Python orchestrator.

This module currently falls back to the local ToolExecutor while providing a thin
abstraction layer that can later be extended to call the OpenCode HTTP API once
the server exposes execution endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from orchestrator.workers.tool_executor import ToolExecutor


@dataclass
class ToolExecutionResult:
    """Standardised result for tool executions."""

    success: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    error: Optional[str] = None


class OpenCodeToolClient:
    """Executes tools on behalf of the orchestrator.

    For now this simply proxies to :class:`ToolExecutor`. The class surface mirrors
    the methods we expect the eventual OpenCode HTTP API to expose, so future work
    can replace the fallback calls with real network requests without having to
    adjust worker logic.
    """

    def __init__(
        self,
        *,
        working_dir: Path,
        base_url: Optional[str] = None,
        session_id: Optional[str] = None,
        executor: Optional[ToolExecutor] = None,
    ) -> None:
        self._working_dir = working_dir
        self._base_url = base_url
        self._session_id = session_id
        self._executor = executor or ToolExecutor(working_dir=working_dir)
        # Note: We intentionally do not import the SDK yet. Executor is a thin shim.

    # ------------------------------------------------------------------ #
    # File helpers
    # ------------------------------------------------------------------ #
    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write a file on disk (currently via fallback executor)."""
        return self._executor.write_file(path, content)

    def read_file(self, path: str) -> Dict[str, Any]:
        """Read a file from disk."""
        return self._executor.read_file(path)

    def list_files(self, directory: str = ".", pattern: str = "*") -> Dict[str, Any]:
        """List files relative to the working directory."""
        return self._executor.list_files(directory, pattern)

    # ------------------------------------------------------------------ #
    # Shell helpers
    # ------------------------------------------------------------------ #
    def execute_bash(self, command: str, timeout: int = 60) -> ToolExecutionResult:
        """Execute a bash command."""
        result = self._executor.execute_bash(command, timeout=timeout)
        return ToolExecutionResult(
            success=result.get("success", False),
            stdout=result.get("stdout", ""),
            stderr=result.get("stderr", ""),
            returncode=result.get("returncode", 0),
            error=result.get("error"),
        )

