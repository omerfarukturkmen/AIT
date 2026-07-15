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
) -> dict[str, int | float] | None:
    """Convert a MediaPipe landmark to pixel coordinates and visibility."""
    try:
        idx = _landmark_index(landmark_enum)
        lm_list = landmarks.landmark
        if idx < 0 or idx >= len(lm_list):
            return None
        p = lm_list[idx]
        return {
            "x": int(round(float(p.x) * image_width)),
            "y": int(round(float(p.y) * image_height)),
            "visibility": float(p.visibility),
        }
    except (AttributeError, IndexError, TypeError, ValueError):
        return None


def average_available_values(values: Sequence[float | None]) -> float | None:
    """Return the mean of non-None values, or None if none are available."""
    available = [float(v) for v in values if v is not None]
    if not available:
        return None
    return sum(available) / len(available)


def _empty_pushup_angles() -> dict[str, float | None]:
    return {
        "left_elbow": None,
        "right_elbow": None,
        "avg_elbow": None,
        "left_shoulder": None,
        "right_shoulder": None,
        "avg_shoulder": None,
        "left_hip": None,
        "right_hip": None,
        "avg_hip": None,
    }


def _pushup_triple_angle(
    landmarks: _LandmarkList,
    landmark_a: Any,
    landmark_b: Any,
    landmark_c: Any,
    image_width: int,
    image_height: int,
) -> float | None:
    """Angle at landmark_b from three pose points; None if unreliable."""
    pa = get_landmark_point(landmarks, landmark_a, image_width, image_height)
    pb = get_landmark_point(landmarks, landmark_b, image_width, image_height)
    pc = get_landmark_point(landmarks, landmark_c, image_width, image_height)
    if pa is None or pb is None or pc is None:
        return None
    if (
        min(pa["visibility"], pb["visibility"], pc["visibility"])
        < VISIBILITY_THRESHOLD
    ):
        return None
    return angle_between_points(
        (pa["x"], pa["y"]),
        (pb["x"], pb["y"]),
        (pc["x"], pc["y"]),
    )


def calculate_pushup_angles(
    landmarks: _LandmarkList | None,
    image_width: int,
    image_height: int,
) -> dict[str, float | None]:
    """Compute elbow, shoulder, and hip alignment angles for push-up analysis."""
    empty = _empty_pushup_angles()
    if landmarks is None:
        return empty

    try:
        import mediapipe as mp

        L = mp.solutions.pose.PoseLandmark
    except (AttributeError, ImportError):
        return empty

    left_elbow = _pushup_triple_angle(
        landmarks, L.LEFT_SHOULDER, L.LEFT_ELBOW, L.LEFT_WRIST, image_width, image_height
    )
    right_elbow = _pushup_triple_angle(
        landmarks, L.RIGHT_SHOULDER, L.RIGHT_ELBOW, L.RIGHT_WRIST, image_width, image_height
    )
    left_shoulder = _pushup_triple_angle(
        landmarks, L.LEFT_HIP, L.LEFT_SHOULDER, L.LEFT_ELBOW, image_width, image_height
    )
    right_shoulder = _pushup_triple_angle(
        landmarks, L.RIGHT_HIP, L.RIGHT_SHOULDER, L.RIGHT_ELBOW, image_width, image_height
    )
    left_hip = _pushup_triple_angle(
        landmarks, L.LEFT_SHOULDER, L.LEFT_HIP, L.LEFT_ANKLE, image_width, image_height
    )
    right_hip = _pushup_triple_angle(
        landmarks, L.RIGHT_SHOULDER, L.RIGHT_HIP, L.RIGHT_ANKLE, image_width, image_height
    )

    return {
        "left_elbow": left_elbow,
        "right_elbow": right_elbow,
        "avg_elbow": average_available_values([left_elbow, right_elbow]),
        "left_shoulder": left_shoulder,
        "right_shoulder": right_shoulder,
        "avg_shoulder": average_available_values([left_shoulder, right_shoulder]),
        "left_hip": left_hip,
        "right_hip": right_hip,
        "avg_hip": average_available_values([left_hip, right_hip]),
    }


