"""Unit tests for squat-specific weighted scoring."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scoring import calculate_weighted_score  # noqa: E402
from squat_analyzer import (  # noqa: E402
    EXCESSIVE_TORSO_LEAN,
    SquatAnalyzer,
    TORSO_LEAN_THRESHOLD,
)
from squat_scoring import (  # noqa: E402
    SQUAT_SCORE_COMPONENT_DEPTH,
    SQUAT_SCORE_COMPONENT_KNEE_CONTROL,
    SQUAT_SCORE_COMPONENT_REP_QUALITY,
    SQUAT_SCORE_COMPONENT_TORSO_POSTURE,
    SQUAT_SCORE_WEIGHTS,
    SquatRepScoreInput,
    calculate_squat_rep_components,
    calculate_squat_rep_score,
    calculate_squat_score,
    calculate_squat_score_from_history,
    score_depth_component,
    score_knee_control_component,
    score_rep_quality_component,
    score_torso_posture_component,
)


def _perfect_rep(**overrides: object) -> SquatRepScoreInput:
    base = dict(
        depth_score=100.0,
        depth_status="deep",
        min_knee_angle=90.0,
        min_hip_angle=95.0,
        max_torso_lean=12.0,
        valid=True,
        completed_full_cycle=True,
        errors=(),
        usable=True,
    )
    base.update(overrides)
    return SquatRepScoreInput(**base)  # type: ignore[arg-type]


def test_all_components_100_yield_final_100():
    components = {
        SQUAT_SCORE_COMPONENT_DEPTH: 100,
        SQUAT_SCORE_COMPONENT_KNEE_CONTROL: 100,
        SQUAT_SCORE_COMPONENT_TORSO_POSTURE: 100,
        SQUAT_SCORE_COMPONENT_REP_QUALITY: 100,
    }
    assert calculate_weighted_score(components, SQUAT_SCORE_WEIGHTS) == 100
    result = calculate_squat_score([_perfect_rep()])
    assert result.score == 100


def test_all_components_0_yield_final_0():
    components = {
        SQUAT_SCORE_COMPONENT_DEPTH: 0,
        SQUAT_SCORE_COMPONENT_KNEE_CONTROL: 0,
        SQUAT_SCORE_COMPONENT_TORSO_POSTURE: 0,
        SQUAT_SCORE_COMPONENT_REP_QUALITY: 0,
    }
    assert calculate_weighted_score(components, SQUAT_SCORE_WEIGHTS) == 0


def test_example_weighted_result_matches_shared_rounding():
    components = {
        SQUAT_SCORE_COMPONENT_DEPTH: 80,
        SQUAT_SCORE_COMPONENT_KNEE_CONTROL: 90,
        SQUAT_SCORE_COMPONENT_TORSO_POSTURE: 70,
        SQUAT_SCORE_COMPONENT_REP_QUALITY: 100,
    }
    # 80*0.35 + 90*0.25 + 70*0.20 + 100*0.20 = 84.5 → int(round(...))
    expected = calculate_weighted_score(components, SQUAT_SCORE_WEIGHTS)
    assert expected == 84
    assert sum(SQUAT_SCORE_WEIGHTS.values()) == pytest.approx(1.0)


def test_perfect_squat_rep_high_score():
    result = calculate_squat_score([_perfect_rep()])
    assert result.score >= 90
    assert result.components[SQUAT_SCORE_COMPONENT_DEPTH] >= 90
    assert result.components[SQUAT_SCORE_COMPONENT_KNEE_CONTROL] >= 90
    assert result.components[SQUAT_SCORE_COMPONENT_TORSO_POSTURE] >= 90
    assert result.components[SQUAT_SCORE_COMPONENT_REP_QUALITY] >= 90


def test_shallow_squat_lowers_depth_only():
    shallow = _perfect_rep(
        depth_score=20.0,
        depth_status="shallow",
        min_knee_angle=135.0,
        min_hip_angle=145.0,
        valid=False,
        completed_full_cycle=False,
        errors=("insufficient_depth", "squat_depth_reach"),
    )
    perfect_components = calculate_squat_rep_components(_perfect_rep())
    shallow_components = calculate_squat_rep_components(shallow)

    assert shallow_components[SQUAT_SCORE_COMPONENT_DEPTH] < 40
    assert (
        shallow_components[SQUAT_SCORE_COMPONENT_DEPTH]
        < perfect_components[SQUAT_SCORE_COMPONENT_DEPTH]
    )
    # Torso unchanged when lean is still good
    assert (
        shallow_components[SQUAT_SCORE_COMPONENT_TORSO_POSTURE]
        == perfect_components[SQUAT_SCORE_COMPONENT_TORSO_POSTURE]
    )


def test_poor_torso_posture_lowers_torso_score():
    good = score_torso_posture_component(_perfect_rep(max_torso_lean=10.0))
    poor = score_torso_posture_component(
        _perfect_rep(max_torso_lean=EXCESSIVE_TORSO_LEAN + 5.0, errors=("torso_lean",))
    )
    assert poor < good
    assert poor < 50


def test_poor_knee_control_lowers_knee_score():
    good = score_knee_control_component(_perfect_rep(min_knee_angle=90.0))
    poor = score_knee_control_component(
        _perfect_rep(
            min_knee_angle=40.0,
            errors=("too_deep_or_unstable", "too_fast"),
        )
    )
    assert poor < good
    assert poor < 50


def test_half_invalid_rep_lowers_rep_quality():
    good = score_rep_quality_component(_perfect_rep())
    half = score_rep_quality_component(
        _perfect_rep(
            valid=False,
            completed_full_cycle=False,
            depth_status="shallow",
            depth_score=25.0,
            errors=("incomplete_rep", "insufficient_depth"),
        )
    )
    assert half < good
    assert half < 50


def test_no_completed_rep_returns_zero():
    result = calculate_squat_score([])
    assert result.score == 0
    assert result.scored_rep_count == 0
    assert result.reason == "no_completed_reps"
    assert result.components == {
        SQUAT_SCORE_COMPONENT_DEPTH: 0.0,
        SQUAT_SCORE_COMPONENT_KNEE_CONTROL: 0.0,
        SQUAT_SCORE_COMPONENT_TORSO_POSTURE: 0.0,
        SQUAT_SCORE_COMPONENT_REP_QUALITY: 0.0,
    }
    assert calculate_squat_score_from_history(None).score == 0
    assert calculate_squat_score_from_history([]).score == 0


def test_multi_rep_aggregation_averages_components():
    high = _perfect_rep(depth_score=100.0)
    low = _perfect_rep(
        depth_score=0.0,
        depth_status="shallow",
        min_knee_angle=140.0,
        valid=False,
        completed_full_cycle=False,
        errors=("insufficient_depth",),
    )
    high_only = calculate_squat_score([high])
    both = calculate_squat_score([high, low])
    assert both.scored_rep_count == 2
    assert both.components[SQUAT_SCORE_COMPONENT_DEPTH] == pytest.approx(50.0)
    assert both.score < high_only.score


def test_low_visibility_not_treated_as_quality_input():
    visible = calculate_squat_score([_perfect_rep()])
    invisible = calculate_squat_score([_perfect_rep(usable=False)])
    from_map = calculate_squat_score(
        [
            {
                "depth_score": 100,
                "depth_status": "deep",
                "min_knee_angle": 90,
                "min_hip_angle": 95,
                "max_torso_lean": 10,
                "valid": True,
                "completed_full_cycle": True,
                "errors": [],
                "landmark_visibility_ok": False,
            }
        ]
    )
    assert invisible.score == 0
    assert invisible.reason == "no_usable_reps"
    assert from_map.score == 0
    assert visible.score >= 90


def test_score_always_within_0_100():
    samples = [
        _perfect_rep(),
        _perfect_rep(depth_score=150.0, min_knee_angle=20.0, max_torso_lean=80.0),
        _perfect_rep(
            depth_score=-10.0,
            valid=False,
            completed_full_cycle=False,
            errors=("too_fast", "torso_lean", "incomplete_rep"),
        ),
        _perfect_rep(usable=False),
    ]
    for sample in samples:
        result = calculate_squat_rep_score(sample)
        assert 0 <= result.score <= 100
        for value in result.components.values():
            assert 0.0 <= value <= 100.0
    video = calculate_squat_score(samples[:3])
    assert 0 <= video.score <= 100


def test_weights_match_spec():
    assert SQUAT_SCORE_WEIGHTS[SQUAT_SCORE_COMPONENT_DEPTH] == 0.35
    assert SQUAT_SCORE_WEIGHTS[SQUAT_SCORE_COMPONENT_KNEE_CONTROL] == 0.25
    assert SQUAT_SCORE_WEIGHTS[SQUAT_SCORE_COMPONENT_TORSO_POSTURE] == 0.20
    assert SQUAT_SCORE_WEIGHTS[SQUAT_SCORE_COMPONENT_REP_QUALITY] == 0.20


def test_depth_uses_existing_analyzer_depth_score():
    rep = _perfect_rep(depth_score=88.5, depth_status="deep")
    assert score_depth_component(rep) == pytest.approx(88.5)


def test_torso_threshold_alignment():
    below = score_torso_posture_component(
        _perfect_rep(max_torso_lean=TORSO_LEAN_THRESHOLD - 1.0)
    )
    above = score_torso_posture_component(
        _perfect_rep(max_torso_lean=TORSO_LEAN_THRESHOLD + 1.0)
    )
    assert below > above


def _metrics(knee: float, hip: float, torso: float = 15.0) -> dict:
    return {
        "left": knee,
        "right": knee,
        "average": knee,
        "avg_knee": knee,
        "left_hip": hip,
        "right_hip": hip,
        "avg_hip": hip,
        "selected_hip": hip,
        "torso_lean": torso,
        "selected_side": "right",
    }


def _hip_for_knee(angle: float) -> float:
    if angle >= 155:
        return angle
    if angle <= 90:
        return max(75.0, angle - 5.0)
    return min(angle + 12.0, 160.0)


def test_analyzer_rep_counter_unchanged_with_scoring_hook():
    a = SquatAnalyzer(fps=30)

    def _feed(angle: float, n: int, torso: float = 15.0) -> None:
        for _ in range(n):
            a.analyze_frame(
                _metrics(angle, _hip_for_knee(angle), torso),
                pose_confidence=0.9,
                torso_lean=torso,
                fps=30.0,
            )

    _feed(165, 10)
    _feed(125, 8)
    _feed(80, 10)
    _feed(120, 8)
    _feed(165, 10)
    a.finalize_session()

    assert a.rep_count >= 1
    assert a.valid_reps >= 1
    # Scoring is available and does not mutate counters
    before = (a.rep_count, a.valid_reps, a.invalid_reps)
    score = a.get_score_breakdown()
    after = (a.rep_count, a.valid_reps, a.invalid_reps)
    assert before == after
    assert 0 <= score["score"] <= 100
    assert "components" in score
    assert a.rep_history[0].get("max_torso_lean") is not None


def test_history_scoring_matches_direct_api():
    history = [
        {
            "depth_score": 100.0,
            "depth_status": "deep",
            "min_knee_angle": 88.0,
            "min_hip_angle": 92.0,
            "max_torso_lean": 15.0,
            "valid": True,
            "completed_full_cycle": True,
            "errors": [],
        }
    ]
    direct = calculate_squat_score(history)
    via = calculate_squat_score_from_history(history)
    assert direct.score == via.score
    assert direct.components == via.components
