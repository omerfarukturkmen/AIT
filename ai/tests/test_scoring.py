"""Unit tests for shared weighted scoring infrastructure."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scoring import (  # noqa: E402
    ScoreBreakdown,
    calculate_score_breakdown,
    calculate_weighted_score,
)


def test_all_perfect_scores_yield_100():
    score = calculate_weighted_score(
        {"A": 100, "B": 100},
        {"A": 0.5, "B": 0.5},
    )
    assert score == 100


def test_all_zero_scores_yield_0():
    score = calculate_weighted_score(
        {"A": 0, "B": 0},
        {"A": 0.5, "B": 0.5},
    )
    assert score == 0


def test_weighted_average_rounds_to_integer():
    score = calculate_weighted_score(
        {"A": 80, "B": 90},
        {"A": 0.6, "B": 0.4},
    )
    assert score == 84


def test_component_score_above_100_is_clamped():
    score = calculate_weighted_score(
        {"A": 150, "B": 100},
        {"A": 0.5, "B": 0.5},
    )
    assert score == 100


def test_component_score_below_0_is_clamped():
    score = calculate_weighted_score(
        {"A": -20, "B": 100},
        {"A": 0.5, "B": 0.5},
    )
    assert score == 50


def test_weight_sum_not_near_one_raises():
    with pytest.raises(ValueError, match="weights must sum"):
        calculate_weighted_score(
            {"A": 80, "B": 90},
            {"A": 0.5, "B": 0.3},
        )


def test_negative_weight_raises():
    with pytest.raises(ValueError, match="must be >= 0"):
        calculate_weighted_score(
            {"A": 80, "B": 90},
            {"A": 0.6, "B": -0.4},
        )


def test_mismatched_component_and_weight_keys_raise():
    with pytest.raises(ValueError, match="keys must match"):
        calculate_weighted_score(
            {"A": 80, "B": 90},
            {"A": 0.6, "C": 0.4},
        )


def test_empty_components_raise():
    with pytest.raises(ValueError, match="must not be empty"):
        calculate_weighted_score({}, {"A": 1.0})


def test_empty_weights_raise():
    with pytest.raises(ValueError, match="must not be empty"):
        calculate_weighted_score({"A": 80}, {})


def test_components_without_weights_raise():
    with pytest.raises(ValueError, match="keys must match"):
        calculate_weighted_score({"A": 80, "B": 90}, {"A": 1.0})


def test_weights_without_matching_components_raise():
    with pytest.raises(ValueError, match="keys must match"):
        calculate_weighted_score({"A": 80}, {"A": 0.5, "B": 0.5})


def test_all_zero_weights_raise():
    with pytest.raises(ValueError):
        calculate_weighted_score(
            {"A": 80, "B": 90},
            {"A": 0.0, "B": 0.0},
        )


def test_nan_component_score_raises():
    with pytest.raises(ValueError, match="finite"):
        calculate_weighted_score(
            {"A": math.nan, "B": 90},
            {"A": 0.5, "B": 0.5},
        )


def test_infinity_component_score_raises():
    with pytest.raises(ValueError, match="finite"):
        calculate_weighted_score(
            {"A": math.inf, "B": 90},
            {"A": 0.5, "B": 0.5},
        )


def test_nan_weight_raises():
    with pytest.raises(ValueError, match="finite"):
        calculate_weighted_score(
            {"A": 80, "B": 90},
            {"A": math.nan, "B": 0.5},
        )


def test_infinity_weight_raises():
    with pytest.raises(ValueError, match="finite"):
        calculate_weighted_score(
            {"A": 80, "B": 90},
            {"A": math.inf, "B": 0.0},
        )


def test_floating_point_weight_sum_tolerance():
    # 0.1 + 0.2 + 0.7 is not exactly 1.0 in binary float; must not raise.
    score = calculate_weighted_score(
        {"A": 100, "B": 80, "C": 60},
        {"A": 0.1, "B": 0.2, "C": 0.7},
    )
    # 0.1*100 + 0.2*80 + 0.7*60 = 68
    assert score == 68


def test_score_breakdown_model():
    result = calculate_score_breakdown(
        {"criterion_a": 80, "criterion_b": 90},
        {"criterion_a": 0.6, "criterion_b": 0.4},
    )
    assert isinstance(result, ScoreBreakdown)
    assert result.score == 84
    assert result.components == {"criterion_a": 80.0, "criterion_b": 90.0}
    assert result.as_dict() == {
        "score": 84,
        "components": {"criterion_a": 80.0, "criterion_b": 90.0},
    }


def test_breakdown_clamps_component_values_in_output():
    result = calculate_score_breakdown(
        {"A": 120, "B": -10},
        {"A": 0.5, "B": 0.5},
    )
    assert result.components == {"A": 100.0, "B": 0.0}
    assert result.score == 50
