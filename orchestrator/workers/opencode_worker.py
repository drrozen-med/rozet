"""Worker that executes tool calls through the OpenCode tool client."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from orchestrator.integrations.opencode_tool_client import OpenCodeToolClient
from orchestrator.workers.local_worker import LocalWorker

LOGGER = logging.getLogger(__name__)


class OpenCodeToolWorker(LocalWorker):
    """Worker implementation that routes tool usage via OpenCode.

    The current implementation still relies on the local :class:`ToolExecutor`
    but centralises the logic in :class:`OpenCodeToolClient` so that future work
    can replace the fallback with real OpenCode API calls without touching the
    orchestrator or bridge logic.
    """

    def __init__(
        self,
        *,
        working_dir: Optional[Path] = None,
        model: str = "gpt-oss:20b",
        verify_outputs: bool = True,
        session_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            model=model,
            working_dir=working_dir,
            verify_outputs=verify_outputs,
        )
        self._tool_client = OpenCodeToolClient(
            working_dir=self._working_dir,
            session_id=session_id,
            executor=self._tool_executor,
        )

    def _process_tool_usage(  # type: ignore[override]
        self,
        tools_used: List[Dict[str, str]],
        working_dir: Path,
        result_data: Dict,
    ) -> List[str]:
        """Execute tool usage entries via the OpenCode tool client."""
        logs: List[str] = []
        errors: List[str] = []
        created_files: set[str] = set(result_data.get("files_created", []))
        modified_files: set[str] = set(result_data.get("files_modified", []))

        for tool_info in tools_used:
            tool_name = (tool_info.get("tool") or "").lower()
            if not tool_name:
                continue

            if tool_name == "write_file":
                path = tool_info.get("file") or tool_info.get("path")
                content = tool_info.get("content", "")
                if not path:
                    errors.append("write_file missing path")
                    continue
                op_result = self._tool_client.write_file(path, content)
                if op_result.get("success"):
                    logs.append(f"✓ write_file -> {path}")
                    created_files.add(path)
                else:
                    errors.append(op_result.get("error") or f"write_file failed for {path}")
            elif tool_name == "read_file":
                path = tool_info.get("file") or tool_info.get("path")
                if not path:
                    errors.append("read_file missing path")
                    continue
                op_result = self._tool_client.read_file(path)
                if op_result.get("success"):
                    preview = (op_result.get("content") or "")[:120]
                    logs.append(f"✓ read_file -> {path} ({len(preview)} preview characters)")
                else:
                    errors.append(op_result.get("error") or f"read_file failed for {path}")
            elif tool_name == "list_files":
                directory = tool_info.get("directory") or tool_info.get("path") or "."
                pattern = tool_info.get("pattern") or "*"
                op_result = self._tool_client.list_files(directory, pattern)
                if op_result.get("success"):
                    logs.append(
                        f"✓ list_files -> {directory} ({op_result.get('count', 0)} items matching '{pattern}')"
                    )
                else:
                    errors.append(op_result.get("error") or f"list_files failed for {directory}")
            elif tool_name == "execute_bash":
                command = tool_info.get("command") or ""
                if not command:
                    errors.append("execute_bash missing command")
                    continue
                op_result = self._tool_client.execute_bash(command)
                if op_result.success:
                    logs.append(f"✓ execute_bash -> {command[:60]}...")
                    if op_result.stdout:
                        logs.append(op_result.stdout.strip())
                else:
                    errors.append(op_result.error or f"execute_bash failed for {command}")
                    if op_result.stderr:
                        logs.append(op_result.stderr.strip())
            else:
                logs.append(f"ℹ︎ Unsupported tool '{tool_name}', skipping execution")

        if errors:
            LOGGER.warning("Tool execution encountered errors: %s", errors)
            result_data.setdefault("errors", []).extend(errors)
            result_data["success"] = False

        result_data["files_created"] = sorted(created_files)
        result_data["files_modified"] = sorted(modified_files)
        return logs

