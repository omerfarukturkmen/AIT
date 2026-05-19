"""Joint angle helpers (to be implemented)."""

from __future__ import annotations

import math
from typing import Any, Protocol, Sequence

VISIBILITY_THRESHOLD = 0.5


class _LandmarkList(Protocol):
    """Minimal protocol for MediaPipe pose_landmarks.landmark access."""

    landmark: Any


def angle_between_points(
    a: Sequence[float],
    b: Sequence[float],
    c: Sequence[float],
) -> float:
    """Return angle ABC at vertex B in degrees."""
    ax, ay = float(a[0]), float(a[1])
    bx, by = float(b[0]), float(b[1])
    cx, cy = float(c[0]), float(c[1])
    v1x, v1y = ax - bx, ay - by
    v2x, v2y = cx - bx, cy - by
    dot = v1x * v2x + v1y * v2y
    n1 = math.hypot(v1x, v1y)
    n2 = math.hypot(v2x, v2y)
    if n1 == 0 or n2 == 0:
        return 0.0
    cos_ = max(-1.0, min(1.0, dot / (n1 * n2)))
    return math.degrees(math.acos(cos_))


def _landmark_index(landmark_enum: Any) -> int:
    v = getattr(landmark_enum, "value", landmark_enum)
    return int(v)


def get_landmark_point(
    landmarks: _LandmarkList,
    landmark_enum: Any,
    image_width: int,
    image_height: int,
) -> dict[str, int | float]:
    """Convert a MediaPipe landmark to pixel coordinates and visibility."""
    p = landmarks.landmark[_landmark_index(landmark_enum)]
    return {
        "x": int(round(float(p.x) * image_width)),
        "y": int(round(float(p.y) * image_height)),
        "visibility": float(p.visibility),
    }


def calculate_knee_angles(
    landmarks: _LandmarkList,
    pose_landmarks_enum: Any,
    image_width: int,
    image_height: int,
) -> dict[str, float | None]:
    """Compute left/right/average knee angles (hip–knee–ankle at knee).

    Returns None for a side if any of its three points is missing or below
    visibility threshold (0.5). Average is mean of available sides, or None.
    """
    L = pose_landmarks_enum

    def side_angle(
        hip_name: Any,
        knee_name: Any,
        ankle_name: Any,
    ) -> float | None:
        hip = get_landmark_point(landmarks, hip_name, image_width, image_height)
        knee = get_landmark_point(landmarks, knee_name, image_width, image_height)
        ankle = get_landmark_point(landmarks, ankle_name, image_width, image_height)
        if (
            min(hip["visibility"], knee["visibility"], ankle["visibility"])
            < VISIBILITY_THRESHOLD
        ):
            return None
        return angle_between_points(
            (hip["x"], hip["y"]),
            (knee["x"], knee["y"]),
            (ankle["x"], ankle["y"]),
        )

    left = side_angle(L.LEFT_HIP, L.LEFT_KNEE, L.LEFT_ANKLE)
    right = side_angle(L.RIGHT_HIP, L.RIGHT_KNEE, L.RIGHT_ANKLE)

    if left is not None and right is not None:
        average = (left + right) / 2.0
    elif left is not None:
        average = left
    elif right is not None:
        average = right
    else:
        average = None

    return {"left": left, "right": right, "average": average}
