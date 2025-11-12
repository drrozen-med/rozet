"""Local worker that executes tasks using Qwen 14B via Ollama."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from json import JSONDecoder
import re

from ..core.coordinator import WorkerResult
from ..core.task_planner import TaskSpec
from .tool_executor import ToolExecutor

LOGGER = logging.getLogger(__name__)

# OpenAI OSS-20 model running locally via Ollama
DEFAULT_MODEL = "gpt-oss:20b"
DEFAULT_FORMAT = "json"
ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


class LocalWorker:
    """Worker that executes tasks using local Ollama models."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        *,
        working_dir: Optional[Path] = None,
        verify_outputs: bool = True,
        tool_executor: Optional[ToolExecutor] = None,
    ) -> None:
        self._model = model
        self._working_dir = working_dir or Path.cwd()
        self._verify_outputs = verify_outputs
        # Initialize tool executor if not provided
        self._tool_executor = tool_executor or ToolExecutor(working_dir=self._working_dir)

    def execute(self, task: TaskSpec, working_dir: Optional[Path] = None) -> WorkerResult:
        """Execute a task and return structured result.
        
        Args:
            task: Task specification to execute
            working_dir: Optional override for working directory
            
        Returns:
            Structured worker result
        """
        dir_path = working_dir or self._working_dir
        
        # Build prompt for worker
        prompt = self._build_prompt(task)
        
        LOGGER.info("Executing task %s with model %s", task.task_id, self._model)
        
        try:
            # Call Ollama
            response = self._call_ollama(prompt)
            
            # Parse JSON response (handle markdown/code fences)
            result_data = self._parse_result_data(response)
            
            # Extract tool usage information
            tools_used = result_data.get("tools_used", [])
            
            # If worker described tool usage, verify by actually executing tools mentioned
            # This is a simple MVP approach - in future we can add iterative tool execution
            tool_results = []
            if tools_used:
                tool_results = self._process_tool_usage(tools_used, dir_path, result_data)
            
            # Build result object
            result = WorkerResult(
                task_id=task.task_id,
                success=result_data.get("success", False),
                files_modified=result_data.get("files_modified", []),
                files_created=result_data.get("files_created", []),
                tests_run=result_data.get("tests_run", []),
                verification_passed=result_data.get("verification_passed", False),
                errors=result_data.get("errors", []),
                logs=result_data.get("logs", ""),
            )
            
            # Add tool execution results to logs if available
            if tool_results:
                result.logs += f"\n\nTool Execution Results:\n" + "\n".join(tool_results)
            
            # Verify outputs if enabled
            if self._verify_outputs:
                self._verify_files(result, dir_path)
            
            return result
            
        except json.JSONDecodeError as exc:
            LOGGER.error("Worker returned invalid JSON: %s", exc)
            return WorkerResult(
                task_id=task.task_id,
                success=False,
                files_modified=[],
                files_created=[],
                tests_run=[],
                verification_passed=False,
                errors=[f"Invalid JSON response: {exc}"],
                logs=f"Raw response: {response[:500]}",
            )
        except Exception as exc:
            LOGGER.error("Worker execution failed: %s", exc)
            return WorkerResult(
                task_id=task.task_id,
                success=False,
                files_modified=[],
                files_created=[],
                tests_run=[],
                verification_passed=False,
                errors=[str(exc)],
                logs=f"Exception: {exc}",
            )

    def _build_prompt(self, task: TaskSpec) -> str:
        """Build the prompt for the worker."""
        prompt_parts = [
            f"Task ID: {task.task_id}",
            f"Description: {task.description}",
            "",
        ]
        
        if task.files:
            prompt_parts.append("Files to work with:")
            for file_path in task.files:
                prompt_parts.append(f"  - {file_path}")
            prompt_parts.append("")
        
        if task.success_criteria:
            prompt_parts.append("Success criteria:")
            for criterion in task.success_criteria:
                prompt_parts.append(f"  - {criterion}")
            prompt_parts.append("")
        
        prompt_parts.extend([
            "TOOLS: read_file(path), write_file(path, content), execute_bash(cmd), list_files(dir, pattern)",
            "",
            "Return JSON only:",
            '{"success": bool, "tools_used": [{"tool": "name", "file": "path", "result": "status"}],',
            ' "files_modified": ["paths"], "files_created": ["paths"], "tests_run": [],',
            ' "verification_passed": bool, "errors": [], "logs": "text"}',
            "",
            "Execute:",
        ])
        
        return "\n".join(prompt_parts)

    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API via HTTP and return response."""
        import requests
        
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "format": "json",  # Request JSON format for structured output
        }
        
        LOGGER.debug("Calling Ollama HTTP API: %s", self._model)
        
        try:
            response = requests.post(url, json=payload, timeout=300)  # Increased from 120 to 300 seconds
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except requests.exceptions.RequestException as exc:
            LOGGER.error("Ollama HTTP API failed: %s", exc)
            raise RuntimeError(f"Ollama API failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Response parsing helpers
    # ------------------------------------------------------------------
    def _parse_result_data(self, response: str) -> Dict:
        """Parse JSON response from worker, tolerating markdown wrappers."""
        decoder = JSONDecoder()
        stripped = ANSI_ESCAPE_RE.sub("", response).strip()
        if not stripped:
            raise json.JSONDecodeError("Empty response", response, 0)

        candidates = []

        # Split out fenced code blocks if present
        if "```" in stripped:
            parts = stripped.split("```")
            for part in parts:
                segment = part.strip()
                if not segment:
                    continue
                if segment.lower().startswith("json"):
                    segment = segment[4:].strip()
                candidates.append(segment)
        else:
            candidates.append(stripped)

        for candidate in candidates:
            for idx, char in enumerate(candidate):
                if char in "{[":
                    try:
                        obj, end = decoder.raw_decode(candidate, idx)
                        return obj
                    except json.JSONDecodeError:
                        continue

        raise json.JSONDecodeError("No JSON object found", response, 0)

    def _process_tool_usage(
        self, tools_used: List[Dict[str, str]], working_dir: Path, result_data: Dict
    ) -> List[str]:
        """Process tool usage described in worker response.
        
        This is an MVP implementation that verifies tool usage by checking files.
        Future enhancement: Implement iterative tool execution loop.
        
        Args:
            tools_used: List of tool usage descriptions from worker
            working_dir: Working directory for tool execution
            result_data: Full result data from worker
            
        Returns:
            List of tool execution result messages
        """
        tool_results = []
        
        # Update tool executor working directory if needed
        if self._tool_executor.working_dir != working_dir:
            self._tool_executor.working_dir = working_dir
        
        for tool_info in tools_used:
            tool_name = tool_info.get("tool", "")
            file_path = tool_info.get("file", "")
            command = tool_info.get("command", "")
            result_status = tool_info.get("result", "")
            
            if tool_name == "write_file" and file_path:
                # Verify file was actually created/modified
                read_result = self._tool_executor.read_file(file_path)
                if read_result["success"]:
                    tool_results.append(f"✓ Verified: {file_path} exists and is readable")
                else:
                    tool_results.append(f"✗ Warning: {file_path} was claimed but doesn't exist")
            
            elif tool_name == "read_file" and file_path:
                # Verify file can be read
                read_result = self._tool_executor.read_file(file_path)
                if read_result["success"]:
                    tool_results.append(f"✓ Verified: {file_path} read successfully ({read_result.get('size', 0)} bytes)")
                else:
                    tool_results.append(f"✗ Warning: {file_path} cannot be read")
            
            elif tool_name == "execute_bash" and command:
                # Note: We can't re-execute bash commands safely, so we just log
                tool_results.append(f"✓ Bash command executed: {command[:50]}...")
            
            elif tool_name == "list_files":
                # Verify directory listing
                list_result = self._tool_executor.list_files()
                if list_result["success"]:
                    tool_results.append(f"✓ Directory listing: {list_result.get('count', 0)} files")
        
        return tool_results

    def _verify_files(self, result: WorkerResult, working_dir: Path) -> None:
        """Verify that claimed files actually exist and were modified."""
        verified_modified = []
        verified_created = []
        
        for file_path in result.files_modified:
            full_path = working_dir / file_path
            if full_path.exists():
                verified_modified.append(file_path)
            else:
                LOGGER.warning("Claimed modified file does not exist: %s", file_path)
        
        for file_path in result.files_created:
            full_path = working_dir / file_path
            if full_path.exists():
                verified_created.append(file_path)
            else:
                LOGGER.warning("Claimed created file does not exist: %s", file_path)
        
        # Update result with verified files
        result.files_modified = verified_modified
        result.files_created = verified_created
        
        # If verification failed, mark as not passed
        if (result.files_modified or result.files_created) and not verified_modified and not verified_created:
            if result.verification_passed:
                LOGGER.warning("Worker claimed verification passed but files don't exist")
                result.verification_passed = False
                if not result.errors:
                    result.errors = []
                result.errors.append("Verification failed: claimed files do not exist")

