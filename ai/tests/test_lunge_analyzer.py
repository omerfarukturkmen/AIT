"""Unit tests for lunge landmark / angle analysis scaffold."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from exercise_registry import (  # noqa: E402
    UnsupportedExerciseError,
    normalize_exercise_type,
    registered_exercise_keys,
)
from lunge_analyzer import (  # noqa: E402
    LUNGE_REQUIRED_LANDMARKS,
    analyze_lunge_landmarks,
    extract_lunge_angles,
    lunge_pose_landmark_indices,
)
from pose_detector import LandmarkListAdapter, NormalizedLandmarkPoint  # noqa: E402
from pose_schema import PoseLandmark  # noqa: E402

IMG = 200


def _blank(visibility: float = 0.95) -> list[NormalizedLandmarkPoint]:
    return [
        NormalizedLandmarkPoint(x=0.5, y=0.5, z=0.0, visibility=visibility)
        for _ in range(33)
    ]


def _set_xy(
    points: list[NormalizedLandmarkPoint],
    index: PoseLandmark,
    x: float,
    y: float,
    visibility: float = 0.95,
) -> None:
    points[int(index)] = NormalizedLandmarkPoint(
        x=x, y=y, z=0.0, visibility=visibility
    )


def _pose_from_points(points: list[NormalizedLandmarkPoint]) -> LandmarkListAdapter:
    return LandmarkListAdapter(landmark=points)


def _straight_leg_pose(*, visibility: float = 0.95) -> LandmarkListAdapter:
    """Both legs nearly straight (~180°) and hips nearly open (~180°)."""
    points = _blank(visibility=visibility)
    # Left chain vertical
    _set_xy(points, PoseLandmark.LEFT_SHOULDER, 0.35, 0.15, visibility)
    _set_xy(points, PoseLandmark.LEFT_HIP, 0.35, 0.40, visibility)
    _set_xy(points, PoseLandmark.LEFT_KNEE, 0.35, 0.60, visibility)
    _set_xy(points, PoseLandmark.LEFT_ANKLE, 0.35, 0.85, visibility)
    # Right chain vertical
    _set_xy(points, PoseLandmark.RIGHT_SHOULDER, 0.65, 0.15, visibility)
    _set_xy(points, PoseLandmark.RIGHT_HIP, 0.65, 0.40, visibility)
    _set_xy(points, PoseLandmark.RIGHT_KNEE, 0.65, 0.60, visibility)
    _set_xy(points, PoseLandmark.RIGHT_ANKLE, 0.65, 0.85, visibility)
    return _pose_from_points(points)


def _bent_90_pose(*, visibility: float = 0.95) -> LandmarkListAdapter:
    """Both knees and hips form ~90° angles."""
    points = _blank(visibility=visibility)
    # Left knee 90° at knee: hip above, ankle to the right
    _set_xy(points, PoseLandmark.LEFT_SHOULDER, 0.30, 0.10, visibility)
    _set_xy(points, PoseLandmark.LEFT_HIP, 0.30, 0.40, visibility)
    _set_xy(points, PoseLandmark.LEFT_KNEE, 0.30, 0.60, visibility)
    _set_xy(points, PoseLandmark.LEFT_ANKLE, 0.50, 0.60, visibility)
    # Left hip 90° at hip: shoulder left of hip, knee below
    # shoulder (0.10, 0.40), hip (0.30, 0.40), knee (0.30, 0.60) → 90°
    _set_xy(points, PoseLandmark.LEFT_SHOULDER, 0.10, 0.40, visibility)

    # Right mirror
    _set_xy(points, PoseLandmark.RIGHT_SHOULDER, 0.90, 0.40, visibility)
    _set_xy(points, PoseLandmark.RIGHT_HIP, 0.70, 0.40, visibility)
    _set_xy(points, PoseLandmark.RIGHT_KNEE, 0.70, 0.60, visibility)
    _set_xy(points, PoseLandmark.RIGHT_ANKLE, 0.50, 0.60, visibility)
    return _pose_from_points(points)


def test_module_imports():
    assert callable(extract_lunge_angles)
    assert analyze_lunge_landmarks is extract_lunge_angles
    assert len(LUNGE_REQUIRED_LANDMARKS) == 8
    assert len(lunge_pose_landmark_indices()) == 8


def test_left_and_right_knee_angles_straight():
    result = extract_lunge_angles(_straight_leg_pose(), PoseLandmark, IMG, IMG)
    assert result["landmarks_valid"] is True
    assert result["left_knee_angle"] == pytest.approx(180.0, abs=1.0)
    assert result["right_knee_angle"] == pytest.approx(180.0, abs=1.0)


def test_left_and_right_hip_angles_straight():
    result = extract_lunge_angles(_straight_leg_pose(), PoseLandmark, IMG, IMG)
    assert result["left_hip_angle"] == pytest.approx(180.0, abs=1.0)
    assert result["right_hip_angle"] == pytest.approx(180.0, abs=1.0)


def test_approx_90_degree_geometry():
    result = extract_lunge_angles(_bent_90_pose(), PoseLandmark, IMG, IMG)
    assert result["left_knee_angle"] == pytest.approx(90.0, abs=1.0)
    assert result["right_knee_angle"] == pytest.approx(90.0, abs=1.0)
    assert result["left_hip_angle"] == pytest.approx(90.0, abs=1.0)
    assert result["right_hip_angle"] == pytest.approx(90.0, abs=1.0)


def test_approx_180_degree_geometry():
    result = extract_lunge_angles(_straight_leg_pose(), PoseLandmark, IMG, IMG)
    for key in (
        "left_knee_angle",
        "right_knee_angle",
        "left_hip_angle",
        "right_hip_angle",
    ):
        assert result[key] == pytest.approx(180.0, abs=1.0)


def test_landmarks_none_safe():
    result = extract_lunge_angles(None, PoseLandmark, IMG, IMG)
    assert result["landmarks_valid"] is False
    assert result["left_knee_angle"] is None
    assert result["right_knee_angle"] is None
    assert result["left_hip_angle"] is None
    assert result["right_hip_angle"] is None


def test_missing_landmarks_safe():
    # Only blank default points — hips/knees/ankles coincide; still no crash.
    result = extract_lunge_angles(_pose_from_points(_blank()), PoseLandmark, IMG, IMG)
    assert isinstance(result, dict)
    assert "left_knee_angle" in result


def test_low_visibility_safe():
    result = extract_lunge_angles(
        _straight_leg_pose(visibility=0.05), PoseLandmark, IMG, IMG
    )
    assert result["landmarks_valid"] is False
    assert result["left_knee_angle"] is None
    assert result["right_knee_angle"] is None
    assert result["left_hip_angle"] is None
    assert result["right_hip_angle"] is None


def test_deterministic_same_input():
    pose = _bent_90_pose()
    a = extract_lunge_angles(pose, PoseLandmark, IMG, IMG)
    b = extract_lunge_angles(pose, PoseLandmark, IMG, IMG)
    assert a == b


def test_lunge_not_in_production_registry():
    """Scaffold is not registered — avoids fake rep/score via analyze_video."""
    assert "lunge" not in registered_exercise_keys()
    with pytest.raises(UnsupportedExerciseError):
        normalize_exercise_type("lunge")


def test_squat_and_pushup_registry_unchanged():
    assert normalize_exercise_type("squat") == "squat"
    assert normalize_exercise_type("pushup") == "pushup"
    assert normalize_exercise_type("push-up") == "pushup"
    assert set(registered_exercise_keys()) == {"pushup", "squat"}
