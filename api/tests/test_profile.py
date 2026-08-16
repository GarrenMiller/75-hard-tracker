from conftest import auth_headers, make_goal, make_plan


def profile(client, token):
    resp = client.get("/api/profile", headers=auth_headers(token))
    assert resp.status_code == 200
    return resp.get_json()


def check_in(client, token, goal_id, completed_at=None):
    payload = {} if completed_at is None else {"completed_at": completed_at}
    resp = client.post(
        f"/api/goals/{goal_id}/check-ins", json=payload, headers=auth_headers(token)
    )
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()


def test_profile_requires_auth(client):
    resp = client.get("/api/profile")
    assert resp.status_code == 401


def test_profile_fresh_account(client, auth):
    data = profile(client, auth["token"])
    assert data["user"]["email"] == "user@example.com"
    assert "created_at" in data["user"]
    assert data["stats"] == {
        "goals_total": 0,
        "goals_active": 0,
        "plans_total": 0,
        "plans_active": 0,
        "plans_failed": 0,
        "check_ins_total": 0,
        "best_streak": 0,
        "member_days": 0,
    }
    assert data["goals"] == []
    assert data["plans"] == []


def test_profile_counts(client, auth):
    goal = make_goal(client, auth["token"])
    plan = make_plan(client, auth["token"], [goal["id"]])
    check_in(client, auth["token"], goal["id"])
    check_in(client, auth["token"], goal["id"])

    data = profile(client, auth["token"])
    stats = data["stats"]
    assert stats["goals_total"] == 1
    assert stats["goals_active"] == 1
    assert stats["plans_total"] == 1
    assert stats["plans_active"] == 1
    assert stats["plans_failed"] == 0
    assert stats["check_ins_total"] == 2

    g = data["goals"][0]
    assert g["goal"]["id"] == goal["id"]
    assert g["total_completions"] == 2
    assert g["last_completed_at"]

    p = data["plans"][0]
    assert p["plan"]["id"] == plan["id"]
    assert p["cycle_day"] == 1
    assert p["cycle_total_days"] == 75


def test_profile_streak(client, auth, freeze):
    freeze("2026-08-15")
    goal = make_goal(client, auth["token"])
    check_in(client, auth["token"], goal["id"])
    freeze("2026-08-16")
    check_in(client, auth["token"], goal["id"])

    data = profile(client, auth["token"])
    assert data["goals"][0]["streak"] == 2
    assert data["stats"]["best_streak"] == 2


def test_profile_streak_breaks_on_miss(client, auth, freeze):
    freeze("2026-08-15")
    goal = make_goal(client, auth["token"])
    check_in(client, auth["token"], goal["id"])
    freeze("2026-08-17")
    check_in(client, auth["token"], goal["id"])

    data = profile(client, auth["token"])
    assert data["goals"][0]["streak"] == 1
    assert data["stats"]["best_streak"] == 1


def test_profile_inactive_goal_counted(client, auth):
    goal = make_goal(client, auth["token"])
    client.patch(
        f"/api/goals/{goal['id']}",
        json={"active": False},
        headers=auth_headers(auth["token"]),
    )
    data = profile(client, auth["token"])
    assert data["stats"]["goals_total"] == 1
    assert data["stats"]["goals_active"] == 0


def test_profile_goal_plan_association(client, auth):
    goal_in = make_goal(client, auth["token"])
    goal_standalone = make_goal(client, auth["token"])
    plan = make_plan(client, auth["token"], [goal_in["id"]])

    data = profile(client, auth["token"])
    by_id = {g["goal"]["id"]: g for g in data["goals"]}
    assert by_id[goal_in["id"]]["plans"] == [{"id": plan["id"], "name": plan["name"]}]
    assert by_id[goal_standalone["id"]]["plans"] == []


def test_profile_failed_plan(client, auth, freeze):
    freeze("2026-08-15")
    goal = make_goal(client, auth["token"])
    plan = make_plan(
        client,
        auth["token"],
        [goal["id"]],
        difficulty_rules={"lapse_policy": "grace_days", "grace_days": 0},
    )
    check_in(client, auth["token"], goal["id"])
    freeze("2026-08-17")

    data = profile(client, auth["token"])
    assert data["stats"]["plans_active"] == 0
    assert data["stats"]["plans_failed"] == 1
    p = data["plans"][0]
    assert p["cycle_day"] is None