SIDE_CONFIDENCE_MIN = 0.55
KNEE_ANGLE_DISAGREE_DEG = 18.0


def _side_knee_measurement(
    landmarks: _LandmarkList,
    hip_enum: Any,
    knee_enum: Any,
    ankle_enum: Any,
    image_width: int,
    image_height: int,
) -> tuple[float | None, float]:
    """Return (angle_or_None, confidence 0–1) for one leg."""
    hip = get_landmark_point(landmarks, hip_enum, image_width, image_height)
    knee = get_landmark_point(landmarks, knee_enum, image_width, image_height)
    ankle = get_landmark_point(landmarks, ankle_enum, image_width, image_height)
    if hip is None or knee is None or ankle is None:
        return None, 0.0
    conf = (
        float(hip["visibility"])
        + float(knee["visibility"])
        + float(ankle["visibility"])
    ) / 3.0
    if conf < SIDE_CONFIDENCE_MIN:
        return None, conf
    if min(hip["visibility"], knee["visibility"], ankle["visibility"]) < VISIBILITY_THRESHOLD:
        return None, conf
    angle = angle_between_points(
        (hip["x"], hip["y"]),
        (knee["x"], knee["y"]),
        (ankle["x"], ankle["y"]),
    )
    return angle, conf


def calculate_knee_angles(
    landmarks: _LandmarkList,
    pose_landmarks_enum: Any,
    image_width: int,
    image_height: int,
) -> dict[str, Any]:
    """Compute left/right knee angles with side-confidence selection.

    selected_side:
      left | right | weighted_average | unavailable
    ``average`` is the selected/combined angle used by squat analysis.
    """
    L = pose_landmarks_enum
    left, left_conf = _side_knee_measurement(
        landmarks, L.LEFT_HIP, L.LEFT_KNEE, L.LEFT_ANKLE, image_width, image_height
    )
    right, right_conf = _side_knee_measurement(
        landmarks, L.RIGHT_HIP, L.RIGHT_KNEE, L.RIGHT_ANKLE, image_width, image_height
    )

    left_ok = left is not None and left_conf >= SIDE_CONFIDENCE_MIN
    right_ok = right is not None and right_conf >= SIDE_CONFIDENCE_MIN

    selected_side = "unavailable"
    selected: float | None = None
    selected_conf = 0.0

    if left_ok and not right_ok:
        selected_side = "left"
        selected = float(left)
        selected_conf = left_conf
    elif right_ok and not left_ok:
        selected_side = "right"
        selected = float(right)
        selected_conf = right_conf
    elif left_ok and right_ok:
        diff = abs(float(left) - float(right))
        if diff > KNEE_ANGLE_DISAGREE_DEG:
            if left_conf >= right_conf:
                selected_side = "left"
                selected = float(left)
                selected_conf = left_conf
            else:
                selected_side = "right"
                selected = float(right)
                selected_conf = right_conf
        else:
            selected_side = "weighted_average"
            weight = left_conf + right_conf
            selected = (float(left) * left_conf + float(right) * right_conf) / weight
            selected_conf = weight / 2.0

    return {
        "left": left,
        "right": right,
        "average": selected,
        "selected_side": selected_side,
        "left_confidence": round(left_conf, 4),
        "right_confidence": round(right_conf, 4),
        "selected_confidence": round(selected_conf, 4),
    }


