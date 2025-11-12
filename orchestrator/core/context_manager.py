"""Conversation context manager built on LangChain summary memory."""

from __future__ import annotations

import json
import logging
import warnings
from pathlib import Path
from typing import Dict, Iterable, List, Optional

# Suppress LangChain deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*LangChainDeprecationWarning.*")
warnings.filterwarnings("ignore", message=".*migration guide.*")

# Lazy import pattern to handle version compatibility issues
# We'll import ConversationSummaryBufferMemory only when needed
_CONVERSATION_SUMMARY_BUFFER_MEMORY = None

def _get_conversation_summary_buffer_memory():
    """Lazy import of ConversationSummaryBufferMemory with fallbacks."""
    global _CONVERSATION_SUMMARY_BUFFER_MEMORY
    if _CONVERSATION_SUMMARY_BUFFER_MEMORY is not None:
        return _CONVERSATION_SUMMARY_BUFFER_MEMORY
    
    # Try various import paths, catching import errors at module level
    import_paths = [
        ("langchain.memory", "ConversationSummaryBufferMemory"),
        ("langchain.memory.conversation_summary_buffer", "ConversationSummaryBufferMemory"),
    ]
    
    for module_path, class_name in import_paths:
        try:
            # Use importlib to get better error handling
            import importlib
            module = importlib.import_module(module_path)
            _CONVERSATION_SUMMARY_BUFFER_MEMORY = getattr(module, class_name)
            LOGGER.debug("Loaded ConversationSummaryBufferMemory from %s", module_path)
            return _CONVERSATION_SUMMARY_BUFFER_MEMORY
        except (ImportError, AttributeError, ModuleNotFoundError) as exc:
            # Check if it's the specific langchain_core.memory error
            if "langchain_core.memory" in str(exc):
                LOGGER.warning(
                    "LangChain version incompatibility detected. "
                    "langchain.memory requires langchain_core.memory which is missing. "
                    "This is a known issue with mismatched versions."
                )
                continue
            continue
    
    # If all imports fail, provide a helpful error message
    raise ImportError(
        "Could not import ConversationSummaryBufferMemory. "
        "This is likely due to LangChain version incompatibility. "
        "The installed langchain-core (1.0.3) is incompatible with langchain (0.3.26). "
        "To fix: pip install --upgrade langchain-core==0.3.21 langchain==0.3.10"
    )

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

LOGGER = logging.getLogger(__name__)


