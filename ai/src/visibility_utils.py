"""Exercise-specific required-landmark visibility evaluation."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from pose_schema import PoseLandmark

MIN_REQUIRED_LANDMARK_VISIBILITY = 0.60

VISIBILITY_WARNING = "Required body landmarks are not clearly visible"
VISIBILITY_WARNING_HINT = "Make sure the required body parts are visible in the frame"
ANALYSIS_STATUS_INSUFFICIENT_VISIBILITY = "insufficient_landmark_visibility"

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

_EXERCISE_SIDE_SETS: dict[str, tuple[tuple[PoseLandmark, ...], tuple[PoseLandmark, ...]]] = {
    "squat": (_SQUAT_LEFT, _SQUAT_RIGHT),
    "pushup": (_PUSHUP_LEFT, _PUSHUP_RIGHT),
}


def sanitize_visibility(value: Any) -> float | None:
    """Return visibility in [0, 1] or None when unreliable."""
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(out):
        return None
    if out < 0.0 or out > 1.0:
        return None
    return out


def _landmark_name(index: PoseLandmark) -> str:
    return PoseLandmark(index).name


def _read_landmark_visibility(landmarks: Any, index: PoseLandmark) -> float | None:
    if landmarks is None:
        return None
    try:
        point = landmarks.landmark[int(index)]
    except (AttributeError, IndexError, TypeError, ValueError):
        return None
    return sanitize_visibility(getattr(point, "visibility", None))


def _evaluate_side(
    landmarks: Any,
    indices: tuple[PoseLandmark, ...],
    *,
    threshold: float,
) -> tuple[bool, float | None, float | None, list[str]]:
    values: list[float] = []
    low_names: list[str] = []
    for index in indices:
        vis = _read_landmark_visibility(landmarks, index)
        name = _landmark_name(index)
        if vis is None or vis < threshold:
            low_names.append(name)
        if vis is not None:
            values.append(vis)
    if low_names:
        min_v = min(values) if values else None
        mean_v = sum(values) / len(values) if values else None
        return False, min_v, mean_v, low_names
    if not values:
        return False, None, None, [_landmark_name(i) for i in indices]
    return True, min(values), sum(values) / len(values), []


@dataclass
class LandmarkVisibilityResult:
    is_usable: bool
    exercise_type: str
    selected_side: str
    min_visibility: float | None
    mean_visibility: float | None
    low_visibility_landmarks: list[str] = field(default_factory=list)
    required_landmarks: list[str] = field(default_factory=list)
    reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "is_usable": self.is_usable,
            "exercise_type": self.exercise_type,
            "selected_side": self.selected_side,
            "min_visibility": self.min_visibility,
            "mean_visibility": self.mean_visibility,
            "low_visibility_landmarks": list(self.low_visibility_landmarks),
            "required_landmarks": list(self.required_landmarks),
            "reason": self.reason,
        }


def evaluate_exercise_landmark_visibility(
    landmarks: Any,
    exercise_type: str,
    *,
    threshold: float = MIN_REQUIRED_LANDMARK_VISIBILITY,
) -> LandmarkVisibilityResult:
    """Return whether at least one complete side chain is visibility-reliable."""
    exercise_key = str(exercise_type or "").strip().lower()
    side_sets = _EXERCISE_SIDE_SETS.get(exercise_key)
    if side_sets is None:
        return LandmarkVisibilityResult(
            is_usable=False,
            exercise_type=exercise_key or "unknown",
            selected_side="unknown",
            min_visibility=None,
            mean_visibility=None,
            reason=f"unsupported exercise_type: {exercise_type}",
        )

    left_indices, right_indices = side_sets
    left_ok, left_min, left_mean, left_low = _evaluate_side(
        landmarks, left_indices, threshold=threshold
    )
    right_ok, right_min, right_mean, right_low = _evaluate_side(
        landmarks, right_indices, threshold=threshold
    )

    if left_ok and right_ok:
        mins = [v for v in (left_min, right_min) if v is not None]
        means = [v for v in (left_mean, right_mean) if v is not None]
        required = [_landmark_name(i) for i in left_indices] + [
            _landmark_name(i) for i in right_indices
        ]
        return LandmarkVisibilityResult(
            is_usable=True,
            exercise_type=exercise_key,
            selected_side="both",
            min_visibility=min(mins) if mins else None,
            mean_visibility=sum(means) / len(means) if means else None,
            low_visibility_landmarks=[],
            required_landmarks=required,
            reason=None,
        )

    if left_ok:
        return LandmarkVisibilityResult(
            is_usable=True,
            exercise_type=exercise_key,
            selected_side="left",
            min_visibility=left_min,
            mean_visibility=left_mean,
            low_visibility_landmarks=[],
            required_landmarks=[_landmark_name(i) for i in left_indices],
            reason=None,
        )

    if right_ok:
        return LandmarkVisibilityResult(
            is_usable=True,
            exercise_type=exercise_key,
            selected_side="right",
            min_visibility=right_min,
            mean_visibility=right_mean,
            low_visibility_landmarks=[],
            required_landmarks=[_landmark_name(i) for i in right_indices],
            reason=None,
        )

    low = sorted(set(left_low + right_low))
    values = [
        v
        for v in (
            _read_landmark_visibility(landmarks, i)
            for i in left_indices + right_indices
        )
        if v is not None
    ]
    return LandmarkVisibilityResult(
        is_usable=False,
        exercise_type=exercise_key,
        selected_side="unknown",
        min_visibility=min(values) if values else None,
        mean_visibility=sum(values) / len(values) if values else None,
        low_visibility_landmarks=low,
        required_landmarks=[_landmark_name(i) for i in left_indices + right_indices],
        reason="required landmarks below visibility threshold",
    )


def visibility_feedback_messages() -> list[str]:
    """Canonical user-facing visibility warnings (deduplicated)."""
    return [VISIBILITY_WARNING, VISIBILITY_WARNING_HINT]
