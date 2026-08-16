import json

from ..db import get_db
from ..errors import ApiError
from ..goal_types.registry import get as get_goal_type
from ..util import today_str


def get_goal_or_404(goal_id, user_id):
    db = get_db()
    row = db.execute(
        "SELECT * FROM goals WHERE id = ? AND user_id = ?", (goal_id, user_id)
    ).fetchone()
    if row is None:
        raise ApiError("Goal not found", 404)
    return row


def goal_payload(row, include_today=False):
    goal_type = get_goal_type(row["goal_type_key"])
    config = json.loads(row["config"] or "{}")
    payload = {
        "id": row["id"],
        "name": row["name"],
        "goal_type_key": row["goal_type_key"],
        "goal_type_name": goal_type.name if goal_type else row["goal_type_key"],
        "period": goal_type.period if goal_type else "day",
        "config": config,
        "active": bool(row["active"]),
        "created_at": row["created_at"],
    }
    if include_today:
        payload["today"] = today_status(row, goal_type, config)
    return payload


def today_status(row, goal_type, config):
    if goal_type is None:
        return {"completed": False, "detail": {}}
    db = get_db()
    check_ins = db.execute(
        "SELECT completed_at, value FROM check_ins WHERE goal_id = ?",
        (row["id"],),
    ).fetchall()
    from datetime import date as _date

    today = _date.fromisoformat(today_str())
    return goal_type.evaluate(config, check_ins, today)


def list_check_ins(goal_id, user_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM check_ins WHERE goal_id = ? AND user_id = ? ORDER BY completed_at DESC",
        (goal_id, user_id),
    ).fetchall()


def check_in_payload(row):
    value = json.loads(row["value"] or "{}") if row["value"] else {}
    return {
        "id": row["id"],
        "goal_id": row["goal_id"],
        "plan_id": row["plan_id"],
        "completed_at": row["completed_at"],
        "value": value,
    }
