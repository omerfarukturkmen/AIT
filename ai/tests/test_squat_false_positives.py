"""Tests for squat rep false-positive reduction."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from squat_analyzer import (  # noqa: E402
    ERROR_MESSAGES,
    MIN_POSE_CONFIDENCE,
    STANDING_CONFIRMATION_FRAMES,
    SquatAnalyzer,
)


def _metrics(knee: float | None, hip: float | None, torso: float = 15.0) -> dict:
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


def _feed(
    a: SquatAnalyzer,
    angles: list[float],
    *,
    fps: float = 30.0,
    confidence: float = 0.9,
) -> None:
    for angle in angles:
        hip = _hip_for_knee(angle)
        a.analyze_frame(
            _metrics(angle, hip, 15.0),
            pose_confidence=confidence,
            torso_lean=15.0,
            fps=fps,
        )


def _hold(angle: float, n: int) -> list[float]:
    return [angle] * n


def _ramp(start: float, end: float, n: int) -> list[float]:
    if n <= 1:
        return [end]
    step = (end - start) / (n - 1)
    return [start + i * step for i in range(n)]


def _full_squat(standing: float = 165.0, bottom: float = 80.0) -> list[float]:
    return (
        _hold(standing, STANDING_CONFIRMATION_FRAMES + 4)
        + _ramp(standing, bottom, 16)
        + _hold(bottom, 6)
        + _ramp(bottom, standing, 16)
        + _hold(standing, STANDING_CONFIRMATION_FRAMES + 4)
    )


def test_small_knee_bend_not_counted():
    a = SquatAnalyzer(fps=30)
    _feed(a, [170, 165, 160, 165, 170] * 4)
    result = a.get_result()
    assert result["rep_count"] == 0


def test_single_frame_spike_not_counted():
    a = SquatAnalyzer(fps=30)
    seq = [170] * 10 + [90] + [170] * 10
    _feed(a, seq)
    result = a.get_result()
    assert result["rep_count"] == 0


def test_threshold_noise_not_counted():
    a = SquatAnalyzer(fps=30)
    seq = [160, 157, 161, 158, 160, 159, 162] * 6
    _feed(a, seq)
    result = a.get_result()
    assert result["rep_count"] == 0


def test_shallow_squat_not_valid():
    a = SquatAnalyzer(fps=30)
    seq = (
        _hold(165, 10)
        + _ramp(165, 125, 14)
        + _hold(125, 6)
        + _ramp(125, 165, 14)
        + _hold(165, 10)
    )
    _feed(a, seq)
    result = a.get_result()
    assert result["valid_reps"] == 0
    assert result["rep_count"] == 0 or result["invalid_reps"] >= 1


def test_valid_full_squat_counts_once():
    a = SquatAnalyzer(fps=30)
    _feed(a, _full_squat())
    result = a.get_result()
    assert result["rep_count"] == 1
    assert result["valid_reps"] == 1


def test_two_full_squats_count_two():
    a = SquatAnalyzer(fps=30)
    one = _full_squat()
    _feed(a, one + one)
    result = a.get_result()
    assert result["rep_count"] == 2
    assert result["valid_reps"] == 2


def test_bottom_bounce_single_rep():
    a = SquatAnalyzer(fps=30)
    seq = (
        _hold(165, 10)
        + _ramp(165, 80, 16)
        + _hold(80, 4)
        + _ramp(80, 110, 8)
        + _ramp(110, 80, 8)
        + _ramp(80, 165, 16)
        + _hold(165, 10)
    )
    _feed(a, seq)
    result = a.get_result()
    assert result["rep_count"] == 1


def test_partial_ascent_then_descent_not_double_count():
    a = SquatAnalyzer(fps=30)
    seq = (
        _hold(165, 10)
        + _ramp(165, 78, 16)
        + _hold(78, 4)
        + _ramp(78, 130, 10)
        + _ramp(130, 78, 10)
        + _ramp(78, 165, 16)
        + _hold(165, 10)
    )
    _feed(a, seq)
    result = a.get_result()
    assert result["valid_reps"] <= 1
    assert result["rep_count"] <= 1


def test_video_mid_squat_start_then_valid_rep():
    a = SquatAnalyzer(fps=30)
    opening = _hold(85, 8) + _ramp(85, 165, 18) + _hold(165, 10)
    _feed(a, opening + _full_squat())
    result = a.get_result()
    assert result["rep_count"] == 1
    assert result["valid_reps"] == 1


def test_low_confidence_does_not_cancel_valid_rep():
    a = SquatAnalyzer(fps=30)
    seq = _full_squat()
    for i, angle in enumerate(seq):
        hip = _hip_for_knee(angle)
        conf = 0.3 if 20 <= i <= 24 else 0.9
        a.analyze_frame(
            _metrics(angle, hip, 15.0),
            pose_confidence=conf,
            torso_lean=15.0,
            fps=30.0,
        )
    result = a.get_result()
    assert result["rep_count"] == 1
    assert 0.3 < MIN_POSE_CONFIDENCE


def test_none_metrics_no_crash_no_false_rep():
    a = SquatAnalyzer(fps=30)
    seq = _full_squat()
    for i, angle in enumerate(seq):
        if 18 <= i <= 20:
            a.analyze_frame(
                _metrics(None, None, 15.0),
                pose_confidence=0.9,
                torso_lean=15.0,
                fps=30.0,
            )
        else:
            hip = _hip_for_knee(angle)
            a.analyze_frame(
                _metrics(angle, hip, 15.0),
                pose_confidence=0.9,
                torso_lean=15.0,
                fps=30.0,
            )
    result = a.get_result()
    assert result["rep_count"] in (0, 1)


def test_double_count_guard_standing_hold():
    a = SquatAnalyzer(fps=30)
    _feed(a, _full_squat() + _hold(165, 20))
    result = a.get_result()
    assert result["rep_count"] == 1


def test_finalize_idempotency():
    a = SquatAnalyzer(fps=30)
    _feed(a, _hold(165, 10) + _ramp(165, 80, 16) + _hold(80, 4))
    before = (a.rep_count, a.valid_reps, a.invalid_reps, dict(a.form_errors))
    a.finalize_session()
    a.finalize_session()
    r1 = a.get_result()
    r2 = a.get_result()
    after = (a.rep_count, a.valid_reps, a.invalid_reps, dict(a.form_errors))
    assert before[0:3] == after[0:3] or after[2] >= before[2]
    assert r1["rep_count"] == r2["rep_count"]
    assert r1["valid_reps"] == r2["valid_reps"]
    assert r1["invalid_reps"] == r2["invalid_reps"]
    assert r1["form_errors"] == r2["form_errors"]


def test_lifecycle_snapshot_fields():
    a = SquatAnalyzer(fps=30)
    snap = a.analyze_frame(_metrics(165, 165, 15.0), pose_confidence=0.9)
    assert "rep_lifecycle" in snap
    lc = snap["rep_lifecycle"]
    assert "rep_in_progress" in lc
    assert "movement_direction" in lc
    assert "has_seen_valid_standing" in lc


def test_shallow_incomplete_feedback_once():
    a = SquatAnalyzer(fps=30)
    seq = (
        _hold(165, 10)
        + _ramp(165, 130, 14)
        + _hold(130, 6)
        + _ramp(130, 165, 14)
        + _hold(165, 10)
    )
    _feed(a, seq)
    result = a.get_result()
    msg = ERROR_MESSAGES["squat_depth_reach"]
    session_fb = result.get("feedback") or []
    assert session_fb.count(msg) <= 1


@pytest.mark.integration
def test_real_video_still_two_reps_if_present():
    video = (
        Path(__file__).resolve().parents[2]
        / "backend"
        / "uploaded_videos"
        / "IMG_5512.mp4"
    )
    if not video.exists():
        pytest.skip("IMG_5512.mp4 not present")

    from video_processor import run_video_analysis

    out = run_video_analysis(
        video_path=str(video),
        exercise_type="squat",
        show_preview=False,
        write_json=False,
    )
    assert out["ai_result"]["reps"]["successful"] == 2
    assert out.get("domain_result", {}).get("rep_count") == 2
