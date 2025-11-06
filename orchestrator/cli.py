#!/usr/bin/env python3
"""CLI entry point for the orchestrator."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from orchestrator.config_loader import load_provider_config
from orchestrator.core.context_manager import ConversationContextManager
from orchestrator.core.coordinator import Coordinator
from orchestrator.core.observability import ObservabilityClient
from orchestrator.core.task_planner import TaskPlanner
from orchestrator.providers.factory import create_chat_model
from orchestrator.workers.local_worker import LocalWorker


def setup_logging(level: str = "INFO") -> None:
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Multi-agent orchestrator")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["plan"],
        help="Command to execute",
    )
    parser.add_argument(
        "request",
        nargs="?",
        help="User request/description",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to provider config YAML",
    )
    parser.add_argument(
        "--working-dir",
        type=Path,
        default=Path.cwd(),
        help="Working directory for execution",
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=6,
        help="Maximum number of tasks to generate",
    )
    parser.add_argument(
        "--log-level",
        default="WARN",  # Changed from "INFO" to reduce noise
        choices=["DEBUG", "INFO", "WARN", "ERROR"],
        help="Logging level",
    )
    parser.add_argument(
        "--output-format",
        default="pretty",  # Changed from "json" for better UX
        choices=["json", "pretty"],
        help="Output format",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute tasks after planning (otherwise just plan)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode: validate config and structure without making API calls",
    )
    parser.add_argument(
        "--tui",
        action="store_true",
        help="Start interactive REPL chat interface (conversational, like Claude Code)",
    )
    parser.add_argument(
        "--repl",
        action="store_true",
        dest="tui",  # Alias for --tui
        help="Alias for --tui (REPL mode: conversational interface)",
    )
    
    args = parser.parse_args()
    setup_logging(args.log_level)
    
    # REPL mode takes precedence (also called "TUI" flag for compatibility)
    if args.tui:
        from orchestrator.tui import run_interactive_tui
        return run_interactive_tui(args.config, args.working_dir)
    
    # Require command if not in REPL mode
    if not args.command:
        parser.error("Command required (use 'plan' or '--tui'/'--repl' for interactive REPL mode)")
    
    if args.command == "plan":
        # Interactive mode: prompt for request if not provided
        if not args.request:
            if not sys.stdin.isatty():
                # Not a TTY, can't prompt interactively
                parser.error("'request' argument required for 'plan' command when not in interactive mode")
            # Interactive mode - prompt for request
            print("Enter your request (or press Ctrl+D to cancel):")
            try:
                args.request = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nCancelled.")
                return 1
            if not args.request:
                parser.error("Request cannot be empty")
        return run_plan(args)
    
    return 0


def run_plan(args: argparse.Namespace) -> int:
    """Run the plan command."""
    try:
        # Dry-run mode: disable strict credential validation
        if args.dry_run:
            os.environ["ORCHESTRATOR_STRICT_CREDENTIALS"] = "false"
        
        # Load configuration
        config = load_provider_config(args.config)
        
        # Dry-run mode: just validate structure
        if args.dry_run:
            print("✓ Configuration loaded successfully")
            print(f"  Orchestrator: {config.orchestrator.provider}/{config.orchestrator.model}")
            print(f"  Workers: {len(config.workers)} configured")
            print(f"  Request: {args.request}")
            print("\n✓ CLI structure validated (dry-run mode)")
            print("  Tip: Set API keys to test full functionality")
            return 0
        
        # Create orchestrator LLM
        orchestrator_llm, system_prompt = create_chat_model(config.orchestrator)
        
        # Create context manager
        context_manager = ConversationContextManager(
            llm=orchestrator_llm,
            storage_path=args.working_dir / ".opencode" / "orchestrator_context.jsonl",
        )
        
        # Create task planner
        planner = TaskPlanner(
            llm=orchestrator_llm,
            max_tasks=args.max_tasks,
            system_prompt=system_prompt,
        )
        
        # Load context summary
        context_summary = context_manager.summarize_old_messages()
        
        # Record user request
        context_manager.record_user(args.request)
        
        # Create observability client
        observability = ObservabilityClient()
        
        # Plan tasks
        tasks = planner.plan(args.request, context_summary=context_summary)
        
        # Send observability events for planned tasks
        for task in tasks:
            observability.task_planned(
                task_id=task.task_id,
                description=task.description,
                files=task.files,
            )
        
        # Record planning result
        planning_result = f"Planned {len(tasks)} tasks: {', '.join(t.task_id for t in tasks)}"
        context_manager.record_assistant(planning_result)
        context_manager.persist()
        
        # Output tasks
        if args.output_format == "json":
            output = {
                "tasks": [
                    {
                        "task_id": t.task_id,
                        "description": t.description,
                        "files": t.files,
                        "success_criteria": t.success_criteria,
                        "budget": t.budget,
                        "dependencies": t.dependencies,
                    }
                    for t in tasks
                ]
            }
            print(json.dumps(output, indent=2))
        else:
            print("Planned Tasks:")
            for task in tasks:
                print(f"\n{task.task_id}: {task.description}")
                if task.files:
                    print(f"  Files: {', '.join(task.files)}")
                if task.success_criteria:
                    print("  Success criteria:")
                    for criterion in task.success_criteria:
                        print(f"    - {criterion}")
        
        # Execute if requested
        if args.execute:
            # Create worker
            worker = LocalWorker(working_dir=args.working_dir)
            
            # Create coordinator with observability
            coordinator = Coordinator(
                worker=worker,
                context_manager=context_manager,
                observability=observability,
            )
            
            # Execute tasks
            results = coordinator.execute_tasks(tasks, working_dir=args.working_dir)
            
            # Record results
            for result in results:
                result_summary = (
                    f"Task {result.task_id}: "
                    f"{'SUCCESS' if result.success else 'FAILED'}"
                )
                if result.errors:
                    result_summary += f" Errors: {', '.join(result.errors)}"
                context_manager.record_assistant(result_summary)
            
            context_manager.persist()
            
            # Output results
            if args.output_format == "json":
                output = {
                    "tasks": [
                        {
                            "task_id": r.task_id,
                            "success": r.success,
                            "files_modified": r.files_modified,
                            "files_created": r.files_created,
                            "tests_run": r.tests_run,
                            "verification_passed": r.verification_passed,
                            "errors": r.errors,
                        }
                        for r in results
                    ]
                }
                print("\n" + json.dumps(output, indent=2))
            else:
                print("\nExecution Results:")
                for result in results:
                    status = "✅" if result.success else "❌"
                    print(f"\n{status} {result.task_id}")
                    if result.files_modified:
                        print(f"  Modified: {', '.join(result.files_modified)}")
                    if result.files_created:
                        print(f"  Created: {', '.join(result.files_created)}")
                    if result.errors:
                        print(f"  Errors: {', '.join(result.errors)}")
        
        return 0
        
    except Exception as exc:
        logging.exception("Orchestrator failed")
        if args.output_format == "json":
            error_output = {"error": str(exc), "type": type(exc).__name__}
            print(json.dumps(error_output, indent=2))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

