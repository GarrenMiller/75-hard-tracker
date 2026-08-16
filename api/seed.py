"""Seed demo data: a user, three goals, and a plan backfilled with history.

Run inside the api container:  docker compose run --rm api python seed.py
"""
from datetime import date, timedelta

from app import create_app
from app.db import get_db


def _user_exists(email):
    db = get_db()
    return db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone() is not None


def run():
    app = create_app()
    client = app.test_client()

    with app.app_context():
        if _user_exists("demo@example.com"):
            print("Demo data already exists. Skipping.")
            return

    user = client.post(
        "/api/auth/register",
        json={"email": "demo@example.com", "password": "password123", "display_name": "Demo"},
    ).get_json()
    headers = {"Authorization": f"Bearer {user['token']}"}

    water = client.post(
        "/api/goals",
        json={"name": "Drink a gallon of water", "goal_type_key": "daily_quantity", "config": {"target": 1, "unit": "gallon"}},
        headers=headers,
    ).get_json()
    workout = client.post(
        "/api/goals",
        json={"name": "Work out 3x per week", "goal_type_key": "weekly_frequency", "config": {"times_per_week": 3}},
        headers=headers,
    ).get_json()
    reading = client.post(
        "/api/goals",
        json={"name": "Read 10 pages", "goal_type_key": "daily_habit"},
        headers=headers,
    ).get_json()

    plan = client.post(
        "/api/plans",
        json={
            "name": "75 Hard",
            "goal_ids": [water["id"], workout["id"], reading["id"]],
            "difficulty_rules": {"duration_days": 75, "lapse_policy": "grace_days", "grace_days": 2},
        },
        headers=headers,
    ).get_json()

    today = date.today()
    start = today - timedelta(days=5)

    with app.app_context():
        db = get_db()
        db.execute(
            "UPDATE plan_cycles SET started_at = ? "
            "WHERE id = (SELECT id FROM plan_cycles WHERE plan_id = ? ORDER BY started_at LIMIT 1)",
            (f"{start.isoformat()} 08:00:00", plan["id"]),
        )
        db.commit()

    for offset in range(5, 0, -1):
        day = (today - timedelta(days=offset)).strftime("%Y-%m-%d")
        client.post(
            f"/api/goals/{water['id']}/check-ins",
            json={"completed_at": f"{day} 09:00:00", "value": {"amount": 1}},
            headers=headers,
        )
        client.post(
            f"/api/goals/{reading['id']}/check-ins",
            json={"completed_at": f"{day} 21:00:00"},
            headers=headers,
        )

    for offset in (2, 4):
        day = (today - timedelta(days=offset)).strftime("%Y-%m-%d")
        client.post(
            f"/api/goals/{workout['id']}/check-ins",
            json={"completed_at": f"{day} 18:00:00"},
            headers=headers,
        )

    print("Seeded demo data:")
    print("  login:    demo@example.com / password123")
    print(f"  plan id:  {plan['id']} (day 5 of 75)")


if __name__ == "__main__":
    run()
