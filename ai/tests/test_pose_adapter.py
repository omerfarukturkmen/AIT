"""Tests for LandmarkListAdapter / PoseDetectionResult."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from angle_utils import (  # noqa: E402
    calculate_knee_angles,
    calculate_pose_confidence,
    calculate_pushup_angles,
)
from pose_detector import (  # noqa: E402
    LandmarkListAdapter,
    NormalizedLandmarkPoint,
    PoseDetectionResult,
    adapt_pose_landmarks,
)
from pose_schema import PoseLandmark  # noqa: E402


def _full_standing_landmarks(
    *,
    visibility: float = 0.95,
) -> LandmarkListAdapter:
    """Synthetic standing pose with usable knee and push-up joints."""
    coords = {
        PoseLandmark.LEFT_SHOULDER: (0.40, 0.30),
        PoseLandmark.RIGHT_SHOULDER: (0.60, 0.30),
        PoseLandmark.LEFT_ELBOW: (0.35, 0.45),
        PoseLandmark.RIGHT_ELBOW: (0.65, 0.45),
        PoseLandmark.LEFT_WRIST: (0.32, 0.60),
        PoseLandmark.RIGHT_WRIST: (0.68, 0.60),
        PoseLandmark.LEFT_HIP: (0.42, 0.55),
        PoseLandmark.RIGHT_HIP: (0.58, 0.55),
        PoseLandmark.LEFT_KNEE: (0.42, 0.75),
        PoseLandmark.RIGHT_KNEE: (0.58, 0.75),
        PoseLandmark.LEFT_ANKLE: (0.42, 0.95),
        PoseLandmark.RIGHT_ANKLE: (0.58, 0.95),
    }
    points: list[NormalizedLandmarkPoint] = []
    for i in range(33):
        x, y = coords.get(PoseLandmark(i), (0.5, 0.5))
        points.append(
            NormalizedLandmarkPoint(x=x, y=y, z=0.0, visibility=visibility)
        )
    return LandmarkListAdapter(landmark=points)


def test_adapter_works_with_angle_utils_knee():
    plm = _full_standing_landmarks()
    angles = calculate_knee_angles(plm, PoseLandmark, 640, 480)
    assert angles["average"] is not None
    assert angles["left"] is not None
    assert angles["right"] is not None


def test_adapter_works_with_pushup_angles_without_mp_solutions():
    plm = _full_standing_landmarks()
    angles = calculate_pushup_angles(plm, 640, 480)
    assert angles["avg_elbow"] is not None
    assert angles["left_elbow"] is not None


def test_pose_not_detected_returns_none_landmarks():
    result = PoseDetectionResult(
        landmarks=None,
        world_landmarks=None,
        pose_detected=False,
    )
    assert result.landmarks is None
    assert result.world_landmarks is None
    assert result.pose_detected is False
    assert calculate_pose_confidence(result.landmarks, [PoseLandmark.LEFT_KNEE]) == 0.0
    assert calculate_pushup_angles(result.landmarks, 640, 480)["avg_elbow"] is None


def test_adapt_pose_landmarks_from_raw_tasks_like_objects():
    raw = [
        SimpleNamespace(x=0.1, y=0.2, z=0.3, visibility=0.8, presence=0.9)
        for _ in range(33)
    ]
    adapted = adapt_pose_landmarks(raw)
    assert adapted is not None
    assert len(adapted.landmark) == 33
    assert adapted.landmark[0].x == 0.1
    assert adapted.landmark[0].visibility == 0.8


def test_adapt_falls_back_to_presence():
    raw = [SimpleNamespace(x=0.1, y=0.2, z=0.0, presence=0.7)]
    adapted = adapt_pose_landmarks(raw)
    assert adapted is not None
    assert adapted.landmark[0].visibility == 0.7
