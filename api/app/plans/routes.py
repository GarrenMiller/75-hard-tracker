import json

from flask import Blueprint, g, jsonify, request

from ..db import get_db
from ..errors import ApiError
from ..goals.service import get_goal_or_404
from ..util import utc_now_str
from ..auth.utils import require_auth
from .service import (
    DEFAULT_DIFFICULTY_RULES,
    compute_progress,
    get_plan_or_404,
    plan_payload,
    sync_plan,
)

plans_bp = Blueprint("plans", __name__)


def _body():
    return request.get_json(silent=True) or {}


def validate_rules(rules):
    try:
        duration = int(rules.get("duration_days", DEFAULT_DIFFICULTY_RULES["duration_days"]))
    except (TypeError, ValueError):
        raise ApiError("difficulty_rules.duration_days must be an integer", 400)
    if duration <= 0:
        raise ApiError("difficulty_rules.duration_days must be greater than 0", 400)

    policy = rules.get("lapse_policy", DEFAULT_DIFFICULTY_RULES["lapse_policy"])
    if policy not in ("restart_on_fail", "grace_days"):
        raise ApiError("difficulty_rules.lapse_policy must be 'restart_on_fail' or 'grace_days'", 400)

    try:
        grace = int(rules.get("grace_days", DEFAULT_DIFFICULTY_RULES["grace_days"]))
    except (TypeError, ValueError):
        raise ApiError("difficulty_rules.grace_days must be an integer", 400)
    if grace < 0:
        raise ApiError("difficulty_rules.grace_days cannot be negative", 400)

    return {
        "duration_days": duration,
        "lapse_policy": policy,
        "grace_days": grace,
    }


def _replace_plan_goals(plan_id, user_id, goal_ids):
    db = get_db()
    db.execute("DELETE FROM plan_goals WHERE plan_id = ?", (plan_id,))
    for i, goal_id in enumerate(goal_ids):
        goal = get_goal_or_404(goal_id, user_id)
        db.execute(
            "INSERT INTO plan_goals (plan_id, goal_id, position) VALUES (?, ?, ?)",
            (plan_id, goal["id"], i),
        )


@plans_bp.post("")
@require_auth
def create_plan():
    data = _body()
    name = (data.get("name") or "").strip() or "My plan"
    goal_ids = data.get("goal_ids") or []
    rules = validate_rules({**DEFAULT_DIFFICULTY_RULES, **(data.get("difficulty_rules") or {})})

    db = get_db()
    cur = db.execute(
        "INSERT INTO plans (user_id, name, difficulty_rules) VALUES (?, ?, ?)",
        (g.user["id"], name, json.dumps(rules)),
    )
    plan_id = cur.lastrowid
    _replace_plan_goals(plan_id, g.user["id"], goal_ids)
    db.execute(
        "INSERT INTO plan_cycles (plan_id, started_at) VALUES (?, ?)",
        (plan_id, utc_now_str()),
    )
    db.commit()
    plan = get_plan_or_404(plan_id, g.user["id"])
    return jsonify(plan_payload(plan, include_goals=True)), 201


@plans_bp.get("")
@require_auth
def list_plans():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM plans WHERE user_id = ? ORDER BY id DESC",
        (g.user["id"],),
    ).fetchall()
    plans = []
    for plan in rows:
        plan = sync_plan(plan)
        plans.append(plan_payload(plan))
    return jsonify({"plans": plans})


@plans_bp.get("/<int:plan_id>")
@require_auth
def get_plan(plan_id):
    plan = get_plan_or_404(plan_id, g.user["id"])
    plan = sync_plan(plan)
    return jsonify(plan_payload(plan, include_goals=True))


@plans_bp.patch("/<int:plan_id>")
@require_auth
def update_plan(plan_id):
    plan = get_plan_or_404(plan_id, g.user["id"])
    data = _body()

    name = data.get("name", plan["name"])
    rules = json.loads(plan["difficulty_rules"] or "{}")
    if "difficulty_rules" in data:
        rules = validate_rules({**DEFAULT_DIFFICULTY_RULES, **data["difficulty_rules"]})
    goal_ids = data.get("goal_ids")

    db = get_db()
    db.execute(
        "UPDATE plans SET name = ?, difficulty_rules = ? WHERE id = ?",
        ((name or "").strip() or plan["name"], json.dumps(rules), plan_id),
    )
    if goal_ids is not None:
        _replace_plan_goals(plan_id, g.user["id"], goal_ids)
    db.commit()
    plan = get_plan_or_404(plan_id, g.user["id"])
    return jsonify(plan_payload(plan, include_goals=True))


@plans_bp.delete("/<int:plan_id>")
@require_auth
def delete_plan(plan_id):
    get_plan_or_404(plan_id, g.user["id"])
    db = get_db()
    db.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
    db.commit()
    return jsonify({"ok": True})


@plans_bp.post("/<int:plan_id>/restart")
@require_auth
def restart_plan(plan_id):
    plan = get_plan_or_404(plan_id, g.user["id"])
    db = get_db()
    db.execute(
        "UPDATE plan_cycles SET ended_at = ?, outcome = 'restarted' "
        "WHERE plan_id = ? AND outcome = 'active'",
        (utc_now_str(), plan_id),
    )
    db.execute(
        "INSERT INTO plan_cycles (plan_id, started_at) VALUES (?, ?)",
        (plan_id, utc_now_str()),
    )
    db.execute("UPDATE plans SET status = 'active' WHERE id = ?", (plan_id,))
    db.commit()
    plan = get_plan_or_404(plan_id, g.user["id"])
    return jsonify(plan_payload(plan, include_goals=True))


@plans_bp.get("/<int:plan_id>/progress")
@require_auth
def get_progress(plan_id):
    plan = get_plan_or_404(plan_id, g.user["id"])
    return jsonify(compute_progress(plan))