class ConversationContextManager:
    """Maintains orchestrator context with rolling summaries and persistence."""

    def __init__(
        self,
        llm,
        *,
        max_token_limit: int = 1200,
        storage_path: Optional[Path] = None,
    ) -> None:
        ConversationSummaryBufferMemory = _get_conversation_summary_buffer_memory()
        # Suppress deprecation warning when creating memory object
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            warnings.filterwarnings("ignore")
            self._memory = ConversationSummaryBufferMemory(
                llm=llm,
                max_token_limit=max_token_limit,
                return_messages=True,
            )
        self._storage_path = storage_path or Path("experiments/logs/orchestrator_context.jsonl")
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        LOGGER.debug("ConversationContextManager initialized | storage=%s", self._storage_path)

    # ------------------------------------------------------------------
    # Message ingestion helpers
    # ------------------------------------------------------------------
    def record_user(self, content: str) -> None:
        self._memory.chat_memory.add_user_message(content)
        self._touch()
        LOGGER.debug("Recorded user message (%s chars)", len(content))

    def record_assistant(self, content: str) -> None:
        self._memory.chat_memory.add_ai_message(content)
        self._touch()
        LOGGER.debug("Recorded assistant message (%s chars)", len(content))

    def record_system(self, content: str) -> None:
        self._memory.chat_memory.add_message(SystemMessage(content=content))
        self._touch()
        LOGGER.debug("Recorded system message (%s chars)", len(content))

    def _touch(self) -> None:
        """Trigger internal summarization bookkeeping."""

        # load_memory_variables forces ConversationSummaryBufferMemory to evaluate
        # whether the transcript exceeds the token limit and update the moving
        # summary buffer.
        self._memory.load_memory_variables({})

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------
    @property
    def summary(self) -> str:
        return getattr(self._memory, "moving_summary_buffer", "")

    @property
    def recent_messages(self) -> List[BaseMessage]:
        return self._memory.load_memory_variables({}).get("history", [])

    def snapshot(self) -> Dict[str, object]:
        """Return a serializable snapshot for observability/logging."""

        return {
            "summary": self.summary,
            "recent_messages": [
                {
                    "type": message.type,
                    "content": message.content,
                }
                for message in self.recent_messages
            ],
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def persist(self) -> None:
        record = {
            "summary": self.summary,
            "messages": [
                {
                    "role": message.type,
                    "content": message.content,
                }
                for message in self.recent_messages
            ],
        }
        with self._storage_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record))
            handle.write("\n")
        LOGGER.debug("Persisted context snapshot to %s", self._storage_path)

    def load(self, records: Iterable[dict]) -> None:
        """Restore context from an iterable of serialized records."""

        messages: List[BaseMessage] = []
        for record in records:
            for entry in record.get("messages", []):
                role = entry.get("role")
                content = entry.get("content", "")
                if role == "human":
                    messages.append(HumanMessage(content=content))
                elif role == "ai":
                    messages.append(AIMessage(content=content))
                elif role == "system":
                    messages.append(SystemMessage(content=content))
        if messages:
            self._memory.chat_memory.messages = messages
            self._touch()
            LOGGER.info("Loaded %s messages into context", len(messages))

    # ------------------------------------------------------------------
    # Context Management Methods (Plan requirements)
    # ------------------------------------------------------------------
    def summarize_old_messages(self, max_tokens: Optional[int] = None) -> str:
        """Summarize older messages beyond the recent buffer.
        
        Args:
            max_tokens: Optional token limit for summary (uses default if None)
            
        Returns:
            Summary string of older conversation context
        """
        # The moving summary buffer IS the summary of old messages
        # ConversationSummaryBufferMemory automatically maintains this
        summary = self.summary
        if not summary:
            # If no summary exists yet, we might need to force summarization
            # by loading memory variables which triggers internal summarization
            self._touch()
            summary = self.summary
        return summary

    def load_relevant_files(self, file_paths: List[str]) -> Dict[str, str]:
        """Load file contents for context.
        
        Args:
            file_paths: List of file paths to load
            
        Returns:
            Dictionary mapping file paths to their contents
        """
        contents: Dict[str, str] = {}
        for file_path in file_paths:
            path = Path(file_path)
            if path.exists() and path.is_file():
                try:
                    contents[str(path)] = path.read_text(encoding="utf-8")
                    LOGGER.debug("Loaded file %s (%s chars)", file_path, len(contents[str(path)]))
                except Exception as exc:  # pragma: no cover - defensive
                    LOGGER.warning("Failed to load file %s: %s", file_path, exc)
                    contents[str(path)] = f"[Error loading file: {exc}]"
            else:
                LOGGER.debug("File not found or not a file: %s", file_path)
                contents[str(path)] = "[File not found]"
        return contents

    def prune_context(self, max_tokens: Optional[int] = None) -> None:
        """Prune context to stay within token limits.
        
        Args:
            max_tokens: Optional token limit (uses instance default if None)
        """
        if max_tokens is not None:
            # Update the token limit if provided
            self._memory.max_token_limit = max_tokens
        
        # Force summarization by loading memory variables
        # This will automatically summarize old messages if limit exceeded
        self._touch()
        
        # Persist the pruned state
        self.persist()
        LOGGER.info("Pruned context | summary_length=%s recent_messages=%s", 
                   len(self.summary), len(self.recent_messages))

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def as_prompt_messages(self) -> List[BaseMessage]:
        """Return the messages suitable for passing to an LLM."""

        return list(self.recent_messages)
