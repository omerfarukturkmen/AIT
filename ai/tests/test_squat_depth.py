"""Tests for squat depth measurement (knee + hip confirmation layer)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from squat_analyzer import (  # noqa: E402
    DEPTH_CONFIRMATION_FRAMES,
    ERROR_MESSAGES,
    SquatAnalyzer,
)


def _metrics(
    knee: float | None,
    hip: float | None,
    torso: float | None = 15.0,
) -> dict:
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


def _start_rep(a: SquatAnalyzer) -> None:
    a.in_rep_attempt = True
    a.descent_started = True
    a._reset_depth_tracking()


def _feed_depth(
    a: SquatAnalyzer,
    knee: float | None,
    hip: float | None,
    frames: int = 1,
    *,
    torso: float = 15.0,
) -> None:
    for _ in range(frames):
        a._update_depth_evaluation(_metrics(knee, hip, torso), torso)


def test_deep_squat_confirms_after_three_frames():
    a = SquatAnalyzer(fps=30)
    _start_rep(a)
    _feed_depth(a, 90, 95, DEPTH_CONFIRMATION_FRAMES)
    assert a.depth_confirmed is True
    assert a.current_rep_best_depth_status == "deep"


def test_acceptable_squat_confirms_after_three_frames():
    a = SquatAnalyzer(fps=30)
    _start_rep(a)
    _feed_depth(a, 110, 120, DEPTH_CONFIRMATION_FRAMES)
    assert a.depth_confirmed is True
    assert a.current_rep_best_depth_status == "acceptable"


def test_shallow_squat_not_confirmed():
    a = SquatAnalyzer(fps=30)
    _start_rep(a)
    _feed_depth(a, 135, 145, 5)
    assert a.depth_confirmed is False
    assert a.current_rep_best_depth_status == "shallow"


def test_deep_knee_shallow_hip_not_confirmed():
    a = SquatAnalyzer(fps=30)
    _start_rep(a)
    _feed_depth(a, 90, 150, DEPTH_CONFIRMATION_FRAMES)
    assert a.depth_confirmed is False


def test_deep_hip_shallow_knee_not_confirmed():
    a = SquatAnalyzer(fps=30)
    _start_rep(a)
    _feed_depth(a, 140, 95, DEPTH_CONFIRMATION_FRAMES)
    assert a.depth_confirmed is False


def test_single_deep_frame_not_confirmed():
    a = SquatAnalyzer(fps=30)
    _start_rep(a)
    _feed_depth(a, 90, 95, 1)
    assert a.depth_confirmed is False


def test_two_deep_frames_not_confirmed():
    a = SquatAnalyzer(fps=30)
    _start_rep(a)
    _feed_depth(a, 90, 95, 2)
    assert a.depth_confirmed is False


def test_three_deep_frames_confirmed():
    a = SquatAnalyzer(fps=30)
    _start_rep(a)
    _feed_depth(a, 90, 95, 3)
    assert a.depth_confirmed is True


def test_confirmed_stays_true_after_shallow_frame_in_same_rep():
    a = SquatAnalyzer(fps=30)
    _start_rep(a)
    _feed_depth(a, 90, 95, DEPTH_CONFIRMATION_FRAMES)
    assert a.depth_confirmed is True
    _feed_depth(a, 135, 145, 3)
    assert a.depth_confirmed is True


def test_depth_resets_on_new_rep():
    a = SquatAnalyzer(fps=30)
    _start_rep(a)
    _feed_depth(a, 90, 95, DEPTH_CONFIRMATION_FRAMES)
    assert a.depth_confirmed is True
    a._reset_depth_tracking()
    assert a.depth_confirmed is False
    assert a.depth_candidate_frames == 0
    assert a.current_rep_best_depth_status == "unknown"


def test_hysteresis_boundary_noise_does_not_flicker_or_false_confirm():
    a = SquatAnalyzer(fps=30)
    _start_rep(a)
    knees = [113, 116, 114, 117, 112]
    hips = [122, 126, 123, 128, 121]
    for k, h in zip(knees, hips):
        _feed_depth(a, k, h, 1)
    assert a.depth_confirmed is False
    assert a.depth_candidate_frames >= 1


def test_minimum_angle_tracking():
    a = SquatAnalyzer(fps=30)
    _start_rep(a)
    sequence = [
        (140, 150),
        (120, 130),
        (105, 115),
        (92, 98),
        (100, 110),
        (130, 140),
    ]
    for k, h in sequence:
        _feed_depth(a, k, h, 1)
    assert a.current_rep_min_knee_angle == 92
    assert a.current_rep_min_hip_angle == 98


def test_depth_score_standing_low():
    a = SquatAnalyzer(fps=30)
    score = a._compute_depth_score(160, 170)
    assert score is not None
    assert score == 0.0


def test_depth_score_deep_high():
    a = SquatAnalyzer(fps=30)
    score = a._compute_depth_score(85, 88)
    assert score is not None
    assert score >= 90.0
    assert score <= 100.0


def test_depth_score_acceptable_mid_high():
    a = SquatAnalyzer(fps=30)
    score = a._compute_depth_score(110, 120)
    assert score is not None
    assert 40.0 <= score <= 100.0


def test_depth_score_clamped_and_handles_none():
    a = SquatAnalyzer(fps=30)
    assert a._compute_depth_score(None, 100) is None
    assert a._compute_depth_score(100, None) is None
    score = a._compute_depth_score(100, 100)
    assert score is not None
    assert 0.0 <= score <= 100.0


def test_best_depth_status_upgrades_acceptable_to_deep():
    a = SquatAnalyzer(fps=30)
    _start_rep(a)
    _feed_depth(a, 110, 120, DEPTH_CONFIRMATION_FRAMES)
    assert a.current_rep_best_depth_status == "acceptable"
    _feed_depth(a, 90, 95, DEPTH_CONFIRMATION_FRAMES)
    assert a.current_rep_best_depth_status == "deep"


def test_metrics_incomplete_does_not_increment_candidate():
    a = SquatAnalyzer(fps=30)
    _start_rep(a)
    _feed_depth(a, 90, None, 3)
    assert a.depth_confirmed is False
    assert a.depth_candidate_frames == 0
    assert a.depth_status == "metrics_incomplete"


def test_depth_snapshot_fields():
    a = SquatAnalyzer(fps=30)
    _start_rep(a)
    _feed_depth(a, 90, 95, DEPTH_CONFIRMATION_FRAMES)
    snap = a._depth_snapshot()
    assert snap["status"] == "deep"
    assert snap["confirmed"] is True
    assert snap["candidate_frames"] >= DEPTH_CONFIRMATION_FRAMES
    assert snap["score"] is not None
    assert snap["min_knee_angle"] == 90
    assert snap["min_hip_angle"] == 95


def _hip_for_knee(angle: float) -> float:
    if angle >= 155:
        return angle
    if angle <= 90:
        return max(75.0, angle - 5.0)
    return min(angle + 12.0, 160.0)


def _feed_squat_sequence(
    a: SquatAnalyzer,
    angles: list[float],
    hip: float | None = None,
) -> None:
    for angle in angles:
        hip_angle = hip if hip is not None else _hip_for_knee(angle)
        if angle >= 155:
            hip_angle = max(hip_angle, 155.0)
        a.analyze_frame(
            _metrics(angle, hip_angle, 15.0),
            pose_confidence=0.9,
            torso_lean=15.0,
            fps=30.0,
        )


def test_shallow_rep_feedback_once_and_insufficient_depth_counter():
    a = SquatAnalyzer(fps=30)
    seq = (
        [165] * 10
        + list(range(165, 130, -3))  # shallow descent
        + [130] * 4
        + list(range(130, 165, 3))
        + [165] * 8
    )
    _feed_squat_sequence(a, seq)
    result = a.get_result()
    depth_msg = ERROR_MESSAGES["squat_depth_reach"]
    feedback_text = " ".join(result.get("feedback") or [])
    assert depth_msg in feedback_text or any(
        depth_msg in (r.get("feedback") or []) for r in result.get("rep_history") or []
    )
    assert a.form_errors.get("insufficient_depth", 0) >= 1


def test_rep_history_includes_depth_fields_after_valid_rep():
    a = SquatAnalyzer(fps=30)
    seq = (
        [165] * 10
        + list(range(165, 75, -5))
        + [75] * 6
        + list(range(75, 165, 5))
        + [165] * 8
    )
    _feed_squat_sequence(a, seq)
    result = a.get_result()
    assert result["rep_count"] >= 1
    rep = result["rep_history"][0]
    assert "depth_status" in rep
    assert "depth_score" in rep
    assert "min_hip_angle" in rep


@pytest.mark.integration
def test_real_video_depth_fields_if_present():
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
    domain = out.get("domain_result") or {}
    assert ai["reps"]["successful"] == 2
    for rep in domain.get("rep_history") or []:
        assert "depth_status" in rep
        assert "depth_score" in rep
