"""Front-facing camera support for squat analysis.

Seen from the front, the 2D hip-knee-ankle angle barely changes while the user
squats (the thigh points at the camera), so the side-view state machine misses
reps. When the session is filmed from the front this module:

* replaces the 2D knee/hip angles with 3D angles from MediaPipe world
  landmarks, rescaled so the user's own standing pose reads ~178 deg
  (world landmarks rarely report a fully straight leg);
* measures knee tracking, which is only visible from the front:
  - ``knee_valgus``: a knee collapses inside its ankle while squatting;
  - ``knee_lateral_shift``: both knees drift to the same side.

Side-view sessions are untouched: ``update`` returns ``None`` for them.
"""

from __future__ import annotations

import math
from collections import deque
from typing import Any

# Landmark indices (MediaPipe Pose).
L_SHOULDER, R_SHOULDER = 11, 12
L_HIP, R_HIP = 23, 24
L_KNEE, R_KNEE = 25, 26
L_ANKLE, R_ANKLE = 27, 28

# View detection: shoulders look wide relative to torso height from the front
# (~0.6-0.8 standing) and narrow from the side (~0.1-0.3).
FRONTAL_SHOULDER_TORSO_RATIO = 0.45
FRONTAL_HIP_TORSO_RATIO = 0.22
VIEW_LOCK_FRAMES = 10
VIEW_FRONTAL_SHARE = 0.7

# Standing calibration of 3D angles.
STANDING_TARGET_ANGLE = 178.0
BASELINE_HISTORY = 90
BASELINE_MIN_SAMPLES = 8
BASELINE_PERCENTILE = 0.9
DEFAULT_KNEE_BASELINE = 165.0
DEFAULT_HIP_BASELINE = 170.0
MIN_BASELINE = 140.0

# Knee tracking (offsets are normalized by ankle width; + = knee outside ankle).
TRACKING_GATE_KNEE_ANGLE = 150.0  # only judge knees while actually squatting
VALGUS_MAX_OUTWARD = -0.05
LATERAL_SHIFT_MIN = 0.18
MIN_ANKLE_WIDTH_PX = 8.0


def _angle(a: tuple[float, ...], b: tuple[float, ...], c: tuple[float, ...]) -> float | None:
    v1 = [a[i] - b[i] for i in range(len(a))]
    v2 = [c[i] - b[i] for i in range(len(c))]
    n1 = math.sqrt(sum(x * x for x in v1))
    n2 = math.sqrt(sum(x * x for x in v2))
    if n1 < 1e-6 or n2 < 1e-6:
        return None
    cos = sum(v1[i] * v2[i] for i in range(len(v1))) / (n1 * n2)
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def _point3(world: Any, idx: int) -> tuple[float, float, float]:
    p = world[idx]
    return (float(p.x), float(p.y), float(p.z))


class _Baseline:
    """Rolling high percentile of an angle = the user's standing value."""

    def __init__(self, default: float) -> None:
        self._values: deque[float] = deque(maxlen=BASELINE_HISTORY)
        self._default = default

    def add(self, value: float) -> None:
        self._values.append(value)

    def value(self) -> float:
        if len(self._values) < BASELINE_MIN_SAMPLES:
            return self._default
        ordered = sorted(self._values)
        k = min(len(ordered) - 1, int(BASELINE_PERCENTILE * (len(ordered) - 1)))
        return max(MIN_BASELINE, ordered[k])

    def calibrate(self, raw: float) -> float:
        return min(180.0, raw * STANDING_TARGET_ANGLE / self.value())


