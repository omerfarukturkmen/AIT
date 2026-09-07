"""Unit tests for SquatAnalyzer state machine (no video hardcoding)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from squat_analyzer import (  # noqa: E402
    FINALIZE_RETURN_ANGLE,
    STANDING_ENTER,
    SquatAnalyzer,
    VALID_DEPTH_ANGLE,
)


def _hip_for_knee(angle: float) -> float:
    if angle >= 155:
        return angle
    if angle <= 90:
        return max(75.0, angle - 5.0)
    return min(angle + 12.0, 160.0)


def _feed(analyzer: SquatAnalyzer, angles: list[float], fps: float = 30.0) -> None:
    for angle in angles:
        hip = _hip_for_knee(angle)
        analyzer.analyze_frame(
            {
                "left": angle,
                "right": angle,
                "average": angle,
                "avg_knee": angle,
                "left_hip": hip,
                "right_hip": hip,
                "avg_hip": hip,
                "selected_hip": hip,
                "selected_side": "right",
            },
            pose_confidence=0.9,
            torso_lean=10.0,
            fps=fps,
        )


def _hold(angle: float, n: int) -> list[float]:
    return [angle] * n


def _ramp(start: float, end: float, n: int) -> list[float]:
    if n <= 1:
        return [end]
    step = (end - start) / (n - 1)
    return [start + i * step for i in range(n)]


def test_opening_bottom_to_standing_counts_zero():
    a = SquatAnalyzer(fps=30)
    # Start at bottom, rise to standing — half rep, not armed yet.
    seq = _hold(85, 8) + _ramp(85, 165, 20) + _hold(165, 10)
    _feed(a, seq)
    result = a.get_result()
    assert result["rep_count"] == 0
    assert result["valid_reps"] == 0


def test_one_full_standing_bottom_standing():
    a = SquatAnalyzer(fps=30)
    seq = (
        _hold(165, 10)  # arm
        + _ramp(165, 80, 18)
        + _hold(80, 6)
        + _ramp(80, 165, 18)
        + _hold(165, 8)
    )
    _feed(a, seq)
    result = a.get_result()
    assert result["rep_count"] == 1
    assert result["valid_reps"] == 1


def test_two_full_reps():
    a = SquatAnalyzer(fps=30)
    one = (
        _ramp(165, 75, 16)
        + _hold(75, 4)
        + _ramp(75, 165, 16)
        + _hold(165, 8)
    )
    seq = _hold(165, 10) + one + one
    _feed(a, seq)
    result = a.get_result()
    assert result["rep_count"] == 2
    assert len(result["rep_history"]) == 2


def test_finalize_counts_second_rep_without_full_standing_confirm():
    a = SquatAnalyzer(fps=30)
    first = (
        _ramp(165, 78, 16)
        + _hold(78, 4)
        + _ramp(78, 165, 16)
        + _hold(165, 8)
    )
    # Second rep: depth then ascend near standing, but stop before long standing confirm.
    second = (
        _ramp(165, 82, 16)
        + _hold(82, 4)
        + _ramp(82, FINALIZE_RETURN_ANGLE + 2, 14)
        + _hold(FINALIZE_RETURN_ANGLE + 2, 2)
    )
    seq = _hold(165, 10) + first + second
    _feed(a, seq)
    result = a.get_result()
    assert result["rep_count"] == 2
    assert len(result["rep_history"]) == 2


def test_mid_ascent_end_does_not_count():
    a = SquatAnalyzer(fps=30)
    seq = (
        _hold(165, 10)
        + _ramp(165, 80, 16)
        + _hold(80, 4)
        + _ramp(80, 125, 10)  # stuck ascending mid-way
    )
    _feed(a, seq)
    result = a.get_result()
    assert result["rep_count"] == 0
    assert "incomplete_rep" in result["errors"]


def test_threshold_noise_does_not_double_count():
    a = SquatAnalyzer(fps=30)
    # Oscillate around standing enter/exit after one valid rep.
    after = []
    for _ in range(12):
        after.extend([152, 148, 156, 149, 154])
    seq = (
        _hold(165, 10)
        + _ramp(165, 78, 16)
        + _hold(78, 4)
        + _ramp(78, 165, 16)
        + _hold(165, 6)
        + after
    )
    _feed(a, seq)
    result = a.get_result()
    assert result["rep_count"] == 1


def test_start_bottom_then_two_reps_skips_half():
    a = SquatAnalyzer(fps=30)
    opening = _hold(88, 6) + _ramp(88, 165, 18) + _hold(165, 10)
    rep = (
        _ramp(165, 76, 16)
        + _hold(76, 4)
        + _ramp(76, 165, 16)
        + _hold(165, 8)
    )
    seq = opening + rep + rep
    _feed(a, seq)
    result = a.get_result()
    assert result["rep_count"] == 2
    assert result["valid_reps"] == 2
    assert all(r["min_knee_angle"] < VALID_DEPTH_ANGLE for r in result["rep_history"])


@pytest.mark.integration
def test_real_video_img_5512_if_present():
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
    ai = out["ai_result"]
    metrics = out["metrics"]
    domain = out.get("domain_result") or {}
    assert metrics["total_frames"] == 332
    assert abs(metrics["duration_seconds"] - 11.08) < 0.25
    assert ai["reps"]["successful"] == 2
    assert ai["reps"]["total"] == 2
    assert domain.get("rep_count") == 2
    assert len(domain.get("rep_history") or []) == 2
    assert metrics["processed_frames"] > 0
    assert metrics["mean_landmark_visibility"] > 0
