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
    """Return the mean of non-None finite values, or None if none are available."""
    available: list[float] = []
    for v in values:
        sanitized = sanitize_angle_value(v)
        if sanitized is not None:
            available.append(sanitized)
    if not available:
        return None
    return sum(available) / len(available)


def sanitize_angle_value(value: Any) -> float | None:
    """Convert to float; reject None, NaN, and inf."""
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if out != out or out in (float("inf"), float("-inf")):
        return None
    return out


# Minimum shoulder–ankle distance in pixels before body-line math is reliable.
_MIN_BODY_LINE_LENGTH_PX = 8.0
_ALIGNMENT_SIDE_CONF_GAP = 0.08


def _empty_pushup_angles() -> dict[str, Any]:
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
        "body_alignment_angle": None,
        "body_line_offset": None,
        "alignment_side": "unknown",
    }


def _point_mean_visibility(points: Sequence[dict[str, int | float]]) -> float:
    if not points:
        return 0.0
    return sum(float(p["visibility"]) for p in points) / float(len(points))


def _signed_body_line_offset(
    shoulder: dict[str, int | float],
    hip: dict[str, int | float],
    ankle: dict[str, int | float],
) -> float | None:
    """Normalized hip offset from shoulder–ankle line.

    Positive → hip displaced toward image +y (down / sagging).
    Negative → hip displaced toward image -y (up / too high).
    Sign is corrected so facing left vs right does not invert meaning.
    """
    try:
        sx, sy = float(shoulder["x"]), float(shoulder["y"])
        hx, hy = float(hip["x"]), float(hip["y"])
        ax, ay = float(ankle["x"]), float(ankle["y"])
    except (KeyError, TypeError, ValueError):
        return None

    dx = ax - sx
    dy = ay - sy
    length = math.hypot(dx, dy)
    if length < _MIN_BODY_LINE_LENGTH_PX:
        return None

    # Dimensionless signed distance of hip relative to directed S→A.
    cross = (hx - sx) * dy - (hy - sy) * dx
    raw = cross / (length * length)

    # Same formula for an image-down unit step from the shoulder.
    # down_raw > 0 means positive raw already points "down" in the image.
    down_raw = -dx / (length * length)
    if abs(down_raw) < 1e-12:
        # Nearly vertical body line: fall back to image-vertical residual.
        t = ((hx - sx) * dx + (hy - sy) * dy) / (length * length)
        py = sy + t * dy
        return (hy - py) / length

    if down_raw < 0.0:
        raw = -raw
    return raw


def _side_body_alignment(
    landmarks: _LandmarkList,
    shoulder_enum: Any,
    hip_enum: Any,
    knee_enum: Any,
    ankle_enum: Any,
    image_width: int,
    image_height: int,
) -> tuple[float | None, float | None, float]:
    """Return (shoulder_hip_knee_angle, body_line_offset, confidence)."""
    shoulder = get_landmark_point(landmarks, shoulder_enum, image_width, image_height)
    hip = get_landmark_point(landmarks, hip_enum, image_width, image_height)
    knee = get_landmark_point(landmarks, knee_enum, image_width, image_height)
    ankle = get_landmark_point(landmarks, ankle_enum, image_width, image_height)
    if shoulder is None or hip is None or knee is None or ankle is None:
        return None, None, 0.0

    points = [shoulder, hip, knee, ankle]
    conf = _point_mean_visibility(points)
    if (
        min(float(p["visibility"]) for p in points) < VISIBILITY_THRESHOLD
        or conf < SIDE_CONFIDENCE_MIN
    ):
        return None, None, conf

    angle = angle_between_points(
        (shoulder["x"], shoulder["y"]),
        (hip["x"], hip["y"]),
        (knee["x"], knee["y"]),
    )
    offset = _signed_body_line_offset(shoulder, hip, ankle)
    if offset is None:
        return None, None, conf
    return float(angle), float(offset), conf


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


SIDE_CONFIDENCE_MIN = 0.55
KNEE_ANGLE_DISAGREE_DEG = 18.0


