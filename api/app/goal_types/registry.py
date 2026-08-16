from .base import GoalType
from .types import DailyHabit, DailyQuantity, WeeklyFrequency

_REGISTRY = {t.key: t() for t in (DailyHabit, DailyQuantity, WeeklyFrequency)}


def all_types():
    return list(_REGISTRY.values())


def get(key):
    return _REGISTRY.get(key)
