"""Unit tests for push-up-specific weighted scoring."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scoring import calculate_weighted_score  # noqa: E402
from pushup_analyzer import (  # noqa: E402
    BOTTOM_POSITION_ANGLE,
    HIP_SAG_OFFSET_THRESHOLD,
    PushupAnalyzer,
)
from pushup_scoring import (  # noqa: E402
    PUSHUP_SCORE_COMPONENT_BODY_ALIGNMENT,
    PUSHUP_SCORE_COMPONENT_ELBOW_ANGLE,
    PUSHUP_SCORE_COMPONENT_REP_DEPTH,
    PUSHUP_SCORE_COMPONENT_TEMPO_CONTROL,
    PUSHUP_SCORE_WEIGHTS,
    PushupRepScoreInput,
    calculate_pushup_rep_components,
    calculate_pushup_rep_score,
    calculate_pushup_score,
    calculate_pushup_score_from_history,
    score_body_alignment_component,
    score_elbow_angle_component,
    score_rep_depth_component,
    score_tempo_control_component,
)


def _perfect_rep(**overrides: object) -> PushupRepScoreInput:
    base = dict(
        min_elbow_angle=80.0,
        rep_start_elbow_angle=165.0,
        reached_bottom=True,
        valid=True,
        completed_full_cycle=True,
        form_issues=(),
        errors=(),
        duration_frames=36,
        max_abs_body_line_offset=0.01,
        min_body_alignment_angle=175.0,
        usable=True,
    )
    base.update(overrides)
    return PushupRepScoreInput(**base)  # type: ignore[arg-type]


def _a(
    elbow: float,
    shoulder: float = 80.0,
    hip: float = 170.0,
    *,
    body_alignment_angle: float | None = 175.0,
    body_line_offset: float | None = 0.01,
) -> dict:
    return {
        "avg_elbow": elbow,
        "avg_shoulder": shoulder,
        "avg_hip": hip,
        "body_alignment_angle": body_alignment_angle,
        "body_line_offset": body_line_offset,
        "alignment_side": "left",
    }


def _hold(analyzer: PushupAnalyzer, elbow: float, frames: int, **form_kwargs) -> None:
    for _ in range(frames):
        analyzer.analyze_frame(_a(elbow, **form_kwargs))


def _full_rep(analyzer: PushupAnalyzer, **form_kwargs) -> None:
    _hold(analyzer, 165, 6, **form_kwargs)
    _hold(analyzer, 125, 8, **form_kwargs)
    _hold(analyzer, 80, 8, **form_kwargs)
    _hold(analyzer, 120, 8, **form_kwargs)
    _hold(analyzer, 160, 8, **form_kwargs)


def test_all_components_100_yield_final_100():
    components = {
        PUSHUP_SCORE_COMPONENT_ELBOW_ANGLE: 100,
        PUSHUP_SCORE_COMPONENT_BODY_ALIGNMENT: 100,
        PUSHUP_SCORE_COMPONENT_REP_DEPTH: 100,
        PUSHUP_SCORE_COMPONENT_TEMPO_CONTROL: 100,
    }
    assert calculate_weighted_score(components, PUSHUP_SCORE_WEIGHTS) == 100
    result = calculate_pushup_score([_perfect_rep()])
    assert result.score == 100


def test_all_components_0_yield_final_0():
    components = {
        PUSHUP_SCORE_COMPONENT_ELBOW_ANGLE: 0,
        PUSHUP_SCORE_COMPONENT_BODY_ALIGNMENT: 0,
        PUSHUP_SCORE_COMPONENT_REP_DEPTH: 0,
        PUSHUP_SCORE_COMPONENT_TEMPO_CONTROL: 0,
    }
    assert calculate_weighted_score(components, PUSHUP_SCORE_WEIGHTS) == 0


def test_example_weighted_result_matches_shared_rounding():
    components = {
        PUSHUP_SCORE_COMPONENT_ELBOW_ANGLE: 80,
        PUSHUP_SCORE_COMPONENT_BODY_ALIGNMENT: 90,
        PUSHUP_SCORE_COMPONENT_REP_DEPTH: 70,
        PUSHUP_SCORE_COMPONENT_TEMPO_CONTROL: 100,
    }
    # 80*0.30 + 90*0.30 + 70*0.25 + 100*0.15 = 83.5
    expected = calculate_weighted_score(components, PUSHUP_SCORE_WEIGHTS)
    assert expected == 84
    assert sum(PUSHUP_SCORE_WEIGHTS.values()) == pytest.approx(1.0)


def test_perfect_pushup_high_score():
    result = calculate_pushup_score([_perfect_rep()])
    assert result.score >= 90
    for key in PUSHUP_SCORE_WEIGHTS:
        assert result.components[key] >= 90


def test_insufficient_elbow_flexion_lowers_elbow_score():
    deep = score_elbow_angle_component(_perfect_rep(min_elbow_angle=80.0))
    shallow = score_elbow_angle_component(_perfect_rep(min_elbow_angle=130.0))
    assert shallow < deep
    assert shallow < 50


def test_hip_sag_lowers_body_alignment():
    good = score_body_alignment_component(_perfect_rep())
    poor = score_body_alignment_component(
        _perfect_rep(
            form_issues=("hips_sagging",),
            max_abs_body_line_offset=HIP_SAG_OFFSET_THRESHOLD + 0.04,
        )
    )
    assert poor < good
    assert poor < 70


def test_half_rep_lowers_rep_depth():
    full = score_rep_depth_component(_perfect_rep())
    half = score_rep_depth_component(
        _perfect_rep(
            reached_bottom=False,
            valid=False,
            completed_full_cycle=False,
            min_elbow_angle=120.0,
            errors=("not_low_enough",),
        )
    )
    assert half < full
    assert half < 40


def test_controlled_full_rep_high_rep_depth():
    score = score_rep_depth_component(
        _perfect_rep(
            reached_bottom=True,
            valid=True,
            min_elbow_angle=BOTTOM_POSITION_ANGLE - 5.0,
        )
    )
    assert score >= 90


def test_very_short_transition_low_tempo():
    short = score_tempo_control_component(_perfect_rep(duration_frames=4))
    controlled = score_tempo_control_component(_perfect_rep(duration_frames=36))
    assert short < controlled
    assert short < 40


def test_multiple_balanced_reps_stable_tempo():
    reps = [
        _perfect_rep(duration_frames=34),
        _perfect_rep(duration_frames=36),
        _perfect_rep(duration_frames=35),
    ]
    result = calculate_pushup_score(reps)
    assert result.components[PUSHUP_SCORE_COMPONENT_TEMPO_CONTROL] >= 90
    assert result.scored_rep_count == 3


def test_highly_variable_tempo_lowers_tempo_score():
    balanced = calculate_pushup_score(
        [_perfect_rep(duration_frames=34), _perfect_rep(duration_frames=36)]
    )
    variable = calculate_pushup_score(
        [_perfect_rep(duration_frames=12), _perfect_rep(duration_frames=60)]
    )
    assert (
        variable.components[PUSHUP_SCORE_COMPONENT_TEMPO_CONTROL]
        < balanced.components[PUSHUP_SCORE_COMPONENT_TEMPO_CONTROL]
    )


def test_single_rep_tempo_is_deterministic():
    rep = _perfect_rep(duration_frames=30)
    a = calculate_pushup_score([rep])
    b = calculate_pushup_score([rep])
    assert a.score == b.score
    assert a.components == b.components
    assert a.components[PUSHUP_SCORE_COMPONENT_TEMPO_CONTROL] >= 70


def test_no_completed_rep_returns_zero():
    result = calculate_pushup_score([])
    assert result.score == 0
    assert result.scored_rep_count == 0
    assert result.reason == "no_completed_reps"
    assert calculate_pushup_score_from_history(None).score == 0
    assert calculate_pushup_score_from_history([]).score == 0


def test_low_visibility_not_scored_as_quality():
    visible = calculate_pushup_score([_perfect_rep()])
    blocked = calculate_pushup_score([_perfect_rep(usable=False)])
    from_map = calculate_pushup_score(
        [
            {
                "min_elbow_angle": 80,
                "reached_bottom": True,
                "valid": True,
                "completed_full_cycle": True,
                "duration_frames": 36,
                "form_issues": [],
                "errors": [],
                "landmark_visibility_ok": False,
            }
        ]
    )
    assert blocked.score == 0
    assert blocked.reason == "no_usable_reps"
    assert from_map.score == 0
    assert visible.score >= 90


def test_score_always_within_0_100():
    samples = [
        _perfect_rep(),
        _perfect_rep(min_elbow_angle=20.0, duration_frames=2, form_issues=("hips_sagging", "back_bent")),
        _perfect_rep(
            reached_bottom=False,
            valid=False,
            completed_full_cycle=False,
            errors=("not_low_enough",),
            duration_frames=5,
        ),
        _perfect_rep(usable=False),
    ]
    for sample in samples:
        result = calculate_pushup_rep_score(sample)
        assert 0 <= result.score <= 100
        for value in result.components.values():
            assert 0.0 <= value <= 100.0
    video = calculate_pushup_score(samples[:3])
    assert 0 <= video.score <= 100


def test_weights_match_spec():
    assert PUSHUP_SCORE_WEIGHTS[PUSHUP_SCORE_COMPONENT_ELBOW_ANGLE] == 0.30
    assert PUSHUP_SCORE_WEIGHTS[PUSHUP_SCORE_COMPONENT_BODY_ALIGNMENT] == 0.30
    assert PUSHUP_SCORE_WEIGHTS[PUSHUP_SCORE_COMPONENT_REP_DEPTH] == 0.25
    assert PUSHUP_SCORE_WEIGHTS[PUSHUP_SCORE_COMPONENT_TEMPO_CONTROL] == 0.15


def test_analyzer_rep_counter_unchanged_with_scoring_hook():
    analyzer = PushupAnalyzer()
    _full_rep(analyzer)
    analyzer.finalize_session()
    assert analyzer.rep_count == 1
    assert analyzer.valid_reps == 1
    before = (analyzer.rep_count, analyzer.valid_reps, analyzer.invalid_reps)
    score = analyzer.get_score_breakdown()
    after = (analyzer.rep_count, analyzer.valid_reps, analyzer.invalid_reps)
    assert before == after
    assert 0 <= score["score"] <= 100
    assert "components" in score
    assert len(analyzer.rep_history) == 1
    assert analyzer.rep_history[0]["valid"] is True
    assert analyzer.rep_history[0]["duration_frames"] >= 12


def test_analyzer_half_rep_recorded_for_scoring_without_counting_valid():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 6)
    _hold(analyzer, 125, 8)  # descending
    _hold(analyzer, 160, 8)  # back up without bottom
    analyzer.finalize_session()
    assert analyzer.rep_count == 0
    assert analyzer.invalid_reps >= 1
    assert len(analyzer.rep_history) >= 1
    half = analyzer.rep_history[0]
    assert half["valid"] is False
    assert half["reached_bottom"] is False
    depth = score_rep_depth_component(PushupRepScoreInput.from_mapping(half))
    assert depth < 40


def test_history_scoring_matches_direct_api():
    history = [
        {
            "min_elbow_angle": 80.0,
            "reached_bottom": True,
            "valid": True,
            "completed_full_cycle": True,
            "duration_frames": 36,
            "form_issues": [],
            "errors": [],
            "max_abs_body_line_offset": 0.01,
            "min_body_alignment_angle": 175.0,
        }
    ]
    direct = calculate_pushup_score(history)
    via = calculate_pushup_score_from_history(history)
    assert direct.score == via.score
    assert direct.components == via.components
