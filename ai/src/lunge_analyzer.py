"""Lunge landmark / angle analysis scaffold (frame-level only).

Provides deterministic knee and hip angle extraction for both sides.
Does **not** implement rep counting, state machine, scoring, or feedback.
"""

from __future__ import annotations

from typing import Any

from angle_utils import calculate_hip_angles, calculate_knee_angles
from pose_schema import PoseLandmark

# Required landmarks for bilateral lunge knee + hip chains (scaffold).
LUNGE_REQUIRED_LANDMARKS: tuple[PoseLandmark, ...] = (
    PoseLandmark.LEFT_SHOULDER,
    PoseLandmark.RIGHT_SHOULDER,
    PoseLandmark.LEFT_HIP,
    PoseLandmark.RIGHT_HIP,
    PoseLandmark.LEFT_KNEE,
    PoseLandmark.RIGHT_KNEE,
    PoseLandmark.LEFT_ANKLE,
    PoseLandmark.RIGHT_ANKLE,
)


def lunge_pose_landmark_indices(pose_landmark_enum: object = PoseLandmark) -> tuple[Any, ...]:
    """Landmark indices used for future lunge pose-confidence scoring."""
    L = pose_landmark_enum
    return (
        L.LEFT_SHOULDER,
        L.RIGHT_SHOULDER,
        L.LEFT_HIP,
        L.RIGHT_HIP,
        L.LEFT_KNEE,
        L.RIGHT_KNEE,
        L.LEFT_ANKLE,
        L.RIGHT_ANKLE,
    )


def _empty_lunge_angles(*, landmarks_valid: bool = False) -> dict[str, Any]:
    return {
        "left_knee_angle": None,
        "right_knee_angle": None,
        "left_hip_angle": None,
        "right_hip_angle": None,
        "landmarks_valid": bool(landmarks_valid),
        "left_knee_confidence": 0.0,
        "right_knee_confidence": 0.0,
        "left_hip_confidence": 0.0,
        "right_hip_confidence": 0.0,
    }


def extract_lunge_angles(
    landmarks: Any,
    pose_landmarks_enum: Any = PoseLandmark,
    image_width: int = 1,
    image_height: int = 1,
) -> dict[str, Any]:
    """Extract bilateral knee and hip angles for one lunge frame.

    Stateless and deterministic. Reuses shared ``angle_utils`` knee/hip helpers
    (same 2D pixel coordinate pipeline as squat/push-up).

    Returns:
        Internal frame dict with ``left_knee_angle``, ``right_knee_angle``,
        ``left_hip_angle``, ``right_hip_angle``, ``landmarks_valid``, and
        per-side confidence fields. Angles are ``None`` when landmarks are
        missing or below the shared visibility thresholds.
    """
    if landmarks is None:
        return _empty_lunge_angles(landmarks_valid=False)

    try:
        _ = landmarks.landmark
    except AttributeError:
        return _empty_lunge_angles(landmarks_valid=False)

    width = int(image_width) if image_width else 1
    height = int(image_height) if image_height else 1
    if width <= 0:
        width = 1
    if height <= 0:
        height = 1

    try:
        knees = calculate_knee_angles(
            landmarks, pose_landmarks_enum, width, height
        )
        hips = calculate_hip_angles(
            landmarks, pose_landmarks_enum, width, height
        )
    except (AttributeError, IndexError, TypeError, ValueError):
        return _empty_lunge_angles(landmarks_valid=False)

    left_knee = knees.get("left")
    right_knee = knees.get("right")
    left_hip = hips.get("left")
    right_hip = hips.get("right")

    landmarks_valid = any(
        value is not None for value in (left_knee, right_knee, left_hip, right_hip)
    )

    return {
        "left_knee_angle": left_knee,
        "right_knee_angle": right_knee,
        "left_hip_angle": left_hip,
        "right_hip_angle": right_hip,
        "landmarks_valid": landmarks_valid,
        "left_knee_confidence": float(knees.get("left_confidence") or 0.0),
        "right_knee_confidence": float(knees.get("right_confidence") or 0.0),
        "left_hip_confidence": float(hips.get("left_confidence") or 0.0),
        "right_hip_confidence": float(hips.get("right_confidence") or 0.0),
    }


# Alias matching task naming options.
analyze_lunge_landmarks = extract_lunge_angles
