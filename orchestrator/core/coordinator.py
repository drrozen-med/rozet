"""Simple task coordinator for routing tasks to workers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional

from .context_manager import ConversationContextManager
from .file_locking import FileLockManager, LockTimeoutError
from .observability import ObservabilityClient
from .task_planner import TaskSpec

LOGGER = logging.getLogger(__name__)


@dataclass
class WorkerResult:
    """Result from a worker execution."""

    task_id: str
    success: bool
    files_modified: List[str]
    files_created: List[str]
    tests_run: List[Dict[str, str]]
    verification_passed: bool
    errors: List[str]
    logs: str = ""


class Coordinator:
    """Routes tasks to workers and coordinates execution."""

    def __init__(
        self,
        worker,
        *,
        context_manager: Optional[ConversationContextManager] = None,
        file_lock_manager: Optional[FileLockManager] = None,
        observability: Optional[ObservabilityClient] = None,
    ) -> None:
        self._worker = worker
        self._context_manager = context_manager
        self._file_lock_manager = file_lock_manager or FileLockManager()
        self._observability = observability

    def execute_tasks(
        self, tasks: List[TaskSpec], working_dir: Optional[Path] = None
    ) -> List[WorkerResult]:
        """Execute tasks sequentially and return results.
        
        Args:
            tasks: List of tasks to execute
            working_dir: Optional working directory for execution
            
        Returns:
            List of worker results in task order
        """
        results: List[WorkerResult] = []
        
        for task in tasks:
            LOGGER.info("Executing task %s: %s", task.task_id, task.description)
            
            # Send observability event
            if self._observability:
                self._observability.task_assigned(
                    task_id=task.task_id,
                    worker_id=getattr(self._worker, "_model", "unknown"),
                    description=task.description,
                )
            
            # Acquire file locks for files this task will modify
            locked_files: List[str] = []
            try:
                # Acquire locks with timeout
                for file_path in task.files:
                    try:
                        self._file_lock_manager.acquire_lock(
                            file_path, timeout=5.0
                        )
                        locked_files.append(file_path)
                    except LockTimeoutError as e:
                        error_msg = f"Could not acquire lock for {file_path}: {e}"
                        LOGGER.error(error_msg)
                        results.append(
                            WorkerResult(
                                task_id=task.task_id,
                                success=False,
                                files_modified=[],
                                files_created=[],
                                tests_run=[],
                                verification_passed=False,
                                errors=[error_msg],
                                logs=f"Lock timeout: {e}",
                            )
                        )
                        # Release any locks we did acquire
                        for locked_file in locked_files:
                            self._file_lock_manager.release_lock(locked_file)
                        continue
                
                # Execute task with worker (only if locks acquired)
                if locked_files or not task.files:
                    result = self._worker.execute(task, working_dir=working_dir)
                    
                    # Send completion event
                    if self._observability:
                        self._observability.worker_completed(
                            task_id=task.task_id,
                            success=result.success,
                            files_modified=result.files_modified,
                            errors=result.errors,
                        )
                    
                    results.append(result)
                
            except Exception as exc:  # pragma: no cover - defensive
                LOGGER.error("Task %s failed with exception: %s", task.task_id, exc)
                results.append(
                    WorkerResult(
                        task_id=task.task_id,
                        success=False,
                        files_modified=[],
                        files_created=[],
                        verification_passed=False,
                        errors=[str(exc)],
                        logs=f"Exception: {exc}",
                    )
                )
            finally:
                # Release all locks
                for file_path in locked_files:
                    self._file_lock_manager.release_lock(file_path)
        
        return results

