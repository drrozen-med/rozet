"""Utility helpers."""
from __future__ import annotations

import secrets
import string

_ID_ALPHABET = string.ascii_lowercase + string.ascii_uppercase + string.digits + "_.:-"


def generate_id(prefix: str = "") -> str:
    core = "".join(secrets.choice(_ID_ALPHABET) for _ in range(24))
    return f"{prefix}{core}"
