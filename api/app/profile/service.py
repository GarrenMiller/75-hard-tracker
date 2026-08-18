import json
from datetime import date, timedelta

from ..db import get_db
from ..goal_types.registry import get as get_goal_type
from ..goals.service import goal_payload
from ..plans.service import plan_payload, sync_plan
from ..util import today_str


def _parse_date(value):
    return date.fromisoformat(value[:10])


def _user_payload(user):
    return {
        "id": user["id"],
        "email": user["email"],
        "display_name": user["display_name"],
        "created_at": user["created_at"],
    }


def _check_ins(goal_id):
    db = get_db()
    return db.execute(
        "SELECT completed_at, value FROM check_ins WHERE goal_id = ?", (goal_id,)
    ).fetchall()


def _current_streak(goal_row, today):
    """All-time current streak: consecutive completed days ending today (or
    yesterday if today is not yet done). Only meaningful for day-period goals."""
    goal_type = get_goal_type(goal_row["goal_type_key"])
    if goal_type is None or goal_type.period != "day":
        return 0
    config = json.loads(goal_row["config"] or "{}")
    check_ins = _check_ins(goal_row["id"])
    if not check_ins:
        return 0

    db = get_db()
    earliest = _parse_date(
        db.execute(
            "SELECT MIN(completed_at) FROM check_ins WHERE goal_id = ?",
            (goal_row["id"],),
        ).fetchone()[0]
    )

    d = today
    if not goal_type.evaluate(config, check_ins, d)["completed"]:
        d -= timedelta(days=1)

    streak = 0
    while d >= earliest and goal_type.evaluate(config, check_ins, d)["completed"]:
        streak += 1
        d -= timedelta(days=1)
    return streak


def build_profile(user, today=None):
    if today is None:
        today = _parse_date(today_str())
    db = get_db()
    user_id = user["id"]

    goals = db.execute(
        "SELECT * FROM goals WHERE user_id = ? ORDER BY active DESC, created_at DESC",
        (user_id,),
    ).fetchall()
    plans = db.execute(
        "SELECT * FROM plans WHERE user_id = ? ORDER BY id DESC", (user_id,)
    ).fetchall()
    synced_plans = [sync_plan(p, today) for p in plans]
    status_by_id = {p["id"]: p["status"] for p in synced_plans}

    goal_stats = []
    total_check_ins = 0
    best_streak = 0
    for g in goals:
        completions = db.execute(
            "SELECT COUNT(*) FROM check_ins WHERE goal_id = ?", (g["id"],)
        ).fetchone()[0]
        last = db.execute(
            "SELECT MAX(completed_at) FROM check_ins WHERE goal_id = ?", (g["id"],)
        ).fetchone()[0]
        streak = _current_streak(g, today)
        total_check_ins += completions
        best_streak = max(best_streak, streak)
        member_plans = db.execute(
            "SELECT p.id, p.name FROM plan_goals pg JOIN plans p ON p.id = pg.plan_id "
            "WHERE pg.goal_id = ? ORDER BY p.id",
            (g["id"],),
        ).fetchall()
        goal_stats.append(
            {
                "goal": goal_payload(g, include_today=True),
                "streak": streak,
                "total_completions": completions,
                "last_completed_at": last,
                "plans": [
                    {
                        "id": p["id"],
                        "name": p["name"],
                        "status": status_by_id.get(p["id"], "active"),
                    }
                    for p in member_plans
                ],
            }
        )

    plan_stats = []
    plans_active = 0
    plans_failed = 0
    for p in synced_plans:
        payload = plan_payload(p, today=today)
        if p["status"] in ("active", "in_grace"):
            plans_active += 1
        elif p["status"] == "failed":
            plans_failed += 1
        plan_stats.append(
            {
                "plan": payload,
                "cycle_day": payload["cycle_day"],
                "cycle_total_days": payload["cycle_total_days"],
            }
        )

    stats = {
        "goals_total": len(goals),
        "goals_active": sum(1 for g in goals if g["active"]),
        "plans_total": len(plans),
        "plans_active": plans_active,
        "plans_failed": plans_failed,
        "check_ins_total": total_check_ins,
        "best_streak": best_streak,
        "member_days": (today - _parse_date(user["created_at"])).days,
    }

    return {
        "user": _user_payload(user),
        "stats": stats,
        "goals": goal_stats,
        "plans": plan_stats,
    }
