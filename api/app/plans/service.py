import json
from datetime import date, timedelta

from ..db import get_db
from ..errors import ApiError
from ..goal_types.registry import get as get_goal_type
from ..util import today_str, utc_now_str

DEFAULT_DIFFICULTY_RULES = {
    "duration_days": 75,
    "lapse_policy": "restart_on_fail",
    "grace_days": 0,
}


def get_plan_or_404(plan_id, user_id):
    db = get_db()
    row = db.execute(
        "SELECT * FROM plans WHERE id = ? AND user_id = ?", (plan_id, user_id)
    ).fetchone()
    if row is None:
        raise ApiError("Plan not found", 404)
    return row


def get_cycles(plan_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM plan_cycles WHERE plan_id = ? ORDER BY started_at", (plan_id,)
    ).fetchall()


def load_plan_goals(plan_id, user_id):
    db = get_db()
    return db.execute(
        "SELECT g.* FROM plan_goals pg JOIN goals g ON g.id = pg.goal_id "
        "WHERE pg.plan_id = ? AND g.user_id = ? ORDER BY pg.position",
        (plan_id, user_id),
    ).fetchall()


def plan_payload(plan, include_goals=False):
    from ..goals.service import goal_payload

    cycles = get_cycles(plan["id"])
    goals = load_plan_goals(plan["id"], plan["user_id"])
    payload = {
        "id": plan["id"],
        "name": plan["name"],
        "difficulty_rules": json.loads(plan["difficulty_rules"] or "{}"),
        "started_at": plan["started_at"],
        "status": plan["status"],
        "cycle_count": len(cycles),
        "goal_count": len(goals),
    }
    if include_goals:
        payload["goals"] = [goal_payload(g) for g in goals]
    return payload


def _parse_date(value):
    return date.fromisoformat(value[:10])


def _check_ins_for_goals(goals):
    db = get_db()
    result = {}
    for goal in goals:
        result[goal["id"]] = db.execute(
            "SELECT completed_at, value FROM check_ins WHERE goal_id = ?",
            (goal["id"],),
        ).fetchall()
    return result


def evaluate_cycle(cycle_start, goals, check_ins_by_goal, today):
    day_num = (today - cycle_start).days + 1
    days = []
    status_by_goal_date = {}
    for i in range(day_num):
        d = cycle_start + timedelta(days=i)
        statuses = {}
        for goal in goals:
            goal_type = get_goal_type(goal["goal_type_key"])
            if goal_type is None:
                continue
            config = json.loads(goal["config"] or "{}")
            status = goal_type.evaluate(config, check_ins_by_goal[goal["id"]], d)
            statuses[goal["id"]] = status
            status_by_goal_date[(goal["id"], d.isoformat())] = status
        days.append({"date": d.isoformat(), "statuses": statuses})

    missed_dates = set()
    for goal in goals:
        goal_type = get_goal_type(goal["goal_type_key"])
        for row in days:
            d = _parse_date(row["date"])
            if d >= today:
                continue
            status = row["statuses"][goal["id"]]
            if status["completed"]:
                continue
            if goal_type.period == "week":
                if status["period_end"] == d:
                    missed_dates.add(row["date"])
            else:
                missed_dates.add(row["date"])

    return {
        "days": days,
        "status_by_goal_date": status_by_goal_date,
        "missed_dates": missed_dates,
        "day_num": day_num,
    }


