"""Tests for exercise-specific landmark visibility gating."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pose_detector import LandmarkListAdapter, NormalizedLandmarkPoint  # noqa: E402
from pose_schema import PoseLandmark  # noqa: E402
from pushup_analyzer import PushupAnalyzer  # noqa: E402
from squat_analyzer import SquatAnalyzer  # noqa: E402
from visibility_utils import (  # noqa: E402
    MIN_REQUIRED_LANDMARK_VISIBILITY,
    VISIBILITY_WARNING,
    evaluate_exercise_landmark_visibility,
    sanitize_visibility,
)
from video_processor import (  # noqa: E402
    _apply_visibility_session_result,
    _finalize_quality_stats,
)

_SQUAT_LEFT = (
    PoseLandmark.LEFT_SHOULDER,
    PoseLandmark.LEFT_HIP,
    PoseLandmark.LEFT_KNEE,
    PoseLandmark.LEFT_ANKLE,
)
_SQUAT_RIGHT = (
    PoseLandmark.RIGHT_SHOULDER,
    PoseLandmark.RIGHT_HIP,
    PoseLandmark.RIGHT_KNEE,
    PoseLandmark.RIGHT_ANKLE,
)
_PUSHUP_LEFT = (
    PoseLandmark.LEFT_SHOULDER,
    PoseLandmark.LEFT_ELBOW,
    PoseLandmark.LEFT_WRIST,
    PoseLandmark.LEFT_HIP,
    PoseLandmark.LEFT_KNEE,
    PoseLandmark.LEFT_ANKLE,
)
_PUSHUP_RIGHT = (
    PoseLandmark.RIGHT_SHOULDER,
    PoseLandmark.RIGHT_ELBOW,
    PoseLandmark.RIGHT_WRIST,
    PoseLandmark.RIGHT_HIP,
    PoseLandmark.RIGHT_KNEE,
    PoseLandmark.RIGHT_ANKLE,
)


def _blank(visibility: float = 0.95) -> list[NormalizedLandmarkPoint]:
    return [
        NormalizedLandmarkPoint(x=0.5, y=0.5, z=0.0, visibility=visibility)
        for _ in range(33)
    ]


def _set_visibility(
    points: list[NormalizedLandmarkPoint],
    index: PoseLandmark,
    visibility: float,
) -> None:
    p = points[int(index)]
    points[int(index)] = NormalizedLandmarkPoint(
        x=p.x, y=p.y, z=p.z, visibility=visibility
    )


def _adapter(
    *,
    left_vis: float = 0.90,
    right_vis: float = 0.10,
    exercise: str = "squat",
) -> LandmarkListAdapter:
    points = _blank(visibility=0.10)
    left_indices = _SQUAT_LEFT if exercise == "squat" else _PUSHUP_LEFT
    right_indices = _SQUAT_RIGHT if exercise == "squat" else _PUSHUP_RIGHT
    for idx in left_indices:
        _set_visibility(points, idx, left_vis)
    for idx in right_indices:
        _set_visibility(points, idx, right_vis)
    return LandmarkListAdapter(landmark=points)


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


def _hold(a: PushupAnalyzer, elbow: float, frames: int, **kwargs) -> None:
    for _ in range(frames):
        a.analyze_frame(_a(elbow, **kwargs))


def _squat_metrics(knee: float = 140.0, hip: float = 150.0) -> dict:
    return {
        "left": knee,
        "right": knee,
        "average": knee,
        "avg_knee": knee,
        "avg_hip": hip,
        "torso_lean": 15.0,
        "metrics_valid": True,
        "selected_side": "left",
    }


def test_squat_left_side_usable():
    plm = _adapter(left_vis=0.90, right_vis=0.10, exercise="squat")
    result = evaluate_exercise_landmark_visibility(plm, "squat")
    assert result.is_usable is True
    assert result.selected_side == "left"


def test_squat_right_side_usable():
    plm = _adapter(left_vis=0.10, right_vis=0.90, exercise="squat")
    result = evaluate_exercise_landmark_visibility(plm, "squat")
    assert result.is_usable is True
    assert result.selected_side == "right"


def test_squat_both_sides_unusable():
    plm = _adapter(left_vis=0.20, right_vis=0.20, exercise="squat")
    result = evaluate_exercise_landmark_visibility(plm, "squat")
    assert result.is_usable is False
    assert result.selected_side == "unknown"
    assert result.low_visibility_landmarks


def test_pushup_left_side_usable():
    plm = _adapter(left_vis=0.90, right_vis=0.10, exercise="pushup")
    result = evaluate_exercise_landmark_visibility(plm, "pushup")
    assert result.is_usable is True
    assert result.selected_side == "left"


def test_pushup_critical_elbow_low_both_sides_unusable():
    points = _blank(0.90)
    for idx in _PUSHUP_LEFT + _PUSHUP_RIGHT:
        _set_visibility(points, idx, 0.90)
    _set_visibility(points, PoseLandmark.LEFT_ELBOW, 0.20)
    _set_visibility(points, PoseLandmark.RIGHT_ELBOW, 0.20)
    plm = LandmarkListAdapter(landmark=points)
    result = evaluate_exercise_landmark_visibility(plm, "pushup")
    assert result.is_usable is False
    assert "LEFT_ELBOW" in result.low_visibility_landmarks
    assert "RIGHT_ELBOW" in result.low_visibility_landmarks


def test_visibility_exact_threshold_is_usable():
    plm = _adapter(left_vis=MIN_REQUIRED_LANDMARK_VISIBILITY, right_vis=0.10, exercise="squat")
    result = evaluate_exercise_landmark_visibility(plm, "squat")
    assert result.is_usable is True


@pytest.mark.parametrize(
    "value",
    [None, float("nan"), float("inf"), float("-inf"), -0.1, 1.2, "bad"],
)
def test_invalid_visibility_values(value):
    assert sanitize_visibility(value) is None


def test_low_visibility_freezes_pushup_rep_count():
    a = PushupAnalyzer()
    _hold(a, 165, 6)
    _hold(a, 125, 8)
    before_state = a.state
    before_reps = a.rep_count
    for _ in range(4):
        snap = a.analyze_frame(_a(80), landmark_visibility_ok=False)
        assert VISIBILITY_WARNING in snap["feedback"][0]
    assert a.state == before_state
    assert a.rep_count == before_reps
    assert a.rep_in_progress is True
    _hold(a, 80, 8)
    _hold(a, 120, 8)
    _hold(a, 160, 8)
    assert a.rep_count == 1


def test_low_visibility_does_not_confirm_bottom():
    a = PushupAnalyzer()
    _hold(a, 165, 6)
    _hold(a, 125, 8)
    for _ in range(5):
        a.analyze_frame(_a(70), landmark_visibility_ok=False)
    assert a.reached_bottom is False
    assert a.rep_count == 0


def test_low_visibility_no_form_error():
    a = PushupAnalyzer()
    _hold(a, 165, 6)
    _hold(a, 125, 8)
    before_errors = dict(a.form_errors)
    a.analyze_frame(
        _a(120, body_line_offset=0.09, body_alignment_angle=150),
        landmark_visibility_ok=False,
    )
    assert a.form_errors == before_errors
    assert a.current_rep_hips_sagging is False


def test_low_visibility_does_not_increment_invalid_reps():
    a = PushupAnalyzer()
    _hold(a, 165, 6)
    _hold(a, 125, 8)
    for _ in range(10):
        a.analyze_frame(_a(80), landmark_visibility_ok=False)
    a.finalize_session()
    assert a.invalid_reps == 0


def test_visibility_warning_priority_over_form():
    a = PushupAnalyzer()
    snap = a.analyze_frame(
        _a(120, body_line_offset=0.09, body_alignment_angle=150),
        landmark_visibility_ok=False,
    )
    assert VISIBILITY_WARNING in snap["feedback"][0]
    assert "Raise your hips" not in snap["feedback"]


def test_squat_analyzer_visibility_guard():
    a = SquatAnalyzer()
    _hold_squat = lambda frames: [
        a.analyze_frame(_squat_metrics(), pose_confidence=0.9) for _ in range(frames)
    ]
    _hold_squat(5)
    before_reps = a.rep_count
    before_state = a.current_state
    out = a.analyze_frame(
        _squat_metrics(),
        pose_confidence=0.9,
        landmark_visibility_ok=False,
    )
    assert VISIBILITY_WARNING in out["feedback"][0]
    assert a.rep_count == before_reps
    assert a.current_state == before_state


def test_fully_unusable_session_result():
    ai_result = {"rep_count": 0, "valid_reps": 0, "feedback": []}
    quality = {"usable_landmark_frames": 0, "low_visibility_frames": 20}
    _apply_visibility_session_result(
        ai_result,
        landmark_frames=20,
        quality_stats=quality,
    )
    assert ai_result["analysis_status"] == "insufficient_landmark_visibility"
    assert ai_result["feedback"].count(VISIBILITY_WARNING) == 1


def test_zero_landmark_frames_marks_insufficient_visibility():
    """All-no-pose sessions use the existing visibility status (no new fields)."""
    ai_result = {"rep_count": 0, "feedback": []}
    quality = {"usable_landmark_frames": 0, "low_visibility_frames": 0}
    _apply_visibility_session_result(
        ai_result,
        landmark_frames=0,
        quality_stats=quality,
    )
    assert ai_result["analysis_status"] == "insufficient_landmark_visibility"
    assert VISIBILITY_WARNING in ai_result["feedback"]


def test_mixed_frames_usable_ratio():
    quality = {
        "usable_landmark_frames": 80,
        "low_visibility_frames": 20,
    }
    _finalize_quality_stats(quality, pose_processed_frames=100)
    assert quality["usable_landmark_frame_ratio"] == pytest.approx(0.80, rel=1e-4)


def test_warning_deduplication_in_session_result():
    ai_result = {"rep_count": 0, "feedback": []}
    quality = {"usable_landmark_frames": 0, "low_visibility_frames": 20}
    _apply_visibility_session_result(
        ai_result,
        landmark_frames=20,
        quality_stats=quality,
    )
    _apply_visibility_session_result(
        ai_result,
        landmark_frames=20,
        quality_stats=quality,
    )
    assert ai_result["feedback"].count(VISIBILITY_WARNING) == 1


def test_visibility_independent_of_camera_status():
    plm = _adapter(left_vis=0.90, right_vis=0.10, exercise="squat")
    result = evaluate_exercise_landmark_visibility(plm, "squat")
    assert result.is_usable is True
    # Camera distance is not part of visibility evaluation.
    assert result.reason is None


def test_landmark_visibility_result_as_dict():
    plm = _adapter(left_vis=0.90, right_vis=0.10, exercise="pushup")
    result = evaluate_exercise_landmark_visibility(plm, "pushup")
    data = result.as_dict()
    assert data["is_usable"] is True
    assert "selected_side" in data
    assert math.isfinite(data["min_visibility"] or 0.0)