def calculate_pushup_angles(
    landmarks: _LandmarkList | None,
    image_width: int,
    image_height: int,
) -> dict[str, Any]:
    """Compute elbow/shoulder/hip angles plus body-line alignment metrics."""
    empty = _empty_pushup_angles()
    if landmarks is None:
        return empty

    try:
        from pose_schema import PoseLandmark as L

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

        left_angle, left_offset, left_conf = _side_body_alignment(
            landmarks,
            L.LEFT_SHOULDER,
            L.LEFT_HIP,
            L.LEFT_KNEE,
            L.LEFT_ANKLE,
            image_width,
            image_height,
        )
        right_angle, right_offset, right_conf = _side_body_alignment(
            landmarks,
            L.RIGHT_SHOULDER,
            L.RIGHT_HIP,
            L.RIGHT_KNEE,
            L.RIGHT_ANKLE,
            image_width,
            image_height,
        )

        body_alignment_angle: float | None = None
        body_line_offset: float | None = None
        alignment_side = "unknown"

        left_ok = left_angle is not None and left_offset is not None
        right_ok = right_angle is not None and right_offset is not None

        if left_ok and right_ok:
            if abs(left_conf - right_conf) < _ALIGNMENT_SIDE_CONF_GAP:
                body_alignment_angle = (float(left_angle) + float(right_angle)) / 2.0
                body_line_offset = (float(left_offset) + float(right_offset)) / 2.0
                alignment_side = "both"
            elif left_conf >= right_conf:
                body_alignment_angle = float(left_angle)
                body_line_offset = float(left_offset)
                alignment_side = "left"
            else:
                body_alignment_angle = float(right_angle)
                body_line_offset = float(right_offset)
                alignment_side = "right"
        elif left_ok:
            body_alignment_angle = float(left_angle)
            body_line_offset = float(left_offset)
            alignment_side = "left"
        elif right_ok:
            body_alignment_angle = float(right_angle)
            body_line_offset = float(right_offset)
            alignment_side = "right"

        return {
            "left_elbow": sanitize_angle_value(left_elbow),
            "right_elbow": sanitize_angle_value(right_elbow),
            "avg_elbow": average_available_values([left_elbow, right_elbow]),
            "left_shoulder": sanitize_angle_value(left_shoulder),
            "right_shoulder": sanitize_angle_value(right_shoulder),
            "avg_shoulder": average_available_values([left_shoulder, right_shoulder]),
            "left_hip": sanitize_angle_value(left_hip),
            "right_hip": sanitize_angle_value(right_hip),
            "avg_hip": average_available_values([left_hip, right_hip]),
            "body_alignment_angle": sanitize_angle_value(body_alignment_angle),
            "body_line_offset": sanitize_angle_value(body_line_offset),
            "alignment_side": alignment_side,
        }
    except Exception:
        return empty


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


def _clamp_angle_deg(angle: float) -> float:
    if angle != angle:  # NaN
        return 0.0
    return max(0.0, min(180.0, float(angle)))


def _side_hip_measurement(
    landmarks: _LandmarkList,
    shoulder_enum: Any,
    hip_enum: Any,
    knee_enum: Any,
    image_width: int,
    image_height: int,
) -> tuple[float | None, float]:
    """Return (shoulder–hip–knee angle at hip, confidence) for one side."""
    shoulder = get_landmark_point(landmarks, shoulder_enum, image_width, image_height)
    hip = get_landmark_point(landmarks, hip_enum, image_width, image_height)
    knee = get_landmark_point(landmarks, knee_enum, image_width, image_height)
    if shoulder is None or hip is None or knee is None:
        return None, 0.0
    conf = (
        float(shoulder["visibility"])
        + float(hip["visibility"])
        + float(knee["visibility"])
    ) / 3.0
    if conf < SIDE_CONFIDENCE_MIN:
        return None, conf
    if (
        min(shoulder["visibility"], hip["visibility"], knee["visibility"])
        < VISIBILITY_THRESHOLD
    ):
        return None, conf
    angle = _clamp_angle_deg(
        angle_between_points(
            (shoulder["x"], shoulder["y"]),
            (hip["x"], hip["y"]),
            (knee["x"], knee["y"]),
        )
    )
    return angle, conf


def calculate_hip_angles(
    landmarks: _LandmarkList,
    pose_landmarks_enum: Any,
    image_width: int,
    image_height: int,
) -> dict[str, Any]:
    """Compute left/right hip flexion angles (shoulder → hip → knee at hip vertex)."""
    L = pose_landmarks_enum
    left, left_conf = _side_hip_measurement(
        landmarks,
        L.LEFT_SHOULDER,
        L.LEFT_HIP,
        L.LEFT_KNEE,
        image_width,
        image_height,
    )
    right, right_conf = _side_hip_measurement(
        landmarks,
        L.RIGHT_SHOULDER,
        L.RIGHT_HIP,
        L.RIGHT_KNEE,
        image_width,
        image_height,
    )

    left_ok = left is not None and left_conf >= SIDE_CONFIDENCE_MIN
    right_ok = right is not None and right_conf >= SIDE_CONFIDENCE_MIN

    selected_side = "unknown"
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
            selected_side = "both"
            weight = left_conf + right_conf
            selected = (float(left) * left_conf + float(right) * right_conf) / weight
            selected_conf = weight / 2.0

    avg_hip = selected
    return {
        "left": left,
        "right": right,
        "left_hip": left,
        "right_hip": right,
        "average": avg_hip,
        "avg_hip": avg_hip,
        "selected_hip": selected,
        "selected_side": selected_side,
        "left_confidence": round(left_conf, 4),
        "right_confidence": round(right_conf, 4),
        "left_visibility": round(left_conf, 4),
        "right_visibility": round(right_conf, 4),
        "selected_confidence": round(selected_conf, 4),
    }


