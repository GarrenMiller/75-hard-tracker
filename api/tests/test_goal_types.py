def test_list_goal_types(client):
    resp = client.get("/api/goal-types")
    assert resp.status_code == 200
    types = resp.get_json()["goal_types"]
    keys = {t["key"] for t in types}
    assert keys == {"daily_habit", "daily_quantity", "weekly_frequency"}
    for t in types:
        assert "config_schema" in t
        assert t["period"] in ("day", "week")


def test_daily_quantity_exposes_units(client):
    resp = client.get("/api/goal-types")
    types = {t["key"]: t for t in resp.get_json()["goal_types"]}
    units = types["daily_quantity"]["units"]
    assert "gallon" in units["volume"]
    assert "fl oz" in units["volume"]
    assert "lb" in units["weight"]
