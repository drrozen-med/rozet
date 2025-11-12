"""Entry point for running the control room API."""
from __future__ import annotations

import uvicorn

from control_room_api import create_app
from control_room_api.config import get_settings


def run() -> None:
    settings = get_settings()
    app = create_app(settings)
    uvicorn.run(app, host="0.0.0.0", port=8001)


if __name__ == "__main__":  # pragma: no cover
    run()
