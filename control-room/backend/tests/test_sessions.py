from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from control_room_api import create_app
from control_room_api.config import Settings

TEST_DB_PATH = Path("control_room_test.db")


@pytest.fixture()
def client():
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    settings = Settings(
        environment="test",
        database_url=f"sqlite+aiosqlite:///{TEST_DB_PATH}",
        auth_disabled=True,
    )
    app = create_app(settings)
    with TestClient(app) as client:
        yield client
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


def test_health(client: TestClient):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_create_and_list_sessions(client: TestClient):
    resp = client.post(
        "/api/sessions",
        json={"working_dir": "/tmp/project", "provider_config": None, "metadata": {}},
    )
    assert resp.status_code == 201
    session_id = resp.json()["id"]

    resp = client.get("/api/sessions")
    assert resp.status_code == 200
    sessions = resp.json()
    assert any(row["id"] == session_id for row in sessions)
