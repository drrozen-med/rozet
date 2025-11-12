"""Interactive REPL (Read-Eval-Print Loop) for orchestrator chat experience.

This is a REPL-style interface (like Claude Code, Gemini CLI) - conversational,
with natural scrolling. Not a fixed TUI (like OpenCode's new interface).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

# Try to import rich for better TUI, fallback to simple if not available
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.markdown import Markdown
    from rich.live import Live
    from rich.status import Status
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from orchestrator.config_loader import load_provider_config
from orchestrator.core.context_manager import ConversationContextManager
from orchestrator.core.task_planner import TaskPlanner
from orchestrator.core.coordinator import Coordinator
from orchestrator.core.observability import ObservabilityClient
from orchestrator.providers.factory import create_chat_model
from orchestrator.workers.local_worker import LocalWorker
from uuid import uuid4


LOGGER = logging.getLogger(__name__)


def _is_greeting_or_small_talk(text: str) -> bool:
    """Detect if input is a greeting, small talk, or conversational request rather than a coding task."""
    text_lower = text.strip().lower()
    
    # Greeting patterns
    greetings = [
        "hello", "hi", "hey", "greetings", "good morning", "good afternoon",
        "good evening", "good night", "howdy", "what's up", "sup", "yo",
        "nice to meet you", "pleased to meet you"
    ]
    
    # Small talk patterns
    small_talk = [
        "how are you", "how's it going", "how are things", "what's happening",
        "how do you do", "thanks", "thank you", "bye", "see you", "goodbye",
        "have a good", "have a nice", "talk to you later"
    ]
    
    # Conversational request patterns (not coding tasks)
    conversational_patterns = [
        "tell me", "explain", "what is", "what are", "describe", "what can you",
        "help me understand", "can you", "could you", "would you", "share",
        "give me", "show me", "what do you", "how do you", "why", "when",
        "where", "who", "joke", "funny", "humor", "story", "example"
    ]
    
    # Check if it's just a greeting
    if text_lower in greetings:
        return True
    
    # Check if it starts with greeting/small talk
    for pattern in greetings + small_talk:
        if text_lower.startswith(pattern) or pattern in text_lower:
            # But exclude if it contains coding keywords
            coding_keywords = ["create", "build", "make", "write", "implement", "code", "script", "function", "api", "app"]
            if not any(keyword in text_lower for keyword in coding_keywords):
                return True
    
    # Check if it's a conversational request (not a coding task)
    for pattern in conversational_patterns:
        if pattern in text_lower:
            # Check if it's a coding ACTION request (not just explaining concepts)
            coding_action_keywords = ["create", "build", "make", "write code", "implement", "code", "script", "function", "program", "develop", "write a", "build a", "make a"]
            # If it contains conversational pattern AND coding action keywords, it's probably a coding task
            # But if it's just explaining/asking about concepts, it's conversational
            if not any(keyword in text_lower for keyword in coding_action_keywords):
                return True
    
    return False


def _get_conversational_response(llm, user_input: str, context_manager: ConversationContextManager) -> str:
    """Get a conversational response for greetings/small talk."""
    from langchain_core.messages import HumanMessage, SystemMessage
    
    # Build conversational system prompt
    system_prompt = """You are a friendly coding assistant. Respond naturally to greetings and small talk.
