"""Tests for camera distance / framing evaluation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from angle_utils import check_camera_distance  # noqa: E402
from camera_utils import (  # noqa: E402
    CAMERA_FEEDBACK_MESSAGES,
    CAMERA_STATUS_CONFIRMATION_FRAMES,
    CameraStatusTracker,
    compute_body_bbox_metrics,
    measure_camera_status_with_hysteresis,
)
from pushup_analyzer import PushupAnalyzer  # noqa: E402
from video_processor import _apply_camera_session_result  # noqa: E402


def _bbox_from_ratios(
    width_ratio: float,
    height_ratio: float,
    *,
    frame_width: int = 1000,
    frame_height: int = 1000,
) -> tuple[int, int, int, int]:
    bw = int(round(width_ratio * frame_width))
    bh = int(round(height_ratio * frame_height))
    x0 = (frame_width - bw) // 2
    y0 = (frame_height - bh) // 2
    return (x0, y0, x0 + bw, y0 + bh)


def test_good_distance_after_confirmation():
    tracker = CameraStatusTracker()
    bbox = _bbox_from_ratios(0.45, 0.70)
    info = None
    for _ in range(CAMERA_STATUS_CONFIRMATION_FRAMES):
        info = tracker.update(bbox, 1000, 1000)
    assert info is not None
    assert info["status"] == "good"
    assert info.get("feedback") is None


def test_too_close_confirmed_feedback():
    tracker = CameraStatusTracker()
    bbox = _bbox_from_ratios(0.95, 0.95)
    info = None
    for _ in range(CAMERA_STATUS_CONFIRMATION_FRAMES):
        info = tracker.update(bbox, 1000, 1000)
    assert info["status"] == "too_close"
    assert info["feedback"] == CAMERA_FEEDBACK_MESSAGES["too_close"]


def test_single_too_close_frame_not_confirmed():
    tracker = CameraStatusTracker()
    good = _bbox_from_ratios(0.45, 0.70)
    close = _bbox_from_ratios(0.95, 0.95)
    for _ in range(3):
        tracker.update(good, 1000, 1000)
    info = tracker.update(close, 1000, 1000)
    assert tracker.confirmed_camera_status == "good"
    assert info.get("feedback") is None


def test_too_far_confirmed_feedback():
    tracker = CameraStatusTracker()
    bbox = _bbox_from_ratios(0.15, 0.20)
    info = None
    for _ in range(CAMERA_STATUS_CONFIRMATION_FRAMES):
        info = tracker.update(bbox, 1000, 1000)
    assert info["status"] == "too_far"
    assert info["feedback"] == CAMERA_FEEDBACK_MESSAGES["too_far"]


def test_single_too_far_frame_not_confirmed():
    tracker = CameraStatusTracker()
    good = _bbox_from_ratios(0.45, 0.70)
    far = _bbox_from_ratios(0.15, 0.20)
    for _ in range(3):
        tracker.update(good, 1000, 1000)
    info = tracker.update(far, 1000, 1000)
    assert tracker.confirmed_camera_status == "good"
    assert info.get("feedback") is None


def test_hysteresis_too_close_no_flicker():
    tracker = CameraStatusTracker()
    for scale in (0.92, 0.91, 0.92, 0.91, 0.88, 0.87, 0.86):
        bbox = _bbox_from_ratios(scale, scale)
        for _ in range(CAMERA_STATUS_CONFIRMATION_FRAMES):
            tracker.update(bbox, 1000, 1000)
    assert tracker.confirmed_camera_status == "too_close"


def test_hysteresis_too_far_release():
    tracker = CameraStatusTracker()
    far = _bbox_from_ratios(0.20, 0.20)
    for _ in range(CAMERA_STATUS_CONFIRMATION_FRAMES):
        tracker.update(far, 1000, 1000)
    assert tracker.confirmed_camera_status == "too_far"
    good = _bbox_from_ratios(0.50, 0.50)
    for _ in range(CAMERA_STATUS_CONFIRMATION_FRAMES):
        tracker.update(good, 1000, 1000)
    assert tracker.confirmed_camera_status == "good"


def test_pushup_horizontal_body_good():
    metrics = compute_body_bbox_metrics(_bbox_from_ratios(0.75, 0.30), 1000, 1000)
    assert metrics["body_scale"] == pytest.approx(0.75, rel=1e-3)
    assert measure_camera_status_with_hysteresis(metrics["body_scale"], "unknown") == "good"


def test_squat_vertical_body_good():
    metrics = compute_body_bbox_metrics(_bbox_from_ratios(0.30, 0.75), 1000, 1000)
    assert metrics["body_scale"] == pytest.approx(0.75, rel=1e-3)
    assert measure_camera_status_with_hysteresis(metrics["body_scale"], "unknown") == "good"


@pytest.mark.parametrize(
    "bbox,frame_w,frame_h",
    [
        (None, 1000, 1000),
        ((0, 0, 0, 0), 1000, 1000),
        ((0, 0, 10, 0), 1000, 1000),
        ((0, 0, 0, 10), 1000, 1000),
        (_bbox_from_ratios(0.5, 0.5), 0, 1000),
        (_bbox_from_ratios(0.5, 0.5), 1000, 0),
    ],
)
def test_unknown_invalid_bbox(bbox, frame_w, frame_h):
    info = check_camera_distance(bbox, frame_h, frame_w)
    assert info["status"] == "unknown"
    assert info.get("feedback") is None


def test_camera_feedback_dedup_session():
    tracker = CameraStatusTracker()
    bbox = _bbox_from_ratios(0.15, 0.20)
    for _ in range(20):
        tracker.update(bbox, 1000, 1000)
    ai_result = {"feedback": []}
    _apply_camera_session_result(ai_result, tracker)
    assert ai_result["feedback"].count(CAMERA_FEEDBACK_MESSAGES["too_far"]) == 1


def test_camera_status_counts():
    tracker = CameraStatusTracker()
    good = _bbox_from_ratios(0.45, 0.70)
    far = _bbox_from_ratios(0.15, 0.20)
    close = _bbox_from_ratios(0.95, 0.95)
    for _ in range(10):
        tracker.update(good, 1000, 1000)
    for _ in range(CAMERA_STATUS_CONFIRMATION_FRAMES):
        tracker.update(far, 1000, 1000)
    for _ in range(2):
        tracker.update(far, 1000, 1000)
    for _ in range(CAMERA_STATUS_CONFIRMATION_FRAMES):
        tracker.update(close, 1000, 1000)
    for _ in range(3):
        tracker.update(close, 1000, 1000)
    summary = tracker.build_summary()
    assert summary["camera_status_counts"]["good"] == 10
    assert summary["too_far_frames"] >= 5
    assert summary["too_close_frames"] >= 3


def test_dominant_camera_status():
    tracker = CameraStatusTracker()
    good = _bbox_from_ratios(0.45, 0.70)
    for _ in range(8):
        tracker.update(good, 1000, 1000)
    far = _bbox_from_ratios(0.15, 0.20)
    for _ in range(3):
        tracker.update(far, 1000, 1000)
    assert tracker.build_summary()["dominant_status"] == "good"


def test_rep_count_unaffected_by_camera_feedback():
    a = PushupAnalyzer()

    def _a(elbow: float, **kwargs) -> dict:
        return {
            "avg_elbow": elbow,
            "avg_shoulder": 80.0,
            "avg_hip": 170.0,
            "body_alignment_angle": 175.0,
            "body_line_offset": 0.01,
            "alignment_side": "left",
        }

    def _hold(elbow: float, frames: int) -> None:
        for _ in range(frames):
            a.analyze_frame(_a(elbow), camera_status="too_far")

    _hold(165, 6)
    _hold(125, 8)
    _hold(80, 8)
    _hold(120, 8)
    _hold(160, 8)
    assert a.rep_count == 1
    assert a.valid_reps == 1


def test_check_camera_distance_body_scale_orientation_invariant():
    bbox = _bbox_from_ratios(0.75, 0.30, frame_width=640, frame_height=480)
    info = check_camera_distance(bbox, 480, 640)
    assert info["status"] == "good"
    assert info["body_scale"] == pytest.approx(0.75, rel=0.02)
