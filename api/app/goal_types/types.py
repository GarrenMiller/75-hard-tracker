import json
from datetime import date, timedelta

from .base import GoalType
from ..errors import ApiError
from ..units import VOLUME_UNITS, WEIGHT_UNITS, convert
from ..util import date_from_timestamp


class DailyHabit(GoalType):
    key = "daily_habit"
    name = "Daily habit"
    description = "Complete the habit once per day."
    period = "day"
    config_schema = {"properties": {}, "required": []}

    def evaluate(self, config, check_ins, day):
        done = any(date_from_timestamp(c["completed_at"]) == day.isoformat() for c in check_ins)
        return {
            "completed": done,
            "period": "day",
            "period_end": day,
            "progress": 1 if done else 0,
            "detail": {},
        }


class DailyQuantity(GoalType):
    key = "daily_quantity"
    name = "Daily quantity"
    description = "Reach a target quantity each day (e.g. 1 gallon of water)."
    period = "day"
    config_schema = {
        "properties": {
            "target": {"type": "number", "title": "Target per day"},
            "unit": {"type": "string", "title": "Unit"},
        },
        "required": ["target", "unit"],
    }

    def to_dict(self):
        data = super().to_dict()
        data["units"] = {"volume": VOLUME_UNITS, "weight": WEIGHT_UNITS}
        return data

    def validate_config(self, config):
        config = super().validate_config(config)
        if config["target"] <= 0:
            raise ValueError("target must be greater than 0")
        return config

    def validate_check_in_value(self, config, value):
        amount = value.get("amount")
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise ValueError("Check-in value must include a numeric 'amount'")
        if amount <= 0:
            raise ValueError("amount must be greater than 0")
        unit = value.get("unit")
        if unit:
            try:
                amount = convert(amount, unit, config["unit"])
            except ValueError as e:
                raise ValueError(str(e))
        return {"amount": amount}

    def evaluate(self, config, check_ins, day):
        total = 0.0
        for c in check_ins:
            if date_from_timestamp(c["completed_at"]) == day.isoformat():
                try:
                    total += json.loads(c["value"] or "{}").get("amount", 0)
                except (ValueError, TypeError):
                    pass
        target = config["target"]
        return {
            "completed": total >= target,
            "period": "day",
            "period_end": day,
            "progress": min(1.0, total / target) if target else 0,
            "detail": {"current": total, "target": target, "unit": config["unit"]},
        }


class WeeklyFrequency(GoalType):
    key = "weekly_frequency"
    name = "Weekly frequency"
    description = "Complete the task N times per week."
    period = "week"
    config_schema = {
        "properties": {
            "times_per_week": {"type": "integer", "title": "Times per week"},
        },
        "required": ["times_per_week"],
    }

    def validate_config(self, config):
        config = super().validate_config(config)
        if config["times_per_week"] <= 0:
            raise ValueError("times_per_week must be greater than 0")
        return config

    def _week_start(self, day):
        return day - timedelta(days=day.weekday())

    def evaluate(self, config, check_ins, day):
        week_start = self._week_start(day)
        week_end = week_start + timedelta(days=6)
        start_iso = week_start.isoformat()
        end_iso = week_end.isoformat()
        count = 0
        for c in check_ins:
            cd = date_from_timestamp(c["completed_at"])
            if start_iso <= cd <= end_iso:
                count += 1
        target = config["times_per_week"]
        return {
            "completed": count >= target,
            "period": "week",
            "period_end": week_end,
            "progress": min(1.0, count / target) if target else 0,
            "detail": {"count": count, "times_per_week": target},
        }
