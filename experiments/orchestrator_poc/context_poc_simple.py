"""Simplified POC for orchestrator context management.

This version implements a basic conversation summarization pattern without
relying on LangChain's ConversationSummaryBufferMemory, which has version
compatibility issues. We'll test the concept manually, then integrate with
LangChain once we have a working environment.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    from langchain.chat_models import ChatOpenAI  # type: ignore[no-redef]

LOGGER = logging.getLogger(__name__)


def _require_api_key(env_name: str) -> str:
    """Return an API key or raise a friendly error."""
    try:
        value = os.environ[env_name].strip()
    except KeyError:
        raise RuntimeError(
            f"Environment variable '{env_name}' is required. "
            "Please export the key before running."
        )
    if not value:
        raise RuntimeError(f"Environment variable '{env_name}' is defined but empty.")
    return value


@dataclass
class SimpleContextManager:
    """Basic context manager with manual summarization."""
    
    model: str = "gpt-5-nano"
    max_recent_messages: int = 6  # Keep last N messages verbatim
    log_dir: Path = field(default_factory=lambda: Path("experiments/logs"))
    
    def __post_init__(self) -> None:
        _require_api_key("OPENAI_API_KEY")
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.log_path = self.log_dir / f"context_simple_{timestamp}.jsonl"
        
        self.llm = ChatOpenAI(model=self.model, temperature=0.0)
        self.recent_messages: List[dict] = []
        self.summary: str = ""
        
        LOGGER.info("Initialized simple context manager | model=%s", self.model)
    
    def step(self, user_input: str) -> str:
        """Process a user message and get AI response."""
        
        LOGGER.debug("User input: %s", user_input)
        
        # Build context: summary + recent messages
        messages = []
        if self.summary:
            messages.append({
                "role": "system",
                "content": f"Previous conversation summary: {self.summary}"
            })
        
        # Add recent messages
        for msg in self.recent_messages[-self.max_recent_messages:]:
            messages.append(msg)
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        # Get response
        response = self.llm.invoke(messages)
        ai_response = response.content if hasattr(response, 'content') else str(response)
        
        # Store in recent messages
        self.recent_messages.append({"role": "user", "content": user_input})
        self.recent_messages.append({"role": "assistant", "content": ai_response})
        
        # Summarize if we have too many messages
        if len(self.recent_messages) > self.max_recent_messages * 2:
            self._summarize_old_messages()
        
        self._log_snapshot(user_input, ai_response)
        return ai_response
    
    def _summarize_old_messages(self) -> None:
        """Summarize old messages and keep only recent ones."""
        
        old_messages = self.recent_messages[:-self.max_recent_messages]
        recent_kept = self.recent_messages[-self.max_recent_messages:]
        
        summary_prompt = (
            "Summarize the following conversation, preserving key decisions, "
            "agreements, and open questions:\n\n" +
            "\n".join([f"{m['role']}: {m['content']}" for m in old_messages])
        )
        
        summary_response = self.llm.invoke([{"role": "user", "content": summary_prompt}])
        new_summary = summary_response.content if hasattr(summary_response, 'content') else str(summary_response)
        
        # Combine with existing summary
        if self.summary:
            self.summary = f"{self.summary}\n{new_summary}"
        else:
            self.summary = new_summary
        
        # Keep only recent messages
        self.recent_messages = recent_kept
        
        LOGGER.info("Summarized %d old messages, summary length: %d", 
                   len(old_messages), len(self.summary))
    
    def _log_snapshot(self, user_input: str, response: str) -> None:
        """Log current state to JSONL file."""
        snapshot = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "user_input": user_input,
            "response": response,
            "recent_messages_count": len(self.recent_messages),
            "summary": self.summary,
            "recent_messages": self.recent_messages[-4:],  # Last 2 exchanges
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(snapshot))
            handle.write("\n")


def run_demo() -> None:
    """Execute a simple multi-turn scenario."""
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    context_mgr = SimpleContextManager(max_recent_messages=4)
    
    scripted_dialogue = [
        "Agent A proposes building an auth API with POST /login and POST /logout.",
        "Agent B suggests storing sessions in Redis and asks whether we should rotate refresh tokens.",
        "Agent C recommends adding a /refresh endpoint and specifies that access tokens should expire after 15 minutes.",
        "Agent D notes that CSR clients need CORS headers and raises a concern about documenting failure codes.",
        "Please summarize the agreed plan and highlight open questions so the human lead can review them.",
    ]
    
    for turn, message in enumerate(scripted_dialogue, start=1):
        LOGGER.info("=" * 60)
        LOGGER.info("Turn %d: %s", turn, message[:50] + "...")
        ai_response = context_mgr.step(message)
        LOGGER.info("Response: %s", ai_response[:100] + "..." if len(ai_response) > 100 else ai_response)
        LOGGER.info("Summary length: %d chars", len(context_mgr.summary))
    
    LOGGER.info("=" * 60)
    LOGGER.info("Demo complete. Detailed log written to %s", context_mgr.log_path)


if __name__ == "__main__":
    run_demo()