Keep responses brief and friendly. If asked what you can do, mention you help with coding tasks and can plan development work.
Be conversational but concise."""
    
    # Get recent conversation context
    recent_messages = context_manager.recent_messages[-4:]  # Last 4 messages
    
    # Build message list
    messages = [SystemMessage(content=system_prompt)]
    messages.extend(recent_messages)
    messages.append(HumanMessage(content=user_input))
    
    # Get response
    response = llm.invoke(messages)
    return response.content if hasattr(response, 'content') else str(response)


def run_interactive_tui(config_path: Optional[Path] = None, working_dir: Optional[Path] = None) -> int:
    """Run interactive TUI chat interface for orchestrator."""
    
    if not RICH_AVAILABLE:
        print("Error: 'rich' package required for REPL mode.")
        print("Install with: uv pip install rich")
        return 1
    
    console = Console()
    
    try:
        # Disable strict credential validation for TUI (user can still set keys)
        import os
        os.environ["ORCHESTRATOR_STRICT_CREDENTIALS"] = "false"
        
        # Load configuration
        with console.status("[bold green]Loading configuration..."):
            config = load_provider_config(config_path)
        
        # Show welcome message with actual provider/model info
        provider_info = f"{config.orchestrator.model}"
        console.print(Panel.fit(
            f"[bold cyan]Rozet Orchestrator[/bold cyan]\n"
            f"[dim]Using:[/dim] [yellow]{provider_info}[/yellow]\n"
            "Chat with your multi-agent orchestrator\n"
            "Type 'exit' or 'quit' to end, 'help' for commands",
            title="Welcome"
        ))
        
        # Create orchestrator LLM
        with console.status("[bold green]Initializing orchestrator..."):
            orchestrator_llm, system_prompt = create_chat_model(config.orchestrator)
            
            # Create context manager
            wd = working_dir or Path.cwd()
            context_manager = ConversationContextManager(
                llm=orchestrator_llm,
                storage_path=wd / ".opencode" / "orchestrator_context.jsonl",
            )
            
            # Create task planner
            # Note: TaskPlanner uses its own JSON-focused prompt, not the orchestrator's conversational prompt
            planner = TaskPlanner(
                llm=orchestrator_llm,
                system_prompt=None,  # Use TaskPlanner's DEFAULT_SYSTEM_PROMPT (JSON-focused)
            )
            
            # Create observability client
            session_id = str(uuid4())
            observability = ObservabilityClient(default_session_id=session_id)
            observability.session_start(session_id, mode="tui")
            session_active = True
            
            # Create worker and coordinator (for execution)
            worker = LocalWorker(working_dir=wd)
            coordinator = Coordinator(
                worker=worker,
                context_manager=context_manager,
                observability=observability,
            )
        
        console.print("[bold green]✓[/bold green] Orchestrator ready!\n")
        console.print("[dim]Tip: Say 'hello' for a greeting, or describe what you'd like to build![/dim]\n")
        
        # Conversation loop
        conversation_history = []
        
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
                
                if not user_input.strip():
                    continue
                
                # Handle special commands
                cmd = user_input.strip().lower()
                if cmd in ("exit", "quit", "q"):
                    console.print("\n[bold yellow]Goodbye![/bold yellow]")
                    observability.session_end(session_id, mode="tui", reason="user_exit")
                    session_active = False
                    break
                elif cmd == "help":
                    console.print("\n[bold]Commands:[/bold]")
                    console.print("  [cyan]help[/cyan]     - Show this help")
                    console.print("  [cyan]plan[/cyan]    - Plan tasks for your request")
                    console.print("  [cyan]execute[/cyan] - Execute planned tasks")
                    console.print("  [cyan]exit[/cyan]    - Exit the TUI")
                    continue
                elif cmd.startswith("plan "):
                    user_input = user_input[5:].strip()
                
                # Check if it's a greeting/small talk
                if _is_greeting_or_small_talk(user_input):
                    # Handle conversationally
                    with console.status("[bold yellow]Thinking..."):
                        response = _get_conversational_response(
                            orchestrator_llm, user_input, context_manager
                        )
                    
                    # Record conversation
                    context_manager.record_user(user_input)
                    context_manager.record_assistant(response)
                    context_manager.persist()
                    observability.user_message(session_id, user_input, mode="tui", conversational=True)
                    
                    # Display response
                    console.print(f"\n[bold magenta]Rozet[/bold magenta]: {response}\n")
                    continue
                
                # Show thinking indicator
                with console.status("[bold yellow]Planning tasks..."):
                    # Load context summary
                    context_summary = context_manager.summarize_old_messages()
                    
                    # Record user request
                    context_manager.record_user(user_input)
                    observability.user_message(session_id, user_input, mode="tui")
                    
                    # Plan tasks
                    tasks = planner.plan(user_input, context_summary=context_summary)
                    
                    # Send observability events
                    for task in tasks:
                        observability.task_planned(
                            session_id,
                            task_id=task.task_id,
                            description=task.description,
                            files=task.files,
                        )
                    
                    # Record planning result
                    planning_result = f"Planned {len(tasks)} tasks"
                    context_manager.record_assistant(planning_result)
                    context_manager.persist()
                
                # Display tasks
                console.print("\n[bold green]✓[/bold green] [bold]Planned Tasks:[/bold]\n")
                
                for i, task in enumerate(tasks, 1):
                    console.print(Panel(
                        f"[bold]Description:[/bold] {task.description}\n"
                        f"[bold]Files:[/bold] {', '.join(task.files) if task.files else 'None'}\n"
                        f"[bold]Success Criteria:[/bold]\n" + "\n".join(f"  • {c}" for c in task.success_criteria),
                        title=f"Task {task.task_id}",
                        border_style="blue"
                    ))
                
                # Ask if user wants to execute
                execute = Prompt.ask(
                    "\n[bold yellow]Execute tasks?[/bold yellow]",
                    choices=["y", "n", "yes", "no"],
                    default="n"
                )
                
                if execute.lower() in ("y", "yes"):
                    with console.status("[bold yellow]Executing tasks..."):
                        results = coordinator.execute_tasks(tasks, working_dir=wd)
                    
                    console.print("\n[bold green]✓[/bold green] [bold]Execution Results:[/bold]\n")
                    
                    for result in results:
                        status = "[bold green]✓[/bold green]" if result.success else "[bold red]✗[/bold red]"
                        console.print(f"{status} [bold]{result.task_id}[/bold]")
                        if result.files_modified:
                            console.print(f"  Modified: {', '.join(result.files_modified)}")
                        if result.files_created:
                            console.print(f"  Created: {', '.join(result.files_created)}")
                        if result.errors:
                            console.print(f"  [red]Errors:[/red] {', '.join(result.errors)}")
                    
                    # Record results
                    for result in results:
                        result_summary = f"Task {result.task_id}: {'SUCCESS' if result.success else 'FAILED'}"
                        if result.errors:
                            result_summary += f" Errors: {', '.join(result.errors)}"
                        context_manager.record_assistant(result_summary)
                    
                    context_manager.persist()
                
                conversation_history.append(("user", user_input))
                conversation_history.append(("assistant", f"Planned {len(tasks)} tasks"))
                
            except KeyboardInterrupt:
                console.print("\n\n[bold yellow]Interrupted. Type 'exit' to quit.[/bold yellow]")
                continue
            except EOFError:
                console.print("\n\n[bold yellow]Goodbye![/bold yellow]")
                break
            except Exception as e:
                console.print(f"\n[bold red]Error:[/bold red] {e}")
                LOGGER.exception("Error in TUI loop")
                continue
        
        if session_active:
            observability.session_end(session_id, mode="tui")
        return 0
        
    except Exception as e:
        console.print(f"[bold red]Failed to start TUI:[/bold red] {e}")
        LOGGER.exception("Failed to start TUI")
        if "observability" in locals() and "session_active" in locals() and session_active:
            observability.session_end(session_id, mode="tui", error=str(e))
        return 1

