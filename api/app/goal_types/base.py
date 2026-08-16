from abc import ABC, abstractmethod


class GoalType(ABC):
    key: str = ""
    name: str = ""
    description: str = ""
    period: str = "day"
    config_schema: dict = {"properties": {}, "required": []}

    def to_dict(self):
        return {
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "period": self.period,
            "config_schema": self.config_schema,
        }

    def validate_config(self, config):
        props = self.config_schema.get("properties", {})
        required = self.config_schema.get("required", [])
        for field in required:
            if field not in config or config[field] in (None, ""):
                raise ValueError(f"Missing required config field: {field}")
        for field, value in config.items():
            if field not in props:
                raise ValueError(f"Unknown config field: {field}")
            expected = props[field].get("type")
            if expected == "number" and isinstance(value, bool):
                raise ValueError(f"Config field {field} must be a number")
            if expected == "number" and not isinstance(value, (int, float)):
                raise ValueError(f"Config field {field} must be a number")
            if expected == "integer" and (not isinstance(value, int) or isinstance(value, bool)):
                raise ValueError(f"Config field {field} must be an integer")
            if expected == "string" and not isinstance(value, str):
                raise ValueError(f"Config field {field} must be a string")
        return dict(config)

    def validate_check_in_value(self, config, value):
        return value or {}

    @abstractmethod
    def evaluate(self, config, check_ins, date):
        """Return a status dict for the given goal on the given date.

        check_ins is a list of rows with keys completed_at and value.
        date is a datetime.date. Status keys: completed (bool), period,
        period_end (datetime.date), progress (float 0..1), detail (dict).
        """
        raise NotImplementedError
