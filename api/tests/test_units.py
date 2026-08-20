import pytest

from app.units import convert


def test_no_unit_returns_amount():
    assert convert(16, None, "gallon") == 16
    assert convert(16, "", "gallon") == 16


def test_same_unit_identity():
    assert convert(1, "gallon", "Gallon") == 1
    assert convert(8, "oz", "oz") == 8


def test_fl_oz_to_gallon():
    assert abs(convert(16, "fl oz", "gallon") - 0.125) < 1e-9
    assert abs(convert(128, "fl oz", "gallon") - 1.0) < 1e-9


def test_cups_to_gallon():
    assert abs(convert(16, "cups", "gal") - 1.0) < 1e-9
    assert abs(convert(8, "cups", "gal") - 0.5) < 1e-9


def test_ml_to_liter():
    assert abs(convert(500, "ml", "liter") - 0.5) < 1e-9


def test_oz_ambiguous_resolves_by_goal_dimension():
    assert abs(convert(16, "oz", "gallon") - 0.125) < 1e-9
    assert abs(convert(16, "oz", "lb") - 1.0) < 1e-9
    assert abs(convert(8, "oz", "lb") - 0.5) < 1e-9


def test_weight_units():
    assert abs(convert(1, "lb", "oz") - 16) < 1e-9
    assert abs(convert(2.5, "kg", "g") - 2500) < 1e-9


def test_incompatible_units_rejected():
    with pytest.raises(ValueError):
        convert(1, "cup", "lb")


def test_unknown_unit_rejected():
    with pytest.raises(ValueError):
        convert(1, "widgets", "gallon")
    with pytest.raises(ValueError):
        convert(1, "g", "widgets")
