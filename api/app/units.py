"""Unit conversion for daily_quantity check-ins.

Check-in amounts may be entered in a different unit than the goal's target unit
(e.g. "16 fl oz" against a "1 gallon" goal). Amounts are converted to the goal's
unit before being stored.
"""

_VOLUME_TO_ML = {
    "ml": 1.0,
    "milliliter": 1.0,
    "milliliters": 1.0,
    "l": 1000.0,
    "liter": 1000.0,
    "liters": 1000.0,
    "fl oz": 29.5735295625,
    "fluid ounce": 29.5735295625,
    "fluid ounces": 29.5735295625,
    "cup": 236.5882365,
    "cups": 236.5882365,
    "pint": 473.176473,
    "pints": 473.176473,
    "pt": 473.176473,
    "quart": 946.352946,
    "quarts": 946.352946,
    "qt": 946.352946,
    "gallon": 3785.411784,
    "gallons": 3785.411784,
    "gal": 3785.411784,
}

_WEIGHT_TO_G = {
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,
    "kg": 1000.0,
    "kilogram": 1000.0,
    "kilograms": 1000.0,
    "oz": 28.349523125,
    "ounce": 28.349523125,
    "ounces": 28.349523125,
    "lb": 453.59237,
    "lbs": 453.59237,
    "pound": 453.59237,
    "pounds": 453.59237,
}

# "oz" is ambiguous (fluid ounce vs weight ounce). It is resolved by the goal's
# unit dimension; these aliases map to the fluid-ounce entry when needed.
_FLUID_ALIASES = {"oz", "oz.", "ounces"}

VOLUME_UNITS = ["ml", "l", "fl oz", "cup", "pint", "quart", "gallon"]
WEIGHT_UNITS = ["g", "kg", "oz", "lb"]


def _dimension(unit):
    if unit in _VOLUME_TO_ML:
        return "volume"
    if unit in _WEIGHT_TO_G:
        return "weight"
    return None


def _factor(unit, dimension):
    return _VOLUME_TO_ML[unit] if dimension == "volume" else _WEIGHT_TO_G[unit]


def convert(amount, from_unit, to_unit):
    """Convert amount from from_unit to to_unit. Returns amount unchanged when
    no unit is given. Raises ValueError for unknown or incompatible units."""
    if not from_unit:
        return amount
    from_unit = from_unit.strip().lower()
    to_unit = to_unit.strip().lower()
    if from_unit == to_unit:
        return amount

    to_dim = _dimension(to_unit)
    if to_dim is None:
        raise ValueError(f"Unsupported unit: {to_unit}")

    # Resolve the ambiguous "oz"/"ounces" alias against the goal's dimension.
    if from_unit in _FLUID_ALIASES:
        if to_dim == "weight":
            from_unit, from_dim = "oz", "weight"
        else:
            from_unit, from_dim = "fl oz", "volume"
    else:
        from_dim = _dimension(from_unit)
        if from_dim is None:
            raise ValueError(f"Unsupported unit: {from_unit}")

    if from_dim != to_dim:
        raise ValueError(f"Cannot convert {from_unit} to {to_unit}")
    return amount * (_factor(from_unit, from_dim) / _factor(to_unit, to_dim))
