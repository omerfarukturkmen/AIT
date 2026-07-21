"""Tests for push-up angle utilities and body-line alignment."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from angle_utils import calculate_pushup_angles  # noqa: E402
from pose_detector import LandmarkListAdapter, NormalizedLandmarkPoint  # noqa: E402
from pose_schema import PoseLandmark as L  # noqa: E402
from pushup_analyzer import (  # noqa: E402
    HIP_HIGH_OFFSET_THRESHOLD,
    HIP_SAG_OFFSET_THRESHOLD,
)

W, H = 640, 480


def _blank_landmarks(visibility: float = 0.95) -> list[NormalizedLandmarkPoint]:
    return [
        NormalizedLandmarkPoint(0.5, 0.5, 0.0, visibility) for _ in range(33)
    ]


def _set(
    points: list[NormalizedLandmarkPoint],
    idx: int,
    x_px: float,
    y_px: float,
    *,
    visibility: float = 0.95,
) -> None:
    points[idx] = NormalizedLandmarkPoint(
        x=x_px / W,
        y=y_px / H,
        z=0.0,
        visibility=visibility,
    )


def _side_pose(
    *,
    facing: str,
    hip_y: float,
    left_vis: float = 0.95,
    right_vis: float = 0.95,
) -> LandmarkListAdapter:
    """Build a near-horizontal push-up silhouette.

    facing='right' → head/shoulders toward +x (ankle left, shoulder right).
    facing='left'  → head/shoulders toward -x.
    """
    points = _blank_landmarks()
    if facing == "right":
        # Ankle left ---- hip ---- shoulder right
        sh, hip, knee, ank = (480.0, 200.0), (320.0, hip_y), (220.0, 200.0), (120.0, 200.0)
    else:
        # Shoulder left ---- hip ---- ankle right
        sh, hip, knee, ank = (120.0, 200.0), (320.0, hip_y), (420.0, 200.0), (520.0, 200.0)

    for side, vis in (("LEFT", left_vis), ("RIGHT", right_vis)):
        _set(points, int(getattr(L, f"{side}_SHOULDER")), sh[0], sh[1], visibility=vis)
        _set(points, int(getattr(L, f"{side}_HIP")), hip[0], hip[1], visibility=vis)
        _set(points, int(getattr(L, f"{side}_KNEE")), knee[0], knee[1], visibility=vis)
        _set(points, int(getattr(L, f"{side}_ANKLE")), ank[0], ank[1], visibility=vis)
        # Elbow/wrist placeholders so other angles still compute when visible.
        _set(points, int(getattr(L, f"{side}_ELBOW")), sh[0], sh[1] + 40, visibility=vis)
        _set(points, int(getattr(L, f"{side}_WRIST")), sh[0], sh[1] + 80, visibility=vis)

    return LandmarkListAdapter(landmark=points)


def test_calculate_pushup_angles_with_none():
    result = calculate_pushup_angles(None, W, H)
    assert result["avg_elbow"] is None
    assert result["avg_shoulder"] is None
    assert result["avg_hip"] is None
    assert result["body_alignment_angle"] is None
    assert result["body_line_offset"] is None
    assert result["alignment_side"] == "unknown"


def test_straight_body_line_near_zero_offset():
    plm = _side_pose(facing="right", hip_y=200.0)
    result = calculate_pushup_angles(plm, W, H)
    assert result["body_line_offset"] is not None
    assert abs(result["body_line_offset"]) < 0.02
    assert result["body_alignment_angle"] is not None
    assert result["body_alignment_angle"] > 170.0


def test_hips_sagging_positive_offset():
    plm = _side_pose(facing="right", hip_y=260.0)
    result = calculate_pushup_angles(plm, W, H)
    assert result["body_line_offset"] is not None
    assert result["body_line_offset"] > HIP_SAG_OFFSET_THRESHOLD


def test_hips_too_high_negative_offset():
    plm = _side_pose(facing="right", hip_y=140.0)
    result = calculate_pushup_angles(plm, W, H)
    assert result["body_line_offset"] is not None
    assert result["body_line_offset"] < HIP_HIGH_OFFSET_THRESHOLD


def test_facing_left_preserves_sag_and_high_signs():
    sag = calculate_pushup_angles(_side_pose(facing="left", hip_y=260.0), W, H)
    high = calculate_pushup_angles(_side_pose(facing="left", hip_y=140.0), W, H)
    assert sag["body_line_offset"] is not None
    assert high["body_line_offset"] is not None
    assert sag["body_line_offset"] > 0
    assert high["body_line_offset"] < 0
    assert sag["body_line_offset"] > HIP_SAG_OFFSET_THRESHOLD
    assert high["body_line_offset"] < HIP_HIGH_OFFSET_THRESHOLD


def test_near_coincident_shoulder_ankle_returns_none_metrics():
    points = _blank_landmarks()
    # Shoulder and ankle almost the same pixel → unsafe division.
    for side in ("LEFT", "RIGHT"):
        _set(points, int(getattr(L, f"{side}_SHOULDER")), 200.0, 200.0)
        _set(points, int(getattr(L, f"{side}_HIP")), 202.0, 220.0)
        _set(points, int(getattr(L, f"{side}_KNEE")), 201.0, 210.0)
        _set(points, int(getattr(L, f"{side}_ANKLE")), 201.0, 201.0)
    result = calculate_pushup_angles(LandmarkListAdapter(landmark=points), W, H)
    assert result["body_alignment_angle"] is None
    assert result["body_line_offset"] is None
    assert result["alignment_side"] == "unknown"


def test_alignment_side_prefers_visible_left():
    plm = _side_pose(facing="right", hip_y=200.0, left_vis=0.95, right_vis=0.2)
    result = calculate_pushup_angles(plm, W, H)
    assert result["alignment_side"] == "left"
    assert result["body_line_offset"] is not None


def test_alignment_side_prefers_visible_right():
    plm = _side_pose(facing="right", hip_y=200.0, left_vis=0.2, right_vis=0.95)
    result = calculate_pushup_angles(plm, W, H)
    assert result["alignment_side"] == "right"
    assert result["body_line_offset"] is not None
