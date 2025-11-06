"""Tool executor for workers - executes bash commands and file operations."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class ToolExecutor:
    """Executes tools (bash, file operations) for workers."""
    
    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize tool executor.
        
        Args:
            working_dir: Working directory for tool execution
        """
        self.working_dir = working_dir or Path.cwd()
        self.working_dir.mkdir(parents=True, exist_ok=True)
    
    def execute_bash(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """Execute a bash command.
        
        Args:
            command: Bash command to execute
            timeout: Timeout in seconds
            
        Returns:
            Dict with stdout, stderr, returncode, success
        """
        LOGGER.info("Executing bash: %s", command)
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(self.working_dir),
                timeout=timeout,
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            LOGGER.error("Bash command timed out: %s", command)
            return {
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "returncode": -1,
                "success": False,
            }
        except Exception as exc:
            LOGGER.error("Bash command failed: %s", exc)
            return {
                "stdout": "",
                "stderr": str(exc),
                "returncode": -1,
                "success": False,
            }
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """Read a file.
        
        Args:
            file_path: Path to file (relative to working_dir)
            
        Returns:
            Dict with content, exists, success
        """
        full_path = self.working_dir / file_path
        
        try:
            if not full_path.exists():
                return {
                    "content": "",
                    "exists": False,
                    "success": False,
                    "error": f"File does not exist: {file_path}",
                }
            
            content = full_path.read_text(encoding="utf-8")
            
            return {
                "content": content,
                "exists": True,
                "success": True,
                "size": len(content),
            }
        except Exception as exc:
            LOGGER.error("Failed to read file %s: %s", file_path, exc)
            return {
                "content": "",
                "exists": False,
                "success": False,
                "error": str(exc),
            }
    
    def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Write content to a file.
        
        Args:
            file_path: Path to file (relative to working_dir)
            content: Content to write
            
        Returns:
            Dict with success, file_path, size
        """
        full_path = self.working_dir / file_path
        
        try:
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            full_path.write_text(content, encoding="utf-8")
            
            # Verify write by reading back
            verify_content = full_path.read_text(encoding="utf-8")
            verified = verify_content == content
            
            return {
                "success": True,
                "file_path": file_path,
                "size": len(content),
                "verified": verified,
            }
        except Exception as exc:
            LOGGER.error("Failed to write file %s: %s", file_path, exc)
            return {
                "success": False,
                "file_path": file_path,
                "error": str(exc),
            }
    
    def list_files(self, directory: str = ".", pattern: str = "*") -> Dict[str, Any]:
        """List files in a directory.
        
        Args:
            directory: Directory to list (relative to working_dir)
            pattern: Glob pattern to match
            
        Returns:
            Dict with files list and success
        """
        dir_path = self.working_dir / directory
        
        try:
            if not dir_path.exists():
                return {
                    "files": [],
                    "success": False,
                    "error": f"Directory does not exist: {directory}",
                }
            
            files = [str(f.relative_to(self.working_dir)) for f in dir_path.glob(pattern)]
            
            return {
                "files": sorted(files),
                "success": True,
                "count": len(files),
            }
        except Exception as exc:
            LOGGER.error("Failed to list files in %s: %s", directory, exc)
            return {
                "files": [],
                "success": False,
                "error": str(exc),
            }


