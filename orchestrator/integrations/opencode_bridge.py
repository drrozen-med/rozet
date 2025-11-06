"""OpenCode session bridge for Rozet orchestrator.

This module bridges OpenCode's session system with our orchestrator,
allowing Rozet to use OpenCode's tools (read, write, bash) while
maintaining our REPL interface and task planning.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

# Try to import OpenCode SDK (optional - bridge works without it)
try:
    import sys
    # Add OpenCode SDK to path if available
    opencode_sdk_path = Path(__file__).parent.parent.parent / "opencode" / "packages" / "sdk" / "python" / "src"
    if opencode_sdk_path.exists():
        sys.path.insert(0, str(opencode_sdk_path))
    from opencode_ai import OpenCodeClient
    OPencode_AVAILABLE = True
except ImportError:
    OPencode_AVAILABLE = False
    OpenCodeClient = None  # type: ignore

from orchestrator.config_loader import load_provider_config
from orchestrator.core.context_manager import ConversationContextManager
from orchestrator.core.coordinator import Coordinator
from orchestrator.core.task_planner import TaskPlanner
from orchestrator.providers.factory import create_chat_model

LOGGER = logging.getLogger(__name__)


class OpenCodeSessionBridge:
    """Bridge between OpenCode sessions and Rozet orchestrator.
    
    This class:
    - Creates/manages OpenCode sessions
    - Routes messages through our orchestrator
    - Executes tasks using OpenCode tools
    - Maintains REPL interface
    """
    
    def __init__(
        self,
        working_dir: Optional[Path] = None,
        config_path: Optional[Path] = None,
    ):
        """Initialize the bridge.
        
        Args:
            working_dir: Working directory for the session
            config_path: Path to provider config YAML
        """
        self.working_dir = working_dir or Path.cwd()
        self.config_path = config_path
        
        # Load orchestrator configuration
        self.config = load_provider_config(config_path)
        
        # Initialize orchestrator components
        orchestrator_llm, system_prompt = create_chat_model(self.config.orchestrator)
        
        self.context_manager = ConversationContextManager(
            llm=orchestrator_llm,
            storage_path=self.working_dir / ".opencode" / "orchestrator_context.jsonl",
        )
        
        self.task_planner = TaskPlanner(
            llm=orchestrator_llm,
            system_prompt=system_prompt,
        )
        
        # Initialize OpenCode client if available
        if OPencode_AVAILABLE and OpenCodeClient:
            try:
                self.opencode_client = OpenCodeClient(base_url="http://localhost:4096")
                LOGGER.info("OpenCode client initialized")
            except Exception as e:
                LOGGER.warning("Failed to initialize OpenCode client: %s", e)
                self.opencode_client = None
        else:
            self.opencode_client = None
            LOGGER.info("OpenCode SDK not available - bridge will work in standalone mode")
        
        self.session = None
    
    def create_session(self, project_id: Optional[str] = None) -> str:
        """Create a new OpenCode session.
        
        Args:
            project_id: Optional project ID (defaults to current project)
            
        Returns:
            Session ID
        """
        if not self.opencode_client:
            LOGGER.warning("OpenCode client not available - using mock session")
            return "mock-session-id"
        
        try:
            # Get current project if not provided
            if not project_id:
                project = self.opencode_client.current_project(directory=str(self.working_dir))
                if project and hasattr(project, 'id'):
                    project_id = project.id
            
            # Create session via OpenCode API
            # Note: This requires the full OpenCode API - for now we'll use a placeholder
            # TODO: Implement actual session creation when OpenCode API is fully integrated
            LOGGER.info("Session creation requires full OpenCode API integration")
            return "mock-session-id"
        except Exception as e:
            LOGGER.error("Failed to create OpenCode session: %s", e)
            return "mock-session-id"
    
    def handle_user_request(self, request: str) -> dict:
        """Handle a user request through the orchestrator.
        
        This method:
        1. Plans tasks using the orchestrator
        2. Routes tasks to workers
        3. Executes tasks using OpenCode tools
        4. Returns results
        
        Args:
            request: User's request/description
            
        Returns:
            Dictionary with tasks, results, and status
        """
        # Plan tasks
        LOGGER.info("Planning tasks for request: %s", request[:100])
        tasks = self.task_planner.plan(request)
        
        # Save to context
        self.context_manager.add_message(
            request,
            f"Planned {len(tasks)} tasks: {', '.join([t.task_id for t in tasks])}"
        )
        
        # TODO: Execute tasks using OpenCode tools
        # For now, just return planned tasks
        return {
            "tasks": [
                {
                    "task_id": task.task_id,
                    "description": task.description,
                    "files": task.files,
                    "success_criteria": task.success_criteria,
                }
                for task in tasks
            ],
            "status": "planned",
            "message": f"Planned {len(tasks)} tasks",
        }
    
    def execute_task(self, task_id: str) -> dict:
        """Execute a specific task using OpenCode tools.
        
        Args:
            task_id: ID of the task to execute
            
        Returns:
            Execution results
        """
        # TODO: Implement task execution with OpenCode tools
        LOGGER.warning("Task execution not yet implemented | task_id=%s", task_id)
        return {
            "task_id": task_id,
            "status": "not_implemented",
            "message": "Task execution coming soon",
        }

