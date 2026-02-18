import pytest
from fantas import (
    FormulaCurve,
    CURVE_LINEAR,
    CURVE_FASTER,
    CURVE_SLOWER,
    CURVE_SMOOTH,
    get_time_ns,
)

test_data = (
    (CURVE_LINEAR, [(0, 0), (0.5, 0.5), (1, 1)]),
    (CURVE_FASTER, [(0, 0), (0.5, 0.25), (1, 1)]),
    (CURVE_SLOWER, [(0, 0), (0.5, 0.75), (1, 1)]),
)


@pytest.mark.parametrize("curve, points", test_data)
def test_predefined_curves(curve, points):
    for x, expected_y in points:
        assert curve(x) == pytest.approx(expected_y)


def test_curve_smooth():
    assert CURVE_SMOOTH(0) == pytest.approx(0)
    assert CURVE_SMOOTH(0.25) < 0.25
    assert CURVE_SMOOTH(0.5) == pytest.approx(0.5)
    assert CURVE_SMOOTH(0.75) > 0.75
    assert CURVE_SMOOTH(1) == pytest.approx(1)


test_data_formula = (
    ("x**2", [(0, 0), (0.5, 0.25), (1, 1)]),
    ("math.sqrt(x)", [(0, 0), (0.25, 0.5), (1, 1)]),
    ("x**2 + 2*x + 1", [(0, 1), (0.5, 2.25), (1, 4)]),
)


@pytest.mark.parametrize("formula, points", test_data_formula)
def test_formula_curve(formula, points):
    curve = FormulaCurve(formula)
    for x, expected_y in points:
        assert curve(x) == pytest.approx(expected_y)


def test_formula_curve_cache():
    formula = " + ".join(
        f"tan(cos(sin(math.log(math.sqrt(({i+1} * pi / 1000) ** 2)))))"
        for i in range(1000)
    )
    curve = FormulaCurve(formula)

    start_time = get_time_ns()
    result1 = curve(0)
    time1 = get_time_ns() - start_time

    start_time = get_time_ns()
    result2 = curve(0)
    time2 = get_time_ns() - start_time

    assert result1 == result2
    assert time2 < time1 / 100
