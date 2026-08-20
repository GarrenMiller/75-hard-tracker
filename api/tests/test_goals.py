from conftest import auth_headers, make_goal, make_plan


def test_create_daily_habit(client, auth):
    goal = make_goal(client, auth["token"])
    assert goal["goal_type_key"] == "daily_habit"
    assert goal["config"] == {}
    assert goal["today"]["completed"] is False


def test_create_daily_quantity(client, auth):
    goal = make_goal(client, auth["token"], key="daily_quantity")
    assert goal["config"] == {"target": 1, "unit": "gallon"}


def test_create_weekly_frequency(client, auth):
    goal = make_goal(client, auth["token"], key="weekly_frequency")
    assert goal["config"] == {"times_per_week": 3}


def test_create_unknown_type(client, auth):
    resp = client.post(
        "/api/goals",
        json={"name": "x", "goal_type_key": "nope"},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 400


def test_create_daily_quantity_missing_target(client, auth):
    resp = client.post(
        "/api/goals",
        json={"name": "x", "goal_type_key": "daily_quantity", "config": {"unit": "g"}},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 400


def test_create_daily_quantity_bad_target_type(client, auth):
    resp = client.post(
        "/api/goals",
        json={"name": "x", "goal_type_key": "daily_quantity", "config": {"target": "lots", "unit": "g"}},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 400


def test_unknown_config_field_rejected(client, auth):
    resp = client.post(
        "/api/goals",
        json={"name": "x", "goal_type_key": "daily_habit", "config": {"bogus": 1}},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 400


def test_list_goals(client, auth):
    make_goal(client, auth["token"])
    resp = client.get("/api/goals", headers=auth_headers(auth["token"]))
    assert resp.status_code == 200
    assert len(resp.get_json()["goals"]) == 1


def test_get_goal(client, auth):
    goal = make_goal(client, auth["token"])
    resp = client.get(f"/api/goals/{goal['id']}", headers=auth_headers(auth["token"]))
    assert resp.status_code == 200
    assert resp.get_json()["id"] == goal["id"]


def test_goal_not_found(client, auth):
    resp = client.get("/api/goals/999", headers=auth_headers(auth["token"]))
    assert resp.status_code == 404


def test_update_goal(client, auth):
    goal = make_goal(client, auth["token"])
    resp = client.patch(
        f"/api/goals/{goal['id']}",
        json={"name": "Renamed", "active": False},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["name"] == "Renamed"
    assert data["active"] is False


def test_delete_goal(client, auth):
    goal = make_goal(client, auth["token"])
    resp = client.delete(f"/api/goals/{goal['id']}", headers=auth_headers(auth["token"]))
    assert resp.status_code == 200
    resp = client.get(f"/api/goals/{goal['id']}", headers=auth_headers(auth["token"]))
    assert resp.status_code == 404


def test_check_in_habit_completes_day(client, auth, freeze):
    freeze("2026-08-16")
    goal = make_goal(client, auth["token"])
    make_plan(client, auth["token"], [goal["id"]])
    resp = client.post(
        f"/api/goals/{goal['id']}/check-ins",
        json={},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 201
    resp = client.get(f"/api/goals/{goal['id']}", headers=auth_headers(auth["token"]))
    assert resp.get_json()["today"]["completed"] is True


def test_check_in_quantity_requires_amount(client, auth):
    goal = make_goal(client, auth["token"], key="daily_quantity")
    make_plan(client, auth["token"], [goal["id"]])
    resp = client.post(
        f"/api/goals/{goal['id']}/check-ins",
        json={"value": {}},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 400


def test_check_in_quantity_progress(client, auth, freeze):
    freeze("2026-08-16")
    goal = make_goal(client, auth["token"], key="daily_quantity")
    make_plan(client, auth["token"], [goal["id"]])
    resp = client.post(
        f"/api/goals/{goal['id']}/check-ins",
        json={"value": {"amount": 0.5}},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 201
    resp = client.get(f"/api/goals/{goal['id']}", headers=auth_headers(auth["token"]))
    today = resp.get_json()["today"]
    assert today["completed"] is False
    assert today["progress"] == 0.5
    resp = client.post(
        f"/api/goals/{goal['id']}/check-ins",
        json={"value": {"amount": 0.5}},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 201
    resp = client.get(f"/api/goals/{goal['id']}", headers=auth_headers(auth["token"]))
    assert resp.get_json()["today"]["completed"] is True


def test_check_in_quantity_sub_units(client, auth, freeze):
    freeze("2026-08-16")
    goal = make_goal(client, auth["token"], key="daily_quantity")
    make_plan(client, auth["token"], [goal["id"]])
    resp = client.post(
        f"/api/goals/{goal['id']}/check-ins",
        json={"value": {"amount": 16, "unit": "fl oz"}},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 201
    resp = client.get(f"/api/goals/{goal['id']}", headers=auth_headers(auth["token"]))
    today = resp.get_json()["today"]
    assert today["completed"] is False
    assert today["progress"] == 0.125
    resp = client.post(
        f"/api/goals/{goal['id']}/check-ins",
        json={"value": {"amount": 112, "unit": "fl oz"}},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 201
    resp = client.get(f"/api/goals/{goal['id']}", headers=auth_headers(auth["token"]))
    assert resp.get_json()["today"]["completed"] is True


def test_check_in_quantity_oz_alias_volume(client, auth, freeze):
    freeze("2026-08-16")
    goal = make_goal(client, auth["token"], key="daily_quantity")
    make_plan(client, auth["token"], [goal["id"]])
    resp = client.post(
        f"/api/goals/{goal['id']}/check-ins",
        json={"value": {"amount": 128, "unit": "oz"}},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 201
    resp = client.get(f"/api/goals/{goal['id']}", headers=auth_headers(auth["token"]))
    assert resp.get_json()["today"]["completed"] is True


def test_check_in_quantity_weight_unit(client, auth, freeze):
    freeze("2026-08-16")
    goal = make_goal(client, auth["token"], key="daily_quantity", config={"target": 1, "unit": "lb"})
    make_plan(client, auth["token"], [goal["id"]])
    resp = client.post(
        f"/api/goals/{goal['id']}/check-ins",
        json={"value": {"amount": 8, "unit": "oz"}},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 201
    resp = client.get(f"/api/goals/{goal['id']}", headers=auth_headers(auth["token"]))
    today = resp.get_json()["today"]
    assert today["completed"] is False
    assert today["progress"] == 0.5


def test_check_in_quantity_incompatible_unit(client, auth):
    goal = make_goal(client, auth["token"], key="daily_quantity")
    make_plan(client, auth["token"], [goal["id"]])
    resp = client.post(
        f"/api/goals/{goal['id']}/check-ins",
        json={"value": {"amount": 1, "unit": "lb"}},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 400


def test_check_in_quantity_unknown_unit(client, auth):
    goal = make_goal(client, auth["token"], key="daily_quantity")
    make_plan(client, auth["token"], [goal["id"]])
    resp = client.post(
        f"/api/goals/{goal['id']}/check-ins",
        json={"value": {"amount": 1, "unit": "widgets"}},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 400


def test_list_check_ins(client, auth, freeze):
    freeze("2026-08-16")
    goal = make_goal(client, auth["token"])
    make_plan(client, auth["token"], [goal["id"]])
    client.post(f"/api/goals/{goal['id']}/check-ins", json={}, headers=auth_headers(auth["token"]))
    resp = client.get(f"/api/goals/{goal['id']}/check-ins", headers=auth_headers(auth["token"]))
    assert resp.status_code == 200
    assert len(resp.get_json()["check_ins"]) == 1


def test_check_in_rejected_without_plan(client, auth):
    goal = make_goal(client, auth["token"])
    resp = client.post(
        f"/api/goals/{goal['id']}/check-ins",
        json={},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 400
    assert "active plan" in resp.get_json()["error"]


def test_check_in_rejected_for_failed_plan(client, auth, freeze):
    freeze("2026-08-15")
    goal = make_goal(client, auth["token"])
    plan = make_plan(
        client,
        auth["token"],
        [goal["id"]],
        difficulty_rules={"lapse_policy": "grace_days", "grace_days": 0},
    )
    client.post(f"/api/goals/{goal['id']}/check-ins", json={}, headers=auth_headers(auth["token"]))
    freeze("2026-08-17")
    data = client.get(f"/api/plans/{plan['id']}/progress", headers=auth_headers(auth["token"]))
    assert data.get_json()["plan"]["status"] == "failed"
    resp = client.post(
        f"/api/goals/{goal['id']}/check-ins",
        json={},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 400


def test_check_in_records_plan_id(client, auth, freeze):
    freeze("2026-08-16")
    goal = make_goal(client, auth["token"])
    plan = make_plan(client, auth["token"], [goal["id"]])
    resp = client.post(
        f"/api/goals/{goal['id']}/check-ins",
        json={},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 201
    assert resp.get_json()["plan_id"] == plan["id"]


def test_check_in_multiple_active_plans_requires_plan_id(client, auth):
    goal = make_goal(client, auth["token"])
    make_plan(client, auth["token"], [goal["id"]])
    plan2 = make_plan(client, auth["token"], [goal["id"]])
    resp = client.post(
        f"/api/goals/{goal['id']}/check-ins",
        json={},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 400
    resp = client.post(
        f"/api/goals/{goal['id']}/check-ins",
        json={"plan_id": plan2["id"]},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 201
    assert resp.get_json()["plan_id"] == plan2["id"]


def test_check_in_bad_plan_id_rejected(client, auth):
    goal = make_goal(client, auth["token"])
    make_plan(client, auth["token"], [goal["id"]])
    make_plan(client, auth["token"], [goal["id"]])
    resp = client.post(
        f"/api/goals/{goal['id']}/check-ins",
        json={"plan_id": 999},
        headers=auth_headers(auth["token"]),
    )
    assert resp.status_code == 400
