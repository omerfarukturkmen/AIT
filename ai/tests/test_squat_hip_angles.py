"""Tests for squat hip angles and combined frame metrics."""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from angle_utils import (  # noqa: E402
    _clamp_angle_deg,
    build_squat_frame_metrics,
    calculate_hip_angles,
)
from pose_detector import LandmarkListAdapter, NormalizedLandmarkPoint  # noqa: E402
from pose_schema import PoseLandmark as L  # noqa: E402

W, H = 640, 480


def _blank(visibility: float = 0.95) -> list[NormalizedLandmarkPoint]:
    return [NormalizedLandmarkPoint(0.5, 0.5, 0.0, visibility) for _ in range(33)]


def _set_px(
    points: list[NormalizedLandmarkPoint],
    idx: int,
    x: float,
    y: float,
    *,
    visibility: float = 0.95,
) -> None:
    points[idx] = NormalizedLandmarkPoint(
        x=x / W, y=y / H, z=0.0, visibility=visibility
    )


def _configure_left_leg(
    points: list[NormalizedLandmarkPoint],
    *,
    shoulder: tuple[float, float],
    hip: tuple[float, float],
    knee: tuple[float, float],
    ankle: tuple[float, float],
    left_vis: float = 0.95,
    right_vis: float = 0.2,
) -> LandmarkListAdapter:
    """Configure left leg chain; right side kept low visibility."""
    for side, vis in (("LEFT", left_vis), ("RIGHT", right_vis)):
        _set_px(points, int(getattr(L, f"{side}_SHOULDER")), *shoulder, visibility=vis)
        _set_px(points, int(getattr(L, f"{side}_HIP")), *hip, visibility=vis)
        _set_px(points, int(getattr(L, f"{side}_KNEE")), *knee, visibility=vis)
        _set_px(points, int(getattr(L, f"{side}_ANKLE")), *ankle, visibility=vis)
    return LandmarkListAdapter(landmark=points)


def test_standing_hip_angle_near_180():
    points = _blank()
    plm = _configure_left_leg(
        points,
        shoulder=(200, 100),
        hip=(200, 200),
        knee=(200, 300),
        ankle=(200, 400),
    )
    result = calculate_hip_angles(plm, L, W, H)
    assert result["left_hip"] is not None
    assert result["left_hip"] > 170.0
    assert result["selected_side"] == "left"


def test_hip_flexion_near_90():
    points = _blank()
    plm = _configure_left_leg(
        points,
        shoulder=(280, 200),
        hip=(200, 200),
        knee=(200, 320),
        ankle=(200, 420),
    )
    result = calculate_hip_angles(plm, L, W, H)
    assert result["left_hip"] is not None
    assert 75.0 <= result["left_hip"] <= 105.0


def test_selected_side_left_when_right_low_visibility():
    points = _blank()
    plm = _configure_left_leg(
        points,
        shoulder=(200, 100),
        hip=(200, 200),
        knee=(200, 300),
        ankle=(200, 400),
        left_vis=0.95,
        right_vis=0.2,
    )
    result = calculate_hip_angles(plm, L, W, H)
    assert result["selected_side"] == "left"


def test_selected_side_right_when_left_low_visibility():
    points = _blank()
    plm = _configure_left_leg(
        points,
        shoulder=(200, 100),
        hip=(200, 200),
        knee=(200, 300),
        ankle=(200, 400),
        left_vis=0.2,
        right_vis=0.95,
    )
    # Mirror to right side with good visibility
    for side, x in (("RIGHT", 440),):
        _set_px(points, int(getattr(L, f"{side}_SHOULDER")), x, 100, visibility=0.95)
        _set_px(points, int(getattr(L, f"{side}_HIP")), x, 200, visibility=0.95)
        _set_px(points, int(getattr(L, f"{side}_KNEE")), x, 300, visibility=0.95)
        _set_px(points, int(getattr(L, f"{side}_ANKLE")), x, 400, visibility=0.95)
    result = calculate_hip_angles(plm, L, W, H)
    assert result["selected_side"] == "right"


def test_both_sides_reliable_selection_deterministic():
    points = _blank()
    for x in (200, 440):
        _set_px(points, int(L.LEFT_SHOULDER if x == 200 else L.RIGHT_SHOULDER), x, 100)
        _set_px(points, int(L.LEFT_HIP if x == 200 else L.RIGHT_HIP), x, 200)
        _set_px(points, int(L.LEFT_KNEE if x == 200 else L.RIGHT_KNEE), x, 300)
        _set_px(points, int(L.LEFT_ANKLE if x == 200 else L.RIGHT_ANKLE), x, 400)
    plm = LandmarkListAdapter(landmark=points)
    r1 = calculate_hip_angles(plm, L, W, H)
    r2 = calculate_hip_angles(plm, L, W, H)
    assert r1["selected_side"] == r2["selected_side"] == "both"
    assert r1["avg_hip"] == r2["avg_hip"]


def test_missing_shoulder_returns_none_hip():
    points = _blank(visibility=0.1)
    _set_px(points, int(L.LEFT_HIP), 200, 200, visibility=0.95)
    _set_px(points, int(L.LEFT_KNEE), 200, 300, visibility=0.95)
    plm = LandmarkListAdapter(landmark=points)
    result = calculate_hip_angles(plm, L, W, H)
    assert result["left_hip"] is None
    assert result["avg_hip"] is None


def test_missing_knee_returns_none_hip():
    points = _blank(visibility=0.1)
    _set_px(points, int(L.LEFT_SHOULDER), 200, 100, visibility=0.95)
    _set_px(points, int(L.LEFT_HIP), 200, 200, visibility=0.95)
    plm = LandmarkListAdapter(landmark=points)
    result = calculate_hip_angles(plm, L, W, H)
    assert result["left_hip"] is None


def test_low_visibility_side_not_selected():
    points = _blank()
    plm = _configure_left_leg(
        points,
        shoulder=(200, 100),
        hip=(200, 200),
        knee=(200, 300),
        ankle=(200, 400),
        left_vis=0.2,
        right_vis=0.2,
    )
    result = calculate_hip_angles(plm, L, W, H)
    assert result["avg_hip"] is None
    assert result["selected_side"] == "unknown"


def test_nan_coordinates_do_not_crash():
    points = _blank()
    points[int(L.LEFT_SHOULDER)] = NormalizedLandmarkPoint(
        x=float("nan"), y=0.3, z=0.0, visibility=0.95
    )
    plm = LandmarkListAdapter(landmark=points)
    result = calculate_hip_angles(plm, L, W, H)
    assert result["left_hip"] is None or 0 <= result["left_hip"] <= 180


def test_angle_clamped_0_180():
    assert _clamp_angle_deg(-10) == 0.0
    assert _clamp_angle_deg(200) == 180.0
    assert math.isnan(_clamp_angle_deg(float("nan"))) is False


def test_build_squat_frame_metrics_includes_all_fields():
    points = _blank()
    plm = _configure_left_leg(
        points,
        shoulder=(200, 100),
        hip=(200, 200),
        knee=(200, 300),
        ankle=(200, 400),
    )
    metrics = build_squat_frame_metrics(plm, L, W, H)
    for key in (
        "avg_knee",
        "avg_hip",
        "torso_lean",
        "torso_lean_deg",
        "metrics_valid",
        "left",
        "average",
    ):
        assert key in metrics
