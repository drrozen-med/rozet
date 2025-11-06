"""Proof-of-concept orchestration context manager using LangChain summary buffer.

This module wires LangChain's ``ConversationSummaryBufferMemory`` into a tiny
driver that simulates an orchestrator exchanging messages with multiple agents.
The intent is to validate token-aware context compaction before we invest in a
full architecture. The script can be executed standalone and prints snapshots of
the raw message buffer alongside the running summary after each turn.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

try:  # Prefer the modern provider-specific package when available.
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover - fall back for older installations
    from langchain.chat_models import ChatOpenAI  # type: ignore[no-redef]

try:
    from langchain.memory import ConversationSummaryBufferMemory
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
except ImportError:
    # Fallback for older versions
    from langchain.memory import ConversationSummaryBufferMemory
    from langchain.schema import BaseMessage, HumanMessage, AIMessage  # type: ignore[assignment]


LOGGER = logging.getLogger(__name__)


def _require_api_key(env_name: str) -> str:
    """Return an API key or raise a friendly error.

    Parameters
    ----------
    env_name:
        Name of the environment variable that should hold the API key.
    """

    try:
        value = os.environ[env_name].strip()
    except KeyError as exc:  # pragma: no cover - defensive check
        message = (
            f"Environment variable '{env_name}' is required for the POC. "
            "Please export the key before running the script."
        )
        raise RuntimeError(message) from exc
    if not value:
        raise RuntimeError(
            f"Environment variable '{env_name}' is defined but empty. "
            "Please provide a valid key."
        )
    return value


@dataclass
class OrchestratorContextPOC:
    """Lightweight wrapper around LangChain's summary buffer memory."""

    query_model: str = "gpt-5-nano"
    summary_model: str = "gpt-5-nano"
    max_token_limit: int = 512
    log_dir: Path = field(default_factory=lambda: Path("experiments/logs"))

    def __post_init__(self) -> None:
        _require_api_key("OPENAI_API_KEY")

        self.log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.log_path = self.log_dir / f"context_snapshot_{timestamp}.jsonl"

        summary_llm = ChatOpenAI(model=self.summary_model, temperature=0.0)
        self.query_llm = ChatOpenAI(model=self.query_model, temperature=0.0)

        self.memory = ConversationSummaryBufferMemory(
            llm=summary_llm,
            max_token_limit=self.max_token_limit,
            return_messages=True,
        )

        LOGGER.info(
            "Initialized orchestrator POC | query_model=%s summary_model=%s",  # noqa: G004
            self.query_model,
            self.summary_model,
        )

    def step(self, user_input: str) -> str:
        """Send a message through the LLM with memory context and record the outcome."""

        LOGGER.debug("User input: %s", user_input)
        
        # Load memory context
        memory_vars = self.memory.load_memory_variables({})
        messages = memory_vars.get("history", [])
        
        # Build message list for LLM
        llm_messages = list(messages) + [HumanMessage(content=user_input)]
        
        # Get response from LLM
        response_obj = self.query_llm.invoke(llm_messages)
        ai_response = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)
        
        # Save to memory
        self.memory.save_context({"input": user_input}, {"output": ai_response})
        
        self._log_snapshot(user_input, ai_response)
        return ai_response

    def _log_snapshot(self, user_input: str, response: str) -> None:
        snapshot = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "user_input": user_input,
            "response": response,
            "recent_buffer": self._serialize_messages(self._recent_messages),
            "moving_summary": getattr(self.memory, "moving_summary_buffer", ""),
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(snapshot))
            handle.write("\n")

    @property
    def _recent_messages(self) -> List[BaseMessage]:
        return self.memory.load_memory_variables({}).get("history", [])

    @staticmethod
    def _serialize_messages(messages: Iterable[BaseMessage]) -> List[dict]:
        serialized = []
        for message in messages:
            serialized.append(
                {
                    "type": type(message).__name__,
                    "content": message.content,
                }
            )
        return serialized


def run_demo() -> None:
    """Execute a simple multi-turn scenario to exercise the summary buffer."""

    logging.basicConfig(level=logging.INFO)
    orchestrator = OrchestratorContextPOC(max_token_limit=400)

    scripted_dialogue = [
        "Agent A proposes building an auth API with POST /login and POST /logout.",
        (
            "Agent B suggests storing sessions in Redis and asks whether we "
            "should rotate refresh tokens."
        ),
        (
            "Agent C recommends adding a /refresh endpoint and specifies that "
            "access tokens should expire after 15 minutes."
        ),
        (
            "Agent D notes that CSR clients need CORS headers and raises a "
            "concern about documenting failure codes."
        ),
        (
            "Please summarise the agreed plan and highlight open questions so "
            "the human lead can review them."
        ),
    ]

    for turn, message in enumerate(scripted_dialogue, start=1):
        ai_response = orchestrator.step(message)
        LOGGER.info("Turn %s | AI responded: %s", turn, ai_response)
        LOGGER.info("Current summary: %s", orchestrator.memory.moving_summary_buffer)

    LOGGER.info("Detailed log written to %s", orchestrator.log_path)


if __name__ == "__main__":  # pragma: no cover - manual execution entry point
    run_demo()