class FrontalSquatTracker:
    def __init__(self) -> None:
        self._votes: list[bool] = []
        self.view: str | None = None  # "frontal" | "side" once locked
        self._knee = {"left": _Baseline(DEFAULT_KNEE_BASELINE), "right": _Baseline(DEFAULT_KNEE_BASELINE)}
        self._hip = {"left": _Baseline(DEFAULT_HIP_BASELINE), "right": _Baseline(DEFAULT_HIP_BASELINE)}

    def _vote(self, lm: Any, w: int, h: int) -> None:
        if self.view is not None:
            return
        sx = abs(lm[L_SHOULDER].x - lm[R_SHOULDER].x) * w
        hx = abs(lm[L_HIP].x - lm[R_HIP].x) * w
        torso = abs(
            (lm[L_HIP].y + lm[R_HIP].y) / 2 - (lm[L_SHOULDER].y + lm[R_SHOULDER].y) / 2
        ) * h
        if torso < 1.0:
            return
        self._votes.append(
            sx / torso >= FRONTAL_SHOULDER_TORSO_RATIO
            and hx / torso >= FRONTAL_HIP_TORSO_RATIO
        )
        if len(self._votes) >= VIEW_LOCK_FRAMES:
            share = sum(self._votes) / len(self._votes)
            self.view = "frontal" if share >= VIEW_FRONTAL_SHARE else "side"

    def update(
        self,
        landmarks: Any,
        world_landmarks: Any,
        image_width: int,
        image_height: int,
    ) -> dict[str, Any] | None:
        """Return frontal metrics for this frame, or None outside frontal mode."""
        try:
            lm = landmarks.landmark
        except AttributeError:
            return None
        if lm is None or len(lm) <= R_ANKLE:
            return None
        self._vote(lm, image_width, image_height)
        if self.view != "frontal" or not world_landmarks or len(world_landmarks) <= R_ANKLE:
            return None

        raw: dict[str, float | None] = {}
        for side, (sh, hp, kn, an) in {
            "left": (L_SHOULDER, L_HIP, L_KNEE, L_ANKLE),
            "right": (R_SHOULDER, R_HIP, R_KNEE, R_ANKLE),
        }.items():
            raw[f"{side}_knee"] = _angle(
                _point3(world_landmarks, hp), _point3(world_landmarks, kn), _point3(world_landmarks, an)
            )
            raw[f"{side}_hip"] = _angle(
                _point3(world_landmarks, sh), _point3(world_landmarks, hp), _point3(world_landmarks, kn)
            )
        if any(v is None for v in raw.values()):
            return None

        knee: dict[str, float] = {}
        hip: dict[str, float] = {}
        for side in ("left", "right"):
            self._knee[side].add(float(raw[f"{side}_knee"]))
            self._hip[side].add(float(raw[f"{side}_hip"]))
            knee[side] = self._knee[side].calibrate(float(raw[f"{side}_knee"]))
            hip[side] = self._hip[side].calibrate(float(raw[f"{side}_hip"]))

        # Knee tracking in image space (x only), relative to each ankle.
        w = float(image_width)
        lax, rax = lm[L_ANKLE].x * w, lm[R_ANKLE].x * w
        ankle_width = abs(lax - rax)
        tracking: dict[str, float] | None = None
        if ankle_width >= MIN_ANKLE_WIDTH_PX:
            sign = 1.0 if lax > rax else -1.0  # direction "outward" for the left leg
            out_left = (lm[L_KNEE].x * w - lax) * sign / ankle_width
            out_right = (rax - lm[R_KNEE].x * w) * sign / ankle_width
            tracking = {
                "out_left": round(out_left, 3),
                "out_right": round(out_right, 3),
                # Same-direction drift of both knees (sign = direction).
                "shift": round((out_left - out_right) / 2.0, 3),
            }

        # Depth follows the more-bent leg: an uneven squat still counts as an
        # attempt instead of disappearing behind the straighter leg.
        depth_knee = min(knee["left"], knee["right"])
        depth_hip = min(hip["left"], hip["right"])
        return {
            "left": knee["left"],
            "right": knee["right"],
            "average": depth_knee,
            "left_hip": hip["left"],
            "right_hip": hip["right"],
            "avg_hip": depth_hip,
            "tracking": tracking,
        }


def knee_tracking_errors(tracking: dict[str, float] | None, knee_angle: float) -> list[str]:
    """Form errors visible in this frame (only while squatting)."""
    if tracking is None or knee_angle >= TRACKING_GATE_KNEE_ANGLE:
        return []
    if abs(tracking["shift"]) >= LATERAL_SHIFT_MIN:
        # A shifted pair also puts one knee inside its ankle; report the cause.
        return ["knee_lateral_shift"]
    if min(tracking["out_left"], tracking["out_right"]) <= VALGUS_MAX_OUTWARD:
        return ["knee_valgus"]
    return []
