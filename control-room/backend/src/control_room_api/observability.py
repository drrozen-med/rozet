"""Wrapper around the existing Rozet observability client."""
from __future__ import annotations

import logging
from typing import Any

try:  # pragma: no cover - optional dependency during early bring-up
    from orchestrator.core.observability import ObservabilityClient
except Exception:  # pragma: no cover
    ObservabilityClient = None  # type: ignore

LOGGER = logging.getLogger(__name__)


def get_observability_client(default_session_id: str | None = None):
    if ObservabilityClient is None:
        LOGGER.warning("Observability client unavailable; events will be dropped")
        return None
    return ObservabilityClient(default_session_id=default_session_id)


def emit_event(client, event_type: str, payload: dict[str, Any]) -> None:
    if client is None:
        return
    try:
        client.send_event(event_type, payload)
    except Exception as exc:  # pragma: no cover - safety net
        LOGGER.warning("Failed to emit observability event %s: %s", event_type, exc)
