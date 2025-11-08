#!/usr/bin/env python3
"""Bridge for OpenCode plugin to call Rozet orchestrator.

This module provides a CLI interface that the OpenCode TypeScript plugin
can call to interact with the Rozet orchestrator.
"""

import argparse
import json
import logging
import os
import sys
import warnings
from datetime import datetime
from io import StringIO
from pathlib import Path

# Suppress LangChain deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*LangChainDeprecationWarning.*")
warnings.filterwarnings("ignore", message=".*migration guide.*")


class BridgeLogHandler(logging.Handler):
    """Custom handler that writes to bridge log file."""
    def __init__(self, bridge_logger):
        super().__init__()
        self.bridge_logger = bridge_logger
    
    def emit(self, record):
        try:
            msg = self.format(record)
            if record.levelno >= logging.ERROR:
                self.bridge_logger.error(msg)
            elif record.levelno >= logging.WARNING:
                self.bridge_logger.warn(msg)
            elif record.levelno >= logging.INFO:
                self.bridge_logger.info(msg)
            else:
                self.bridge_logger.debug(msg)
        except Exception:
            pass  # Don't break if logging fails

def setup_logger(working_dir: Path) -> logging.Logger:
    """Set up logger that writes to file."""
    log_dir = working_dir / ".opencode" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "rozet-bridge.log"
    
    logger = logging.getLogger("rozet_bridge")
    logger.setLevel(logging.DEBUG)
    
    # File handler
    file_handler = logging.FileHandler(log_file, mode="a")
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    # Try loading from project root
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    # Also try loading from current directory
    load_dotenv()
except ImportError:
    # dotenv not installed, skip
    pass

from orchestrator.config_loader import load_provider_config
from orchestrator.core.context_manager import ConversationContextManager
from orchestrator.core.coordinator import Coordinator, WorkerResult
from orchestrator.core.task_planner import TaskPlanner
from orchestrator.core.observability import ObservabilityClient
from orchestrator.providers.factory import create_chat_model
from orchestrator.workers.local_worker import LocalWorker
from orchestrator.workers.opencode_worker import OpenCodeToolWorker

def _is_truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"", "0", "false", "no", "off"}:
        return False
    if normalized in {"1", "true", "yes", "on"}:
        return True
    return default


def _worker_result_to_dict(result: WorkerResult) -> dict:
    return {
        "task_id": result.task_id,
        "success": result.success,
        "files_modified": result.files_modified,
        "files_created": result.files_created,
        "tests_run": result.tests_run,
        "verification_passed": result.verification_passed,
        "errors": result.errors,
        "logs": result.logs,
    }


