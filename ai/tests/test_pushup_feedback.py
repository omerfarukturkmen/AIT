"""Tests for push-up form and incomplete-rep feedback generation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pushup_analyzer import (  # noqa: E402
    FORM_CONFIRMATION_FRAMES,
    FORM_MSG_BACK_BENT,
    FORM_MSG_COMPLETE_UP,
    FORM_MSG_GO_LOWER,
    FORM_MSG_HIPS_SAGGING,
    FORM_MSG_HIPS_TOO_HIGH,
    FORM_MSG_LOW_CONFIDENCE,
    PushupAnalyzer,
)


def _a(
    elbow: float,
    *,
    shoulder: float = 80.0,
    hip: float = 170.0,
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


def _hold(a: PushupAnalyzer, elbow: float, frames: int, **kwargs) -> None:
    for _ in range(frames):
        a.analyze_frame(_a(elbow, **kwargs))


def _enter_rep(a: PushupAnalyzer, **kwargs) -> None:
    _hold(a, 165, 6, **kwargs)
    _hold(a, 125, 8, **kwargs)


def _full_rep(a: PushupAnalyzer, **kwargs) -> None:
    _hold(a, 165, 6, **kwargs)
    _hold(a, 125, 8, **kwargs)
    _hold(a, 80, 8, **kwargs)
    _hold(a, 120, 8, **kwargs)
    _hold(a, 160, 8, **kwargs)


def test_hips_sagging_feedback_after_confirmation():
    a = PushupAnalyzer()
    _enter_rep(a, body_line_offset=0.09, body_alignment_angle=150)
    _hold(a, 120, FORM_CONFIRMATION_FRAMES, body_line_offset=0.09, body_alignment_angle=150)
    assert FORM_MSG_HIPS_SAGGING in a.feedback


def test_single_frame_sagging_no_feedback():
    a = PushupAnalyzer()
    _enter_rep(a, body_line_offset=0.01, body_alignment_angle=175)
    a.candidate_form_issues = set()
    a.candidate_form_frames = 0
    a.confirmed_form_issues = set()
    a.current_form_state = "unknown"
    a.analyze_frame(_a(120, body_line_offset=0.09, body_alignment_angle=150))
    assert FORM_MSG_HIPS_SAGGING not in a.feedback


def test_hips_too_high_feedback():
    a = PushupAnalyzer()
    _enter_rep(a, body_line_offset=-0.09, body_alignment_angle=150)
    _hold(a, 120, FORM_CONFIRMATION_FRAMES, body_line_offset=-0.09, body_alignment_angle=150)
    assert FORM_MSG_HIPS_TOO_HIGH in a.feedback


def test_back_bent_feedback():
    a = PushupAnalyzer()
    _enter_rep(a, body_line_offset=0.0, body_alignment_angle=150)
    _hold(a, 120, FORM_CONFIRMATION_FRAMES, body_line_offset=0.0, body_alignment_angle=150)
    assert FORM_MSG_BACK_BENT in a.feedback


def test_shallow_rep_feedback_on_incomplete_only():
    a = PushupAnalyzer()
    _hold(a, 165, 6)
    _hold(a, 125, 8)
    _hold(a, 122, 8)
    assert FORM_MSG_GO_LOWER not in a.feedback
    _hold(a, 160, 10)
    assert a.rep_count == 0
    assert FORM_MSG_GO_LOWER in a.feedback


def test_no_early_go_lower_during_descending():
    a = PushupAnalyzer()
    _hold(a, 165, 6)
    _hold(a, 140, 5)
    assert a.state == "descending"
    assert FORM_MSG_GO_LOWER not in a.feedback


def test_bottom_reached_incomplete_gets_complete_up_not_go_lower():
    a = PushupAnalyzer()
    _hold(a, 165, 6)
    _hold(a, 125, 8)
    _hold(a, 80, 8)
    a.finalize_session()
    result = a.get_result()
    assert FORM_MSG_COMPLETE_UP in result["feedback"]
    assert FORM_MSG_GO_LOWER not in result["feedback"]


def test_duplicate_sagging_message_once_in_final_summary():
    a = PushupAnalyzer()
    _enter_rep(a, body_line_offset=0.09, body_alignment_angle=150)
    _hold(a, 120, 15, body_line_offset=0.09, body_alignment_angle=150)
    result = a.get_result()
    assert result["feedback"].count(FORM_MSG_HIPS_SAGGING) == 1


def test_multiple_distinct_feedback_messages():
    a = PushupAnalyzer()
    _enter_rep(a, body_line_offset=0.09, body_alignment_angle=150)
    _hold(a, 120, FORM_CONFIRMATION_FRAMES, body_line_offset=0.09, body_alignment_angle=150)
    snap = a.analyze_frame(_a(120, body_line_offset=0.0, body_alignment_angle=150))
    _hold(a, 120, FORM_CONFIRMATION_FRAMES, body_line_offset=0.0, body_alignment_angle=150)
    assert FORM_MSG_HIPS_SAGGING in snap["feedback"] or FORM_MSG_HIPS_SAGGING in a.feedback
    assert FORM_MSG_BACK_BENT in a.feedback
    assert len(set(a.feedback) & {FORM_MSG_HIPS_SAGGING, FORM_MSG_BACK_BENT}) == 2


def test_low_confidence_no_form_feedback():
    a = PushupAnalyzer()
    _enter_rep(a, body_line_offset=0.09, body_alignment_angle=150)
    snap = a.analyze_frame(_a(120, body_line_offset=0.09, body_alignment_angle=150), pose_confidence=0.1)
    assert FORM_MSG_LOW_CONFIDENCE in snap["feedback"]
    assert FORM_MSG_HIPS_SAGGING not in snap["feedback"]


def test_metrics_incomplete_no_form_feedback():
    a = PushupAnalyzer()
    _enter_rep(a)
    snap = a.analyze_frame(_a(120, body_alignment_angle=None, body_line_offset=None))
    assert a.current_form_state == "metrics_incomplete"
    assert FORM_MSG_HIPS_SAGGING not in snap["feedback"]
    assert FORM_MSG_BACK_BENT not in snap["feedback"]


def test_valid_rep_with_form_error_still_valid():
    a = PushupAnalyzer()
    _full_rep(a, body_line_offset=0.09, body_alignment_angle=150)
    assert a.rep_count == 1
    assert a.valid_reps == 1
    assert FORM_MSG_HIPS_SAGGING in a.get_result()["feedback"]


def test_get_result_idempotent():
    a = PushupAnalyzer()
    _full_rep(a, body_line_offset=0.09, body_alignment_angle=150)
    r1 = a.get_result()
    r2 = a.get_result()
    assert r1["feedback"] == r2["feedback"]
    assert r1["form_errors"] == r2["form_errors"]
    assert r1["rep_count"] == r2["rep_count"]


def test_finalize_idempotent_no_duplicate_feedback():
    a = PushupAnalyzer()
    _hold(a, 165, 6)
    _hold(a, 125, 8)
    a.finalize_session()
    inv1 = a.invalid_reps
    not_low1 = a.form_errors["not_low_enough"]
    fb1 = list(a.feedback)
    a.finalize_session()
    assert a.invalid_reps == inv1
    assert a.form_errors["not_low_enough"] == not_low1
    r1 = a.get_result()
    r2 = a.get_result()
    assert r1["feedback"] == r2["feedback"]
    assert fb1.count(FORM_MSG_GO_LOWER) <= 1


def test_feedback_order_deterministic():
    def run_sequence() -> list[str]:
        a = PushupAnalyzer()
        _hold(a, 165, 6)
        _hold(a, 125, 8)
        _hold(a, 122, 8)
        _hold(a, 160, 10)
        _enter_rep(a, body_line_offset=0.09, body_alignment_angle=150)
        _hold(a, 120, FORM_CONFIRMATION_FRAMES, body_line_offset=0.09, body_alignment_angle=150)
        return a.get_result()["feedback"]

    assert run_sequence() == run_sequence()


def test_last_rep_feedback_present():
    a = PushupAnalyzer()
    _full_rep(a, body_line_offset=0.0, body_alignment_angle=150)
    result = a.get_result()
    assert "last_rep_feedback" in result
    assert FORM_MSG_BACK_BENT in result["last_rep_feedback"]