def calculate_torso_lean_angle(
    landmarks: _LandmarkList,
    pose_landmarks_enum: Any,
    image_width: int,
    image_height: int,
) -> float | None:
    """Estimate forward torso lean using the more visible shoulder–hip side.

    Prefer visible side in profile shots instead of blending occluded landmarks.
    """
    L = pose_landmarks_enum
    ls = get_landmark_point(landmarks, L.LEFT_SHOULDER, image_width, image_height)
    rs = get_landmark_point(landmarks, L.RIGHT_SHOULDER, image_width, image_height)
    lh = get_landmark_point(landmarks, L.LEFT_HIP, image_width, image_height)
    rh = get_landmark_point(landmarks, L.RIGHT_HIP, image_width, image_height)

    candidates: list[tuple[float, float, float, float, float]] = []
    if ls is not None and lh is not None:
        conf = (float(ls["visibility"]) + float(lh["visibility"])) / 2.0
        if conf >= SIDE_CONFIDENCE_MIN:
            candidates.append(
                (conf, float(ls["x"]), float(ls["y"]), float(lh["x"]), float(lh["y"]))
            )
    if rs is not None and rh is not None:
        conf = (float(rs["visibility"]) + float(rh["visibility"])) / 2.0
        if conf >= SIDE_CONFIDENCE_MIN:
            candidates.append(
                (conf, float(rs["x"]), float(rs["y"]), float(rh["x"]), float(rh["y"]))
            )

    if not candidates:
        return None

    candidates.sort(key=lambda c: c[0], reverse=True)
    _conf, sx, sy, hx, hy = candidates[0]
    dx = sx - hx
    dy = hy - sy  # image y grows downward
    if dy <= 1.0:
        return None
    return abs(math.degrees(math.atan2(abs(dx), dy)))


def calculate_pose_confidence(landmarks: _LandmarkList | None, landmark_indices: Sequence[Any]) -> float:
    """Return mean visibility (0.0–1.0) for the given landmark indices."""
    if landmarks is None:
        return 0.0
    try:
        lm_list = landmarks.landmark
    except AttributeError:
        return 0.0

    visibilities: list[float] = []
    for idx_item in landmark_indices:
        try:
            idx = _landmark_index(idx_item)
            if idx < 0 or idx >= len(lm_list):
                visibilities.append(0.0)
                continue
            p = lm_list[idx]
            vis = getattr(p, "visibility", None)
            visibilities.append(float(vis) if vis is not None else 0.0)
        except (AttributeError, IndexError, TypeError, ValueError):
            visibilities.append(0.0)

    if not visibilities:
        return 0.0
    avg = sum(visibilities) / len(visibilities)
    return max(0.0, min(1.0, avg))


def estimate_body_bbox(
    landmarks: _LandmarkList | None,
    frame_width: int,
    frame_height: int,
) -> tuple[int, int, int, int] | None:
    """Bounding box (min_x, min_y, max_x, max_y) from visible landmarks."""
    if landmarks is None:
        return None
    try:
        lm_list = landmarks.landmark
    except AttributeError:
        return None

    xs: list[float] = []
    ys: list[float] = []
    for p in lm_list:
        vis = getattr(p, "visibility", None)
        if vis is None or float(vis) < VISIBILITY_THRESHOLD:
            continue
        try:
            xs.append(float(p.x) * frame_width)
            ys.append(float(p.y) * frame_height)
        except (AttributeError, TypeError, ValueError):
            continue

    if len(xs) < 2 or len(ys) < 2:
        return None

    return (int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))


def check_camera_distance(
    body_bbox: tuple[int, int, int, int] | None,
    frame_height: int,
) -> dict[str, Any]:
    """Estimate whether the subject is too far from or too close to the camera."""
    if body_bbox is None or frame_height <= 0:
        return {
            "status": "unknown",
            "message": "Camera distance unknown",
            "ratio": None,
        }

    _min_x, min_y, _max_x, max_y = body_bbox
    bbox_height = max_y - min_y
    ratio = bbox_height / float(frame_height)

    if ratio < 0.35:
        return {
            "status": "too_far",
            "message": "Move closer to camera",
            "ratio": ratio,
        }
    if ratio > 0.90:
        return {
            "status": "too_close",
            "message": "Move away from camera",
            "ratio": ratio,
        }
    return {
        "status": "good",
        "message": "Camera distance OK",
        "ratio": ratio,
    }