def calculate_torso_lean_angle(
    landmarks: _LandmarkList,
    pose_landmarks_enum: Any,
    image_width: int,
    image_height: int,
) -> float | None:
    """Estimate torso lean from vertical (0° ≈ upright; larger = more lean).

    Prefer shoulder/hip midpoints when both sides are reliable; otherwise fall
    back to the more visible single side (legacy behaviour).
    """
    L = pose_landmarks_enum
    ls = get_landmark_point(landmarks, L.LEFT_SHOULDER, image_width, image_height)
    rs = get_landmark_point(landmarks, L.RIGHT_SHOULDER, image_width, image_height)
    lh = get_landmark_point(landmarks, L.LEFT_HIP, image_width, image_height)
    rh = get_landmark_point(landmarks, L.RIGHT_HIP, image_width, image_height)

    if ls is not None and rs is not None and lh is not None and rh is not None:
        vis = [
            float(ls["visibility"]),
            float(rs["visibility"]),
            float(lh["visibility"]),
            float(rh["visibility"]),
        ]
        if min(vis) >= VISIBILITY_THRESHOLD and sum(vis) / 4.0 >= SIDE_CONFIDENCE_MIN:
            sx = (float(ls["x"]) + float(rs["x"])) / 2.0
            sy = (float(ls["y"]) + float(rs["y"])) / 2.0
            hx = (float(lh["x"]) + float(rh["x"])) / 2.0
            hy = (float(lh["y"]) + float(rh["y"])) / 2.0
            dx = sx - hx
            dy = hy - sy
            if dy > 1.0:
                return abs(math.degrees(math.atan2(abs(dx), dy)))

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


def build_squat_frame_metrics(
    landmarks: _LandmarkList,
    pose_landmarks_enum: Any,
    image_width: int,
    image_height: int,
) -> dict[str, Any]:
    """Combine knee, hip, and torso metrics for one squat analysis frame."""
    knee = calculate_knee_angles(
        landmarks, pose_landmarks_enum, image_width, image_height
    )
    hip = calculate_hip_angles(
        landmarks, pose_landmarks_enum, image_width, image_height
    )
    torso = calculate_torso_lean_angle(
        landmarks, pose_landmarks_enum, image_width, image_height
    )

    avg_knee = knee.get("average")
    avg_hip = hip.get("avg_hip")
    metrics_valid = (
        avg_knee is not None and avg_hip is not None and torso is not None
    )

    return {
        # Legacy knee fields used by SquatAnalyzer state machine
        "left": knee.get("left"),
        "right": knee.get("right"),
        "average": avg_knee,
        "selected_side": knee.get("selected_side"),
        "left_confidence": knee.get("left_confidence"),
        "right_confidence": knee.get("right_confidence"),
        "selected_confidence": knee.get("selected_confidence"),
        # Explicit knee aliases
        "left_knee": knee.get("left"),
        "right_knee": knee.get("right"),
        "avg_knee": avg_knee,
        # Hip metrics
        "left_hip": hip.get("left_hip"),
        "right_hip": hip.get("right_hip"),
        "avg_hip": avg_hip,
        "selected_hip": hip.get("selected_hip"),
        "hip_selected_side": hip.get("selected_side"),
        "left_visibility": knee.get("left_confidence"),
        "right_visibility": knee.get("right_confidence"),
        # Torso
        "torso_lean": torso,
        "torso_lean_deg": torso,
        "metrics_valid": metrics_valid,
    }


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
    frame_width: int | None = None,
) -> dict[str, Any]:
    """Estimate whether the subject framing is too far/close (bbox scale, not metres)."""
    from camera_utils import (
        build_camera_frame_info,
        compute_body_bbox_metrics,
        measure_instant_camera_status,
    )

    if frame_height <= 0 or frame_width is None or frame_width <= 0:
        return build_camera_frame_info(
            status="unknown",
            metrics=compute_body_bbox_metrics(None, 0, 0),
            confirmed=True,
        )

    metrics = compute_body_bbox_metrics(body_bbox, frame_width, frame_height)
    status = measure_instant_camera_status(metrics.get("body_scale"))
    info = build_camera_frame_info(status=status, metrics=metrics, confirmed=True)
    return info

