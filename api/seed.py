"""Seed demo data: a user, several goals, and two plans backfilled with history.

Run inside the api container:  docker compose run --rm api python seed.py
"""
from datetime import date, timedelta

from app import create_app
from app.db import get_db

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "password123"


def _post(client, path, headers, payload):
    resp = client.post(path, json=payload, headers=headers)
    assert resp.status_code in (200, 201), (path, resp.status_code, resp.get_json())
    return resp.get_json()


def _check_in(client, headers, goal_id, day, value=None):
    payload = {"completed_at": f"{day.isoformat()} 09:00:00"}
    if value is not None:
        payload["value"] = value
    return _post(client, f"/api/goals/{goal_id}/check-ins", headers, payload)


def _backdate_cycle(db, plan_id, started_at):
    db.execute(
        "UPDATE plan_cycles SET started_at = ? "
        "WHERE id = (SELECT id FROM plan_cycles WHERE plan_id = ? ORDER BY started_at LIMIT 1)",
        (started_at, plan_id),
    )
    db.commit()


def _backfill_weekly(client, headers, goal_id, weeks_back=6, weeks=6):
    today = date.today()
    current_week_start = today - timedelta(days=today.weekday())
    for w in range(weeks_back, weeks_back - weeks, -1):
        week_start = current_week_start - timedelta(weeks=w)
        for day_offset in (1, 3, 5):
            day = week_start + timedelta(days=day_offset)
            if day > today:
                continue
            _check_in(client, headers, goal_id, day)


def run():
    app = create_app()
    client = app.test_client()

    with app.app_context():
        db = get_db()
        db.execute("DELETE FROM users WHERE email = ?", (DEMO_EMAIL,))
        db.commit()

    user = client.post(
        "/api/auth/register",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD, "display_name": "Demo"},
    ).get_json()
    headers = {"Authorization": f"Bearer {user['token']}"}

    water = _post(
        client, "/api/goals", headers,
        {"name": "Drink a gallon of water", "goal_type_key": "daily_quantity", "config": {"target": 1, "unit": "gallon"}},
    )
    workout = _post(
        client, "/api/goals", headers,
        {"name": "Work out 3x per week", "goal_type_key": "weekly_frequency", "config": {"times_per_week": 3}},
    )
    reading = _post(
        client, "/api/goals", headers,
        {"name": "Read 10 pages", "goal_type_key": "daily_habit"},
    )
    meditate = _post(
        client, "/api/goals", headers,
        {"name": "Meditate 10 minutes", "goal_type_key": "daily_habit"},
    )
    sit_ups = _post(
        client, "/api/goals", headers,
        {"name": "50 sit-ups", "goal_type_key": "daily_habit"},
    )
    client.patch(
        f"/api/goals/{sit_ups['id']}", json={"active": False}, headers=headers
    )

    plan = _post(
        client, "/api/plans", headers,
        {
            "name": "75 Hard",
            "goal_ids": [water["id"], workout["id"], reading["id"], meditate["id"]],
            "difficulty_rules": {"duration_days": 75, "lapse_policy": "grace_days", "grace_days": 2},
        },
    )
    redemption = _post(
        client, "/api/plans", headers,
        {
            "name": "Redemption",
            "goal_ids": [sit_ups["id"]],
            "difficulty_rules": {"duration_days": 75, "lapse_policy": "restart_on_fail"},
        },
    )

    today = date.today()

    with app.app_context():
        db = get_db()
        _backdate_cycle(db, plan["id"], f"{(today - timedelta(days=30)).isoformat()} 08:00:00")
        _backdate_cycle(db, redemption["id"], f"{(today - timedelta(days=10)).isoformat()} 08:00:00")

    for offset in range(30, 0, -1):
        day = today - timedelta(days=offset)
        _check_in(client, headers, water["id"], day, {"amount": 1})
        _check_in(client, headers, reading["id"], day)
        _check_in(client, headers, meditate["id"], day)

    _backfill_weekly(client, headers, workout["id"])

    for offset in (10, 9, 8, 7, 6, 4, 3, 2, 1):
        day = today - timedelta(days=offset)
        _check_in(client, headers, sit_ups["id"], day)

    print("Seeded demo data:")
    print(f"  login:    {DEMO_EMAIL} / {DEMO_PASSWORD}")
    print(f"  plan 1:   {plan['name']} (day 31 of 75, all goals on track)")
    print(f"  plan 2:   {redemption['name']} (auto-restarted once — shows cycle #2)")


if __name__ == "__main__":
    run()
