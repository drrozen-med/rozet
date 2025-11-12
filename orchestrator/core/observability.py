"""Observability client for emitting events to the multi-agent dashboard."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

try:  # pragma: no cover - optional dependency
    import requests
except ImportError:  # pragma: no cover - runtime guard
    requests = None  # type: ignore

LOGGER = logging.getLogger(__name__)

DEFAULT_OBSERVABILITY_URL = "http://localhost:4000/events"
DEFAULT_SOURCE_APP = "rozet-opencode"


def _is_truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() not in {"0", "false", "no", "off", ""}


class ObservabilityClient:
    """Client for sending events to the observability system."""

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        source_app: Optional[str] = None,
        enabled: Optional[bool] = None,
        default_session_id: Optional[str] = None,
    ) -> None:
        env_enabled = os.getenv("ROZET_OBSERVABILITY_ENABLED")
        env_url = os.getenv("ROZET_OBSERVABILITY_URL")
        env_app = os.getenv("ROZET_OBSERVABILITY_APP")

        self._base_url = base_url or env_url or DEFAULT_OBSERVABILITY_URL
        self._source_app = source_app or env_app or DEFAULT_SOURCE_APP
        self._default_session_id = default_session_id

        if enabled is None:
            enabled = _is_truthy(env_enabled) if env_enabled is not None else True

        self._enabled = bool(enabled) and requests is not None
        if not self._enabled and enabled:
            LOGGER.warning(
                "Observability disabled: 'requests' package not installed. "
                "Install with: pip install requests"
            )

    # --------------------------------------------------------------------- #
    # Core emission helper
    # --------------------------------------------------------------------- #
    def send_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        *,
        source_app: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Send an event to the observability server."""

        if not self._enabled:
            LOGGER.debug("Observability disabled, skipping event: %s", event_type)
            return

        resolved_session_id = session_id or self._default_session_id
        if resolved_session_id is None:
            LOGGER.debug("Skipping event %s: missing session_id", event_type)
            return

        event = {
            "source_app": source_app or self._source_app,
            "session_id": resolved_session_id,
            "hook_event_type": event_type,
            "payload": payload,
        }

        try:
            response = requests.post(  # type: ignore
                self._base_url,
                json=event,
                timeout=2.0,
            )
            response.raise_for_status()
            LOGGER.debug("Sent observability event: %s", event_type)
        except Exception as exc:  # pragma: no cover - network failure guard
            LOGGER.warning("Failed to send observability event %s: %s", event_type, exc)

    # --------------------------------------------------------------------- #
    # Event helpers
    # --------------------------------------------------------------------- #
    def session_start(self, session_id: str, **payload: Any) -> None:
        self.send_event("SessionStart", payload, session_id=session_id)

    def session_end(self, session_id: str, **payload: Any) -> None:
        self.send_event("SessionEnd", payload, session_id=session_id)

    def user_message(self, session_id: str, message: str, **payload: Any) -> None:
        data = {"message": message, **payload}
        self.send_event("UserPromptSubmit", data, session_id=session_id)

    def task_planned(
        self,
        session_id: Optional[str] = None,
        task_id: str = "",
        description: str = "",
        **payload: Any,
    ) -> None:
        self.send_event(
            "TaskPlanned",
            {"task_id": task_id, "description": description, **payload},
            session_id=session_id,
        )

    def task_assigned(
        self,
        session_id: Optional[str] = None,
        task_id: str = "",
        worker_id: str = "",
        **payload: Any,
    ) -> None:
        self.send_event(
            "TaskAssigned",
            {"task_id": task_id, "worker_id": worker_id, **payload},
            session_id=session_id,
        )

    def task_completed(
        self,
        session_id: Optional[str] = None,
        task_id: str = "",
        success: bool = False,
        **payload: Any,
    ) -> None:
        event_type = "TaskCompleted" if success else "TaskFailed"
        data = {"task_id": task_id, "success": success, **payload}
        self.send_event(event_type, data, session_id=session_id)

    def tool_requested(
        self,
        session_id: Optional[str] = None,
        call_id: str = "",
        tool: str = "",
        **payload: Any,
    ) -> None:
        self.send_event(
            "ToolRequested",
            {"call_id": call_id, "tool": tool, **payload},
            session_id=session_id,
        )

    def tool_completed(
        self,
        session_id: Optional[str] = None,
        call_id: str = "",
        tool: str = "",
        *,
        success: bool = False,
        **payload: Any,
    ) -> None:
        event_type = "ToolCompleted" if success else "ToolFailed"
        data = {"call_id": call_id, "tool": tool, "success": success, **payload}
        self.send_event(event_type, data, session_id=session_id)

    # --------------------------------------------------------------------- #
    # Configuration helpers
    # --------------------------------------------------------------------- #
    def with_session(self, session_id: str) -> "ObservabilityClient":
        """Return a shallow copy bound to a particular session ID."""
        return ObservabilityClient(
            base_url=self._base_url,
            source_app=self._source_app,
            enabled=self._enabled,
            default_session_id=session_id,
        )


