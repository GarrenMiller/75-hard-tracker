import json

from flask import Blueprint, g, jsonify, request

from ..db import get_db
from ..errors import ApiError
from ..goal_types.registry import get as get_goal_type
from ..util import utc_now_str
from ..auth.utils import require_auth
from .service import (
    check_in_payload,
    get_goal_or_404,
    goal_payload,
    list_check_ins,
)

goals_bp = Blueprint("goals", __name__)


def _body():
    return request.get_json(silent=True) or {}


@goals_bp.post("")
@require_auth
@require_auth
def create_goal():
    data = _body()
    name = (data.get("name") or "").strip()
    key = data.get("goal_type_key")
    config = data.get("config") or {}

    if not name:
        raise ApiError("name is required", 400)
    goal_type = get_goal_type(key)
    if goal_type is None:
        raise ApiError(f"Unknown goal type: {key}", 400)
    try:
        config = goal_type.validate_config(config)
    except ValueError as e:
        raise ApiError(str(e), 400)

    db = get_db()
    cur = db.execute(
        "INSERT INTO goals (user_id, goal_type_key, name, config) VALUES (?, ?, ?, ?)",
        (g.user["id"], key, name, json.dumps(config)),
    )
    db.commit()
    row = get_goal_or_404(cur.lastrowid, g.user["id"])
    return jsonify(goal_payload(row, include_today=True)), 201


@goals_bp.get("")
@require_auth
@require_auth
def list_goals():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM goals WHERE user_id = ? ORDER BY active DESC, created_at DESC",
        (g.user["id"],),
    ).fetchall()
    return jsonify({"goals": [goal_payload(r, include_today=True) for r in rows]})


@goals_bp.get("/<int:goal_id>")
@require_auth
@require_auth
def get_goal(goal_id):
    row = get_goal_or_404(goal_id, g.user["id"])
    return jsonify(goal_payload(row, include_today=True))


@goals_bp.patch("/<int:goal_id>")
@require_auth
@require_auth
def update_goal(goal_id):
    row = get_goal_or_404(goal_id, g.user["id"])
    data = _body()
    goal_type = get_goal_type(row["goal_type_key"])

    name = data.get("name", row["name"])
    config = data.get("config", json.loads(row["config"] or "{}"))
    active = data.get("active", row["active"])
    try:
        config = goal_type.validate_config(config)
    except ValueError as e:
        raise ApiError(str(e), 400)

    db = get_db()
    db.execute(
        "UPDATE goals SET name = ?, config = ?, active = ? WHERE id = ?",
        (name.strip() or row["name"], json.dumps(config), 1 if active else 0, goal_id),
    )
    db.commit()
    row = get_goal_or_404(goal_id, g.user["id"])
    return jsonify(goal_payload(row, include_today=True))


@goals_bp.delete("/<int:goal_id>")
@require_auth
@require_auth
def delete_goal(goal_id):
    get_goal_or_404(goal_id, g.user["id"])
    db = get_db()
    db.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    db.commit()
    return jsonify({"ok": True})


@goals_bp.post("/<int:goal_id>/check-ins")
@require_auth
@require_auth
def create_check_in(goal_id):
    row = get_goal_or_404(goal_id, g.user["id"])
    data = _body()
    goal_type = get_goal_type(row["goal_type_key"])
    value = data.get("value") or {}
    try:
        value = goal_type.validate_check_in_value(json.loads(row["config"] or "{}"), value)
    except ValueError as e:
        raise ApiError(str(e), 400)

    db = get_db()
    active_plans = db.execute(
        "SELECT p.id FROM plan_goals pg JOIN plans p ON p.id = pg.plan_id "
        "WHERE pg.goal_id = ? AND p.user_id = ? AND p.status IN ('active', 'in_grace')",
        (goal_id, g.user["id"]),
    ).fetchall()
    if not active_plans:
        raise ApiError("Goal is not part of an active plan", 400)

    plan_ids = {r["id"] for r in active_plans}
    if len(plan_ids) == 1:
        plan_id = plan_ids.pop()
    else:
        plan_id = data.get("plan_id")
        if plan_id not in plan_ids:
            raise ApiError(
                "plan_id is required and must be an active plan containing this goal", 400
            )

    completed_at = data.get("completed_at") or utc_now_str()

    cur = db.execute(
        "INSERT INTO check_ins (user_id, goal_id, plan_id, completed_at, value) VALUES (?, ?, ?, ?, ?)",
        (g.user["id"], goal_id, plan_id, completed_at, json.dumps(value)),
    )
    db.commit()
    c = db.execute("SELECT * FROM check_ins WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(check_in_payload(c)), 201


@goals_bp.get("/<int:goal_id>/check-ins")
@require_auth
@require_auth
def get_check_ins(goal_id):
    get_goal_or_404(goal_id, g.user["id"])
    rows = list_check_ins(goal_id, g.user["id"])
    return jsonify({"check_ins": [check_in_payload(r) for r in rows]})
