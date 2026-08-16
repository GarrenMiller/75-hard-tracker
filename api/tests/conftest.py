import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402


@pytest.fixture()
def app(tmp_path):
    db_path = tmp_path / "test.db"
    return create_app({"TESTING": True, "DATABASE_PATH": str(db_path)})


@pytest.fixture()
def client(app):
    return app.test_client()


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def auth(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "display_name": "Test User",
        },
    )
    assert resp.status_code == 201
    data = resp.get_json()
    return {"token": data["token"], "user": data["user"]}


@pytest.fixture()
def freeze(monkeypatch):
    """Freeze the app clock to a fixed date, e.g. freeze('2026-08-15')."""

    def _freeze(date_str):
        import app.goals.routes as gr
        import app.goals.service as gs
        import app.plans.routes as pr
        import app.plans.service as ps
        import app.profile.service as pf
        import app.util as util

        monkeypatch.setattr(util, "today_str", lambda: date_str)
        monkeypatch.setattr(util, "utc_now_str", lambda: f"{date_str} 08:00:00")
        monkeypatch.setattr(gs, "today_str", lambda: date_str)
        monkeypatch.setattr(gr, "utc_now_str", lambda: f"{date_str} 08:00:00")
        monkeypatch.setattr(ps, "today_str", lambda: date_str)
        monkeypatch.setattr(ps, "utc_now_str", lambda: f"{date_str} 08:00:00")
        monkeypatch.setattr(pr, "utc_now_str", lambda: f"{date_str} 08:00:00")
        monkeypatch.setattr(pf, "today_str", lambda: date_str)
        return date_str

    return _freeze


def make_goal(client, token, key="daily_habit", **overrides):
    payload = {"name": "Water", "goal_type_key": key}
    if key == "daily_quantity":
        payload["config"] = {"target": 1, "unit": "gallon"}
    elif key == "weekly_frequency":
        payload["config"] = {"times_per_week": 3}
    payload.update(overrides)
    resp = client.post("/api/goals", json=payload, headers=auth_headers(token))
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()


def make_plan(client, token, goal_ids, **overrides):
    payload = {"name": "75 Hard", "goal_ids": goal_ids}
    payload.update(overrides)
    resp = client.post("/api/plans", json=payload, headers=auth_headers(token))
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()