def sync_plan(plan, today=None):
    """Apply failure/restart logic to persist plan and cycle state."""
    if today is None:
        today = _parse_date(today_str())
    db = get_db()

    cycles = get_cycles(plan["id"])
    if not cycles:
        db.execute(
            "INSERT INTO plan_cycles (plan_id, started_at) VALUES (?, ?)",
            (plan["id"], utc_now_str()),
        )
        db.commit()
        cycles = get_cycles(plan["id"])

    active_cycles = [c for c in cycles if c["outcome"] == "active"]
    if not active_cycles:
        return get_plan_or_404(plan["id"], plan["user_id"])

    active_cycle = active_cycles[-1]
    rules = json.loads(plan["difficulty_rules"] or "{}")
    policy = rules.get("lapse_policy", "restart_on_fail")
    grace = rules.get("grace_days", 0)

    goals = load_plan_goals(plan["id"], plan["user_id"])
    result = evaluate_cycle(
        _parse_date(active_cycle["started_at"]),
        goals,
        _check_ins_for_goals(goals),
        today,
    )
    missed_count = len(result["missed_dates"])

    if policy == "restart_on_fail" and missed_count > 0:
        db.execute(
            "UPDATE plan_cycles SET ended_at = ?, outcome = 'failed' WHERE id = ?",
            (utc_now_str(), active_cycle["id"]),
        )
        db.execute(
            "INSERT INTO plan_cycles (plan_id, started_at) VALUES (?, ?)",
            (plan["id"], utc_now_str()),
        )
        db.execute("UPDATE plans SET status = 'active' WHERE id = ?", (plan["id"],))
        db.commit()
        return get_plan_or_404(plan["id"], plan["user_id"])

    if policy == "grace_days":
        if missed_count > grace:
            db.execute(
                "UPDATE plan_cycles SET ended_at = ?, outcome = 'failed' WHERE id = ?",
                (utc_now_str(), active_cycle["id"]),
            )
            db.execute("UPDATE plans SET status = 'failed' WHERE id = ?", (plan["id"],))
        elif missed_count > 0:
            db.execute("UPDATE plans SET status = 'in_grace' WHERE id = ?", (plan["id"],))
        else:
            db.execute("UPDATE plans SET status = 'active' WHERE id = ?", (plan["id"],))
        db.commit()
        return get_plan_or_404(plan["id"], plan["user_id"])

    return get_plan_or_404(plan["id"], plan["user_id"])


def compute_progress(plan, today=None):
    if today is None:
        today = _parse_date(today_str())

    plan = sync_plan(plan, today)
    db = get_db()
    cycles = get_cycles(plan["id"])
    active_cycles = [c for c in cycles if c["outcome"] == "active"]
    if not active_cycles:
        return {"plan": plan_payload(plan), "cycle": None, "days": [], "goals": []}
    active_cycle = active_cycles[-1]

    rules = json.loads(plan["difficulty_rules"] or "{}")
    duration = rules.get("duration_days", 75)
    goals = load_plan_goals(plan["id"], plan["user_id"])
    cycle_start = _parse_date(active_cycle["started_at"])
    result = evaluate_cycle(cycle_start, goals, _check_ins_for_goals(goals), today)

    day_summary = []
    today_iso = today.isoformat()
    for row in result["days"]:
        statuses = list(row["statuses"].values())
        if not statuses:
            continue
        all_done = all(s["completed"] for s in statuses)
        any_done = any(s["completed"] for s in statuses)
        if all_done:
            summary = "completed"
        elif any_done:
            summary = "partial"
        else:
            summary = "missed"
        if row["date"] == today_iso and summary == "missed":
            summary = "pending"
        day_summary.append({"date": row["date"], "status": summary})

    goal_details = []
    for goal in goals:
        from ..goals.service import goal_payload

        goal_type = get_goal_type(goal["goal_type_key"])
        today_status = result["status_by_goal_date"].get((goal["id"], today.isoformat()))
        goal_details.append(
            {
                "goal": goal_payload(goal),
                "today": today_status or {"completed": False, "progress": 0, "detail": {}},
                "streak": _compute_streak(result, goal["id"], cycle_start, today),
            }
        )

    return {
        "plan": plan_payload(plan),
        "cycle": {
            "id": active_cycle["id"],
            "started_at": active_cycle["started_at"],
            "day": result["day_num"],
            "total_days": duration,
            "missed_days": len(result["missed_dates"]),
        },
        "days": day_summary,
        "goals": goal_details,
    }


def _compute_streak(result, goal_id, cycle_start, today):
    d = today
    first = result["status_by_goal_date"].get((goal_id, d.isoformat()))
    if first is None or not first["completed"]:
        d = d - timedelta(days=1)
    streak = 0
    while d >= cycle_start:
        status = result["status_by_goal_date"].get((goal_id, d.isoformat()))
        if status is not None and status["completed"]:
            streak += 1
            d -= timedelta(days=1)
        else:
            break
    return streak