def main():
    """Main entry point for OpenCode plugin bridge."""
    parser = argparse.ArgumentParser(description="Rozet orchestrator bridge for OpenCode")
    parser.add_argument("--message", required=True, help="User message text")
    parser.add_argument("--directory", required=True, help="Working directory")
    parser.add_argument("--config", help="Path to provider config YAML")
    parser.add_argument("--context-summary", help="Conversation context summary (JSON)")
    parser.add_argument("--session-id", help="Explicit session identifier")
    parser.add_argument(
        "--auto-execute",
        action="store_true",
        help="Automatically execute planned tasks with the default worker",
    )
    args = parser.parse_args()
    
    working_dir = Path(args.directory)
    config_path = Path(args.config) if args.config else None
    session_id = args.session_id or os.getenv("ROZET_SESSION_ID")
    auto_execute = args.auto_execute or _is_truthy(os.getenv("ROZET_AUTO_EXECUTE"))
    use_opencode_tools = _is_truthy(os.getenv("ROZET_USE_OPEN_CODE_TOOLS"), default=True)
    
    logger = setup_logger(working_dir)
    observability = ObservabilityClient(default_session_id=session_id)
    
    # Redirect all Python logging to our bridge logger (suppress stdout)
    root_logger = logging.getLogger()
    root_logger.handlers = []  # Remove default handlers
    root_logger.addHandler(BridgeLogHandler(logger))
    root_logger.setLevel(logging.DEBUG)
    
    # Capture stdout to prevent TaskPlanner errors from appearing
    stdout_capture = StringIO()
    original_stdout = sys.stdout
    
    logger.info("Bridge script started", extra={
        "message_length": len(args.message),
        "directory": str(working_dir),
        "has_context": bool(args.context_summary)
    })
    
    try:
        # Redirect stdout temporarily
        sys.stdout = stdout_capture
        
        # Load configuration
        logger.debug(
            "Loading provider config",
            extra={"config_path": str(config_path), "auto_execute": auto_execute},
        )
        config = load_provider_config(config_path)
        logger.debug("Config loaded successfully")
        
        # Initialize orchestrator components
        orchestrator_llm, system_prompt = create_chat_model(config.orchestrator)
        
        context_manager = ConversationContextManager(
            llm=orchestrator_llm,
            storage_path=working_dir / ".opencode" / "orchestrator_context.jsonl",
        )
        context_manager.record_user(args.message)
        
        # Load context summary if provided
        context_summary = ""
        if args.context_summary:
            try:
                context_data = json.loads(args.context_summary)
                context_summary = context_data.get("summary", "")
            except json.JSONDecodeError:
                pass
        
        task_planner = TaskPlanner(
            llm=orchestrator_llm,
            system_prompt=system_prompt,
        )
        
        # Check if message needs task planning
        # Simple heuristic: if it contains action words, plan tasks
        action_words = ["create", "build", "make", "write", "implement", "add", "fix", "refactor"]
        needs_planning = any(word in args.message.lower() for word in action_words)
        
        logger.info("Planning decision", extra={
            "needs_planning": needs_planning,
            "message_preview": args.message[:50]
        })
        
        execution_results: list[dict] = []
        execution_error: str | None = None

        if needs_planning:
            # Plan tasks with context
            logger.debug("Calling task planner", extra={"context_length": len(context_summary)})
            try:
                tasks = task_planner.plan(args.message, context_summary=context_summary)
                logger.info("Task planning completed", extra={"task_count": len(tasks)})
            except Exception as plan_error:
                error_msg = str(plan_error)
                logger.error("Task planning failed", exc_info=True, extra={
                    "error": error_msg,
                    "error_type": type(plan_error).__name__
                })
                # Check if it's an auth error
                if "User not found" in error_msg or "401" in error_msg:
                    logger.error("Authentication error - API key may be invalid or expired")
                if session_id:
                    observability.task_completed(
                        session_id,
                        task_id="planner",
                        success=False,
                        error=error_msg,
                    )
                tasks = []
            
            # Return task plan
            result = {
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "description": task.description,
                        "files": task.files,
                        "success_criteria": task.success_criteria,
                    }
                    for task in tasks
                ],
                "systemPrompt": system_prompt if system_prompt else None,
                "needsExecution": True,
            }
            if session_id:
                for planned_task in result["tasks"]:
                    observability.task_planned(
                        session_id,
                        planned_task["task_id"],
                        planned_task["description"],
                        files=planned_task.get("files") or [],
                        success_criteria=planned_task.get("success_criteria") or [],
                    )
            
            # Optionally execute tasks automatically
            if tasks and auto_execute:
                try:
                    logger.info(
                        "Auto execution enabled, running %s tasks",
                        len(tasks),
                    )
                    if use_opencode_tools:
                        logger.debug("Using OpenCodeToolWorker for auto execution")
                        worker = OpenCodeToolWorker(working_dir=working_dir, session_id=session_id)
                    else:
                        logger.debug("Using LocalWorker for auto execution (ROZET_USE_OPEN_CODE_TOOLS disabled)")
                        worker = LocalWorker(working_dir=working_dir)
                    coordinator = Coordinator(
                        worker=worker,
                        context_manager=context_manager,
                        observability=observability,
                    )
                    worker_results = coordinator.execute_tasks(
                        tasks,
                        working_dir=working_dir,
                    )
                    execution_results = [_worker_result_to_dict(res) for res in worker_results]
                    for res in worker_results:
                        if session_id:
                            observability.task_completed(
                                session_id,
                                task_id=res.task_id,
                                success=res.success,
                                files_modified=res.files_modified,
                                files_created=res.files_created,
                                errors=res.errors,
                            )
                    if execution_results:
                        summary_lines = []
                        for res in execution_results:
                            status = "SUCCESS" if res["success"] else "FAILED"
                            line = f"{res['task_id']}: {status}"
                            if res["files_modified"] or res["files_created"]:
                                line += f" (modified: {', '.join(res['files_modified']) or 'none'}, created: {', '.join(res['files_created']) or 'none'})"
                            if res["errors"]:
                                line += f" | errors: {', '.join(res['errors'])}"
                            summary_lines.append(line)
                        context_manager.record_assistant("\n".join(summary_lines))
                        logger.info(
                            "Auto execution completed",
                            extra={"results": execution_results},
                        )
                    result["executionResults"] = execution_results
                    result["needsExecution"] = False
                except Exception as exec_error:  # pragma: no cover - defensive
                    execution_error = str(exec_error)
                    logger.error(
                        "Auto execution failed",
                        exc_info=True,
                        extra={"error": execution_error},
                    )
                    if session_id:
                        observability.task_completed(
                            session_id,
                            task_id="AUTO_EXECUTION",
                            success=False,
                            error=execution_error,
                        )
                    result["executionError"] = execution_error
            else:
                result["needsExecution"] = True
        else:
            # Just return system prompt for conversational responses
            result = {
                "tasks": [],
                "systemPrompt": system_prompt if system_prompt else None,
                "needsExecution": False,
            }
        
        context_manager.persist()
        
        # Restore stdout before printing JSON
        sys.stdout = original_stdout
        
        # Log any captured stdout (errors from TaskPlanner, etc.)
        captured_output = stdout_capture.getvalue()
        if captured_output:
            # Check for authentication errors
            if "User not found" in captured_output or "401" in captured_output:
                logger.error("Authentication error detected in stdout", extra={"output": captured_output})
            else:
                logger.debug("Captured stdout output", extra={"output": captured_output})
        
        # Output JSON for TypeScript plugin
        logger.debug("Returning result", extra={
            "has_tasks": bool(result.get("tasks")),
            "task_count": len(result.get("tasks", [])),
            "has_system_prompt": bool(result.get("systemPrompt"))
        })
        print(json.dumps(result))
        logger.info("Bridge script completed successfully")
        return 0
        
    except Exception as e:
        # Restore stdout before printing error JSON
        sys.stdout = original_stdout
        
        # Log any captured stdout
        captured_output = stdout_capture.getvalue()
        if captured_output:
            logger.debug("Captured stdout output (error case)", extra={"output": captured_output})
        
        # Return error in JSON format
        logger.error("Bridge script failed", exc_info=True, extra={"error": str(e)})
        error_result = {
            "error": str(e),
            "tasks": [],
            "systemPrompt": None,
            "needsExecution": False,
        }
        print(json.dumps(error_result))
        return 1


if __name__ == "__main__":
    sys.exit(main())

