"""Tests for push-up rep state machine hardening."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pushup_analyzer import (  # noqa: E402
    FORM_MSG_GO_LOWER,
    PushupAnalyzer,
)


def _a(elbow: float, **kwargs) -> dict:
    base = {
        "avg_elbow": elbow,
        "avg_shoulder": 80.0,
        "avg_hip": 170.0,
        "body_alignment_angle": 175.0,
        "body_line_offset": 0.01,
        "alignment_side": "left",
    }
    base.update(kwargs)
    return base


def _hold(analyzer: PushupAnalyzer, elbow: float, frames: int, **kwargs) -> None:
    for _ in range(frames):
        analyzer.analyze_frame(_a(elbow, **kwargs))


def _full_rep(analyzer: PushupAnalyzer, **kwargs) -> None:
    _hold(analyzer, 165, 6, **kwargs)
    _hold(analyzer, 125, 8, **kwargs)
    _hold(analyzer, 80, 8, **kwargs)
    _hold(analyzer, 120, 8, **kwargs)
    _hold(analyzer, 160, 8, **kwargs)


def test_small_arm_bend_no_rep():
    a = PushupAnalyzer()
    _hold(a, 165, 6)
    for value in [160, 155, 160, 165]:
        a.analyze_frame(_a(value))
    assert a.rep_count == 0
    assert a.valid_reps == 0
    assert a.rep_in_progress is False


def test_single_frame_bottom_spike_no_rep():
    a = PushupAnalyzer()
    for value in [165, 165, 165, 85, 165, 165, 165]:
        a.analyze_frame(_a(value))
    assert a.rep_count == 0
    assert a.reached_bottom is False
    assert a.state != "bottom"


def test_descent_threshold_jitter_no_rep():
    a = PushupAnalyzer()
    _hold(a, 165, 6)
    for value in [150, 146, 144, 147, 143, 146, 148, 155]:
        a.analyze_frame(_a(value))
    assert a.rep_count == 0
    assert a.valid_reps == 0


def test_shallow_push_up_invalid_not_valid():
    a = PushupAnalyzer()
    _hold(a, 165, 6)
    _hold(a, 125, 8)
    _hold(a, 122, 8)
    _hold(a, 160, 10)
    assert a.rep_count == 0
    assert a.valid_reps == 0
    assert a.invalid_reps == 1
    assert a.form_errors["not_low_enough"] == 1
    assert any(FORM_MSG_GO_LOWER in m for m in a.feedback)


def test_full_valid_push_up():
    a = PushupAnalyzer()
    _full_rep(a)
    assert a.rep_count == 1
    assert a.valid_reps == 1
    assert a.invalid_reps == 0


def test_two_valid_push_ups():
    a = PushupAnalyzer()
    _full_rep(a)
    _full_rep(a)
    assert a.rep_count == 2
    assert a.valid_reps == 2


def test_bottom_bounce_single_rep():
    a = PushupAnalyzer()
    _hold(a, 165, 6)
    _hold(a, 125, 8)
    _hold(a, 80, 8)
    _hold(a, 115, 6)
    _hold(a, 85, 6)
    _hold(a, 120, 8)
    _hold(a, 160, 8)
    assert a.rep_count == 1
    assert a.valid_reps == 1


def test_no_full_return_to_up_at_most_one_rep():
    a = PushupAnalyzer()
    _hold(a, 165, 6)
    _hold(a, 125, 8)
    _hold(a, 80, 8)
    _hold(a, 115, 6)
    _hold(a, 125, 6)
    _hold(a, 85, 6)
    _hold(a, 120, 8)
    _hold(a, 160, 8)
    assert a.rep_count == 1
    assert a.valid_reps == 1


def test_mid_video_start_no_rep_then_one_after_full_cycle():
    a = PushupAnalyzer()
    _hold(a, 80, 8)
    _hold(a, 120, 8)
    _hold(a, 160, 8)
    assert a.rep_count == 0
    assert a.has_seen_valid_up is True
    _full_rep(a)
    assert a.rep_count == 1
    assert a.valid_reps == 1


def test_low_confidence_during_valid_rep_still_completes():
    a = PushupAnalyzer()
    _hold(a, 165, 6)
    _hold(a, 125, 8)
    for _ in range(4):
        a.analyze_frame(_a(80), pose_confidence=0.1)
    _hold(a, 80, 4)
    _hold(a, 120, 8)
    _hold(a, 160, 8)
    assert a.rep_count == 1
    assert a.valid_reps == 1


def test_none_angle_during_rep_no_crash_no_false_complete():
    a = PushupAnalyzer()
    _hold(a, 165, 6)
    _hold(a, 125, 8)
    for _ in range(4):
        a.analyze_frame({"avg_elbow": None, "avg_shoulder": 80, "avg_hip": 170})
    assert a.rep_in_progress is True
    assert a.rep_count == 0
    _hold(a, 80, 8)
    _hold(a, 120, 8)
    _hold(a, 160, 8)
    assert a.rep_count == 1


def test_long_up_hold_no_double_count():
    a = PushupAnalyzer()
    _full_rep(a)
    _hold(a, 165, 20)
    assert a.rep_count == 1
    assert a.valid_reps == 1


def test_finalize_incomplete_idempotent():
    a = PushupAnalyzer()
    _hold(a, 165, 6)
    _hold(a, 125, 8)
    _hold(a, 80, 8)
    a.finalize_session()
    first_invalid = a.invalid_reps
    a.finalize_session()
    assert a.rep_count == 0
    assert a.valid_reps == 0
    assert a.invalid_reps == first_invalid == 1


def test_get_result_idempotent_after_state_hardening():
    a = PushupAnalyzer()
    _full_rep(a)
    r1 = a.get_result()
    r2 = a.get_result()
    assert r1["rep_count"] == r2["rep_count"] == 1
    assert r1["valid_reps"] == r2["valid_reps"] == 1
    assert r1["form_errors"] == r2["form_errors"]


def test_snapshot_includes_state_guard_fields():
    a = PushupAnalyzer()
    snap = a.analyze_frame(_a(165))
    for key in (
        "has_seen_valid_up",
        "rep_counted",
        "candidate_state",
        "candidate_state_frames",
        "rep_start_elbow_angle",
    ):
        assert key in snap
