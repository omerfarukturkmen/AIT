"""Unit tests for successful / failed / total rep summary."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pushup_analyzer import PushupAnalyzer  # noqa: E402
from rep_summary import RepSummary, summarize_rep_counters, summarize_rep_history  # noqa: E402
from squat_analyzer import SquatAnalyzer  # noqa: E402


def test_no_reps_all_zero():
    summary = summarize_rep_history([])
    assert summary.as_dict() == {
        "successful_reps": 0,
        "failed_reps": 0,
        "total_reps": 0,
    }
    assert summarize_rep_history(None).total_reps == 0


def test_one_valid_rep():
    summary = summarize_rep_history([{"valid": True}])
    assert summary.successful_reps == 1
    assert summary.failed_reps == 0
    assert summary.total_reps == 1


def test_one_failed_rep():
    summary = summarize_rep_history([{"valid": False}])
    assert summary.successful_reps == 0
    assert summary.failed_reps == 1
    assert summary.total_reps == 1


def test_two_valid_reps():
    summary = summarize_rep_history([{"valid": True}, {"valid": True}])
    assert summary.as_dict() == {
        "successful_reps": 2,
        "failed_reps": 0,
        "total_reps": 2,
    }


def test_one_valid_one_failed():
    summary = summarize_rep_history([{"valid": True}, {"valid": False}])
    assert summary.successful_reps == 1
    assert summary.failed_reps == 1
    assert summary.total_reps == 2


def test_three_valid_two_failed():
    history = (
        [{"valid": True}] * 3
        + [{"valid": False}] * 2
    )
    summary = summarize_rep_history(history)
    assert summary.successful_reps == 3
    assert summary.failed_reps == 2
    assert summary.total_reps == 5


def test_total_invariant():
    for history in (
        [],
        [{"valid": True}],
        [{"valid": False}, {"valid": True}, {"valid": False}],
    ):
        summary = summarize_rep_history(history)
        assert summary.total_reps == summary.successful_reps + summary.failed_reps


def test_counters_non_negative():
    summary = summarize_rep_counters(successful_reps=2, failed_reps=1)
    assert summary.successful_reps >= 0
    assert summary.failed_reps >= 0
    assert summary.total_reps >= 0


def test_rep_summary_rejects_negative_and_broken_invariant():
    with pytest.raises(ValueError):
        RepSummary(successful_reps=-1, failed_reps=0, total_reps=-1)
    with pytest.raises(ValueError):
        RepSummary(successful_reps=1, failed_reps=1, total_reps=3)


def _squat_metrics(knee: float, hip: float | None = None, torso: float = 15.0) -> dict:
    if hip is None:
        hip = knee if knee >= 155 else max(75.0, knee - 5.0)
        if knee >= 155:
            hip = max(hip, 155.0)
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


def _feed_squat(a: SquatAnalyzer, angles: list[float], torso: float = 15.0) -> None:
    for angle in angles:
        a.analyze_frame(
            _squat_metrics(angle, torso=torso),
            pose_confidence=0.9,
            torso_lean=torso,
            fps=30.0,
        )


def _full_squat_cycle() -> list[float]:
    return [165] * 10 + [125] * 8 + [80] * 10 + [120] * 8 + [165] * 10


def _pushup_angles(
    elbow: float,
    *,
    shoulder: float = 80.0,
    body_alignment_angle: float = 175.0,
    body_line_offset: float = 0.01,
) -> dict:
    return {
        "avg_elbow": elbow,
        "avg_shoulder": shoulder,
        "avg_hip": 170.0,
        "body_alignment_angle": body_alignment_angle,
        "body_line_offset": body_line_offset,
        "alignment_side": "left",
    }


def _hold_pushup(a: PushupAnalyzer, elbow: float, frames: int, **kwargs) -> None:
    for _ in range(frames):
        a.analyze_frame(_pushup_angles(elbow, **kwargs))


def _full_pushup(a: PushupAnalyzer, **kwargs) -> None:
    _hold_pushup(a, 165, 6, **kwargs)
    _hold_pushup(a, 125, 8, **kwargs)
    _hold_pushup(a, 80, 8, **kwargs)
    _hold_pushup(a, 120, 8, **kwargs)
    _hold_pushup(a, 160, 8, **kwargs)


def test_angle_spike_does_not_create_failed_rep_squat():
    a = SquatAnalyzer(fps=30)
    _feed_squat(a, [165] * 8)
    # Single-frame spike then recover — should not finalize a failed attempt.
    _feed_squat(a, [90, 165, 165, 165])
    a.finalize_session()
    summary = a.get_rep_summary()
    assert summary["failed_reps"] == 0
    assert summary["total_reps"] == a.valid_reps + a.invalid_reps


def test_low_visibility_does_not_create_failed_rep_pushup():
    a = PushupAnalyzer()
    _hold_pushup(a, 165, 4)
    before = a.get_rep_summary()
    for _ in range(10):
        a.analyze_frame(_pushup_angles(80), landmark_visibility_ok=False)
    after = a.get_rep_summary()
    assert after == before
    assert after["failed_reps"] == 0


def test_camera_status_does_not_create_failed_rep_pushup():
    a = PushupAnalyzer()
    _hold_pushup(a, 165, 4)
    before = a.invalid_reps
    for _ in range(8):
        a.analyze_frame(_pushup_angles(165), camera_status="too_far")
    assert a.invalid_reps == before
    assert a.get_rep_summary()["failed_reps"] == 0


def test_same_failed_attempt_counted_once_pushup():
    a = PushupAnalyzer()
    _hold_pushup(a, 165, 6)
    _hold_pushup(a, 125, 8)  # descending
    _hold_pushup(a, 160, 10)  # up without bottom → one incomplete
    assert a.invalid_reps == 1
    assert a.get_rep_summary()["failed_reps"] == 1
    assert a.get_rep_summary()["total_reps"] == 1
    assert len(a.rep_history) == 1
    assert a.rep_history[0]["valid"] is False


def test_valid_rep_with_form_feedback_still_successful_pushup():
    a = PushupAnalyzer()
    _full_pushup(a, body_line_offset=0.08, body_alignment_angle=150.0)
    a.finalize_session()
    summary = a.get_rep_summary()
    assert a.rep_count == 1
    assert summary["successful_reps"] == 1
    assert summary["failed_reps"] == 0
    assert summary["total_reps"] == 1


def test_squat_valid_rep_counting_preserved():
    a = SquatAnalyzer(fps=30)
    _feed_squat(a, _full_squat_cycle())
    a.finalize_session()
    summary = a.get_rep_summary()
    assert a.rep_count >= 1
    assert a.valid_reps >= 1
    assert summary["successful_reps"] == a.valid_reps
    assert summary["failed_reps"] == a.invalid_reps
    assert summary["total_reps"] == summary["successful_reps"] + summary["failed_reps"]


def test_squat_half_attempt_failed_when_recorded():
    a = SquatAnalyzer(fps=30)
    # Shallow descent — may record incomplete or be rejected as FP.
    seq = [165] * 10 + list(range(165, 130, -3)) + [130] * 4 + list(range(130, 165, 3)) + [165] * 8
    _feed_squat(a, seq)
    a.finalize_session()
    summary = a.get_rep_summary()
    assert summary["total_reps"] == summary["successful_reps"] + summary["failed_reps"]
    assert summary["successful_reps"] == a.valid_reps
    assert summary["failed_reps"] == a.invalid_reps
    # Either no recorded attempt (FP filter) or failed/incomplete — not a silent invent.
    assert a.valid_reps == 0


def test_pushup_valid_rep_summary():
    a = PushupAnalyzer()
    _full_pushup(a)
    a.finalize_session()
    summary = a.get_rep_summary()
    assert a.rep_count == 1
    assert summary == {
        "successful_reps": 1,
        "failed_reps": 0,
        "total_reps": 1,
    }


def test_pushup_incomplete_failed_summary():
    a = PushupAnalyzer()
    _hold_pushup(a, 165, 6)
    _hold_pushup(a, 125, 8)
    _hold_pushup(a, 160, 8)
    a.finalize_session()
    summary = a.get_rep_summary()
    assert a.rep_count == 0
    assert summary["successful_reps"] == 0
    assert summary["failed_reps"] == 1
    assert summary["total_reps"] == 1


def test_history_matches_summary_multi_rep_pushup():
    a = PushupAnalyzer()
    _full_pushup(a)
    _hold_pushup(a, 165, 6)
    _hold_pushup(a, 125, 8)
    _hold_pushup(a, 160, 8)  # failed
    _full_pushup(a)
    a.finalize_session()
    summary = a.get_rep_summary()
    assert len(a.rep_history) == summary["total_reps"]
    assert sum(1 for r in a.rep_history if r.get("valid")) == summary["successful_reps"]
    assert sum(1 for r in a.rep_history if not r.get("valid")) == summary["failed_reps"]
    assert a.rep_count == summary["successful_reps"]  # push-up: rep_count == successful
    assert a.invalid_reps == summary["failed_reps"]


def test_existing_rep_count_semantics_unchanged_squat_two_valid():
    a = SquatAnalyzer(fps=30)
    _feed_squat(a, _full_squat_cycle())
    _feed_squat(a, _full_squat_cycle())
    a.finalize_session()
    result = a.get_result()
    assert result["rep_count"] == result["valid_reps"] + result["invalid_reps"]
    assert result["successful_reps"] == result["valid_reps"]
    assert result["failed_reps"] == result["invalid_reps"]
    assert result["total_reps"] == result["successful_reps"] + result["failed_reps"]
    # When only successful reps exist, squat rep_count equals successful
    if result["invalid_reps"] == 0:
        assert result["rep_count"] == result["successful_reps"]


def test_pushup_rep_count_still_means_successful_only():
    a = PushupAnalyzer()
    _full_pushup(a)
    _hold_pushup(a, 165, 6)
    _hold_pushup(a, 125, 8)
    _hold_pushup(a, 160, 8)
    a.finalize_session()
    result = a.get_result()
    assert result["rep_count"] == 1
    assert result["successful_reps"] == 1
    assert result["failed_reps"] == 1
    assert result["total_reps"] == 2
    assert result["rep_count"] == result["successful_reps"]
    assert result["rep_count"] != result["total_reps"]


def test_scoring_not_used_for_validity_pushup():
    # Form issues may lower score quality metrics but valid cycle remains successful.
    a = PushupAnalyzer()
    _full_pushup(a, body_line_offset=0.09, body_alignment_angle=145.0)
    a.finalize_session()
    assert a.get_rep_summary()["successful_reps"] == 1
    assert a.rep_count == 1
