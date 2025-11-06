"""Basic observability client for sending events to the observability system."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore

LOGGER = logging.getLogger(__name__)

DEFAULT_OBSERVABILITY_URL = "http://localhost:4000/events"


class ObservabilityClient:
    """Client for sending events to the observability system."""

    def __init__(self, base_url: str = DEFAULT_OBSERVABILITY_URL, enabled: bool = True) -> None:
        self._base_url = base_url
        self._enabled = enabled and requests is not None
        if not self._enabled and enabled:
            LOGGER.warning(
                "Observability disabled: 'requests' package not installed. "
                "Install with: pip install requests"
            )

    def send_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        *,
        source_app: str = "orchestrator",
        session_id: Optional[str] = None,
    ) -> None:
        """Send an event to the observability server.
        
        Args:
            event_type: Type of event (e.g., "TaskPlanned", "TaskAssigned")
            payload: Event payload dictionary
            source_app: Source application identifier
            session_id: Optional session identifier
        """
        if not self._enabled:
            LOGGER.debug("Observability disabled, skipping event: %s", event_type)
            return

        event = {
            "source_app": source_app,
            "hook_event_type": event_type,
            "payload": payload,
        }
        if session_id:
            event["session_id"] = session_id

        try:
            response = requests.post(  # type: ignore
                self._base_url,
                json=event,
                timeout=2.0,
            )
            response.raise_for_status()
            LOGGER.debug("Sent observability event: %s", event_type)
        except Exception as exc:
            # Don't fail the orchestrator if observability is down
            LOGGER.warning("Failed to send observability event %s: %s", event_type, exc)

    def task_planned(self, task_id: str, description: str, **kwargs: Any) -> None:
        """Send a TaskPlanned event."""
        self.send_event(
            "TaskPlanned",
            {"task_id": task_id, "description": description, **kwargs},
        )

    def task_assigned(self, task_id: str, worker_id: str, **kwargs: Any) -> None:
        """Send a TaskAssigned event."""
        self.send_event(
            "TaskAssigned",
            {"task_id": task_id, "worker_id": worker_id, **kwargs},
        )

    def worker_completed(self, task_id: str, success: bool, **kwargs: Any) -> None:
        """Send a WorkerCompleted event."""
        self.send_event(
            "WorkerCompleted",
            {"task_id": task_id, "success": success, **kwargs},
        )

