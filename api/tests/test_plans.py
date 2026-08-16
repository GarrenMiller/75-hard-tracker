from conftest import auth_headers, make_goal, make_plan


def check_in(client, token, goal_id, completed_at=None, value=None):
    payload = {} if completed_at is None else {"completed_at": completed_at}
    if value is not None:
        payload["value"] = value
    resp = client.post(
        f"/api/goals/{goal_id}/check-ins", json=payload, headers=auth_headers(token)
    )
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()


def progress(client, token, plan_id):
    resp = client.get(f"/api/plans/{plan_id}/progress", headers=auth_headers(token))
    assert resp.status_code == 200
    return resp.get_json()


def test_create_plan_with_goals(client, auth):
    goal = make_goal(client, auth["token"])
    plan = make_plan(client, auth["token"], [goal["id"]])
    assert plan["cycle_count"] == 1
    assert plan["goal_count"] == 1
    assert plan["difficulty_rules"]["lapse_policy"] == "restart_on_fail"
    assert len(plan["goals"]) == 1


def test_create_plan_no_goals(client, auth):
    plan = make_plan(client, auth["token"], [])
    assert plan["goal_count"] == 0


def test_create_plan_invalid_rules(client, auth):
    goal = make_goal(client, auth["token"])
    resp = client.post(
        "/api/plans",
        json={
            "name": "x",
            "goal_ids": [goal["id"]],
            "difficulty_rules": {"lapse_policy": "banana"},
        },
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 400


def test_create_plan_with_unowned_goal(client, auth, app):
    other = app.test_client()
    other_reg = other.post(
        "/api/auth/register",
        json={"email": "other@example.com", "password": "password123", "display_name": "O"},
    )
    other_token = other_reg.get_json()["token"]
    resp = other.post(
        "/api/goals",
        json={"name": "x", "goal_type_key": "daily_habit"},
        headers=auth_headers(other_token),
    )
    other_goal = resp.get_json()
    resp = client.post(
        "/api/plans",
        json={"name": "x", "goal_ids": [other_goal["id"]]},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 404


def test_get_plan_detail(client, auth):
    goal = make_goal(client, auth["token"])
    plan = make_plan(client, auth["token"], [goal["id"]])
    resp = client.get(f"/api/plans/{plan['id']}", headers=auth_headers(auth["token"]))
    assert resp.status_code == 200
    assert resp.get_json()["goals"][0]["id"] == goal["id"]


def test_list_plans(client, auth):
    goal = make_goal(client, auth["token"])
    make_plan(client, auth["token"], [goal["id"]])
    resp = client.get("/api/plans", headers=auth_headers(auth["token"]))
    assert resp.status_code == 200
    assert len(resp.get_json()["plans"]) == 1


def test_delete_plan(client, auth):
    goal = make_goal(client, auth["token"])
    plan = make_plan(client, auth["token"], [goal["id"]])
    resp = client.delete(f"/api/plans/{plan['id']}", headers=auth_headers(auth["token"]))
    assert resp.status_code == 200
    resp = client.get(f"/api/plans/{plan['id']}", headers=auth_headers(auth["token"]))
    assert resp.status_code == 404


def test_progress_fresh_plan(client, auth, freeze):
    freeze("2026-08-16")
    goal = make_goal(client, auth["token"])
    plan = make_plan(client, auth["token"], [goal["id"]])
    data = progress(client, auth["token"], plan["id"])
    assert data["cycle"]["day"] == 1
    assert data["cycle"]["missed_days"] == 0
    assert data["cycle"]["total_days"] == 75
    assert data["days"][-1]["status"] == "pending"
    assert data["goals"][0]["today"]["completed"] is False


def test_progress_days_include_per_goal_detail(client, auth, freeze):
    freeze("2026-08-15")
    goal1 = make_goal(client, auth["token"])
    goal2 = make_goal(client, auth["token"], key="daily_quantity")
    plan = make_plan(client, auth["token"], [goal1["id"], goal2["id"]])
    check_in(client, auth["token"], goal1["id"])
    check_in(client, auth["token"], goal2["id"], "2026-08-15 09:00:00", value={"amount": 1})

    data = progress(client, auth["token"], plan["id"])
    day = data["days"][-1]
    assert day["date"] == "2026-08-15"
    assert day["status"] == "completed"
    assert {g["id"] for g in day["goals"]} == {goal1["id"], goal2["id"]}
    by_id = {g["id"]: g for g in day["goals"]}
    assert by_id[goal1["id"]]["completed"] is True
    assert by_id[goal2["id"]]["completed"] is True
    assert by_id[goal2["id"]]["detail"]["current"] == 1

    freeze("2026-08-16")
    check_in(client, auth["token"], goal1["id"])
    data = progress(client, auth["token"], plan["id"])
    day = data["days"][-1]
    assert day["status"] == "partial"
    by_id = {g["id"]: g for g in day["goals"]}
    assert by_id[goal1["id"]]["completed"] is True
    assert by_id[goal2["id"]]["completed"] is False
    assert by_id[goal2["id"]]["progress"] == 0


def test_progress_completed_days(client, auth, freeze):
    freeze("2026-08-15")
    goal = make_goal(client, auth["token"])
    plan = make_plan(client, auth["token"], [goal["id"]])
    check_in(client, auth["token"], goal["id"])
    freeze("2026-08-16")
    check_in(client, auth["token"], goal["id"])
    data = progress(client, auth["token"], plan["id"])
    assert data["cycle"]["day"] == 2
    assert data["cycle"]["missed_days"] == 0
    assert [d["status"] for d in data["days"]] == ["completed", "completed"]
    assert data["goals"][0]["streak"] == 2


def test_restart_on_fail_auto_restarts(client, auth, freeze):
    freeze("2026-08-15")
    goal = make_goal(client, auth["token"])
    plan = make_plan(client, auth["token"], [goal["id"]])
    check_in(client, auth["token"], goal["id"])
    freeze("2026-08-16")
    check_in(client, auth["token"], goal["id"])
    freeze("2026-08-17")
    freeze("2026-08-18")
    data = progress(client, auth["token"], plan["id"])
    assert data["cycle"]["day"] == 1
    assert data["cycle"]["missed_days"] == 0
    resp = client.get(f"/api/plans/{plan['id']}", headers=auth_headers(auth["token"]))
    assert resp.get_json()["cycle_count"] == 2
    assert resp.get_json()["status"] == "active"


def test_grace_days_in_grace_then_failed(client, auth, freeze):
    freeze("2026-08-15")
    goal = make_goal(client, auth["token"])
    plan = make_plan(
        client,
        auth["token"],
        [goal["id"]],
        difficulty_rules={"lapse_policy": "grace_days", "grace_days": 1},
    )
    check_in(client, auth["token"], goal["id"])
    freeze("2026-08-16")
    check_in(client, auth["token"], goal["id"])
    freeze("2026-08-18")
    data = progress(client, auth["token"], plan["id"])
    assert data["plan"]["status"] == "in_grace"
    assert data["cycle"]["missed_days"] == 1
    freeze("2026-08-19")
    data = progress(client, auth["token"], plan["id"])
    assert data["plan"]["status"] == "failed"


def test_grace_days_zero_fails_on_first_miss(client, auth, freeze):
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
    data = progress(client, auth["token"], plan["id"])
    assert data["plan"]["status"] == "failed"


def test_manual_restart_after_failure(client, auth, freeze):
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
    data = progress(client, auth["token"], plan["id"])
    assert data["plan"]["status"] == "failed"
    resp = client.post(
        f"/api/plans/{plan['id']}/restart", headers=auth_headers(auth["token"])
    )
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "active"
    assert resp.get_json()["cycle_count"] == 2
    data = progress(client, auth["token"], plan["id"])
    assert data["cycle"]["day"] == 1


def test_weekly_goal_not_missed_mid_week(client, auth, freeze):
    freeze("2026-08-17")
    goal = make_goal(client, auth["token"], key="weekly_frequency")
    plan = make_plan(
        client,
        auth["token"],
        [goal["id"]],
        difficulty_rules={"lapse_policy": "grace_days", "grace_days": 5},
    )
    data = progress(client, auth["token"], plan["id"])
    assert data["goals"][0]["today"]["completed"] is False
    assert data["cycle"]["missed_days"] == 0
    freeze("2026-08-24")
    data = progress(client, auth["token"], plan["id"])
    assert data["plan"]["status"] == "in_grace"
    assert data["cycle"]["missed_days"] == 1


def test_weekly_goal_completes_mid_week(client, auth, freeze):
    freeze("2026-08-17")
    goal = make_goal(client, auth["token"], key="weekly_frequency")
    plan = make_plan(client, auth["token"], [goal["id"]])
    check_in(client, auth["token"], goal["id"], "2026-08-17 09:00:00")
    check_in(client, auth["token"], goal["id"], "2026-08-18 09:00:00")
    check_in(client, auth["token"], goal["id"], "2026-08-19 09:00:00")
    data = progress(client, auth["token"], plan["id"])
    assert data["goals"][0]["today"]["completed"] is True
    assert data["cycle"]["missed_days"] == 0


def test_update_plan_replaces_goals(client, auth):
    goal1 = make_goal(client, auth["token"])
    goal2 = make_goal(client, auth["token"])
    plan = make_plan(client, auth["token"], [goal1["id"]])
    resp = client.patch(
        f"/api/plans/{plan['id']}",
        json={"goal_ids": [goal1["id"], goal2["id"]], "name": "Updated"},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["name"] == "Updated"
    assert data["goal_count"] == 2
