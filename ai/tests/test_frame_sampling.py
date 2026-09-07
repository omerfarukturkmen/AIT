"""Deterministic FPS-aware frame sampling tests (Week 3 Task 6)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analysis_response import TOP_LEVEL_KEYS  # noqa: E402
from frame_analysis import analyze_frame, create_analysis_session  # noqa: E402
from frame_sampling import (  # noqa: E402
    TARGET_PROCESSING_FPS,
    calculate_frame_step,
    should_process_frame,
)
from pose_detector import PoseDetectionResult  # noqa: E402
from video_processor import run_video_analysis  # noqa: E402


def _blank_frame():
    return np.zeros((48, 48, 3), dtype=np.uint8)


def _fake_detector():
    det = MagicMock()
    det.process_frame.return_value = PoseDetectionResult(
        landmarks=None, world_landmarks=None, pose_detected=False
    )
    return det


@pytest.mark.parametrize(
    ("source_fps", "target", "expected"),
    [
        (60.0, 30.0, 2),
        (120.0, 30.0, 4),
        (30.0, 30.0, 1),
        (29.97, 30.0, 1),
        (15.0, 30.0, 1),
        (24.0, 30.0, 1),
        (0.0, 30.0, 1),
        (-5.0, 30.0, 1),
        (float("nan"), 30.0, 1),
        (float("inf"), 30.0, 1),
    ],
)
def test_calculate_frame_step(source_fps, target, expected):
    assert calculate_frame_step(source_fps, target) == expected


def test_frame_step_never_zero_or_negative():
    for src in (0, -1, float("nan"), None, "bad", 0.5, 1e-9):
        step = calculate_frame_step(src)  # type: ignore[arg-type]
        assert step >= 1


def test_should_process_first_frame_always():
    assert should_process_frame(0, 1) is True
    assert should_process_frame(0, 2) is True
    assert should_process_frame(0, 7) is True


def test_should_process_deterministic_indices():
    step = 3
    selected = [i for i in range(12) if should_process_frame(i, step)]
    assert selected == [0, 3, 6, 9]
    assert selected == [i for i in range(12) if should_process_frame(i, step)]


def test_high_fps_session_sets_frame_step_gt_one():
    session = create_analysis_session(
        "squat",
        fps=60.0,
        source_fps=60.0,
        target_processing_fps=30.0,
    )
    assert session.frame_step == 2
    assert abs(session.effective_fps - 30.0) < 1e-6
    assert abs(session.source_fps - 60.0) < 1e-6


def test_low_fps_session_no_skip():
    session = create_analysis_session(
        "pushup",
        fps=15.0,
        source_fps=15.0,
        target_processing_fps=TARGET_PROCESSING_FPS,
    )
    assert session.frame_step == 1


def test_invalid_fps_session_safe_fallback():
    session = create_analysis_session(
        "squat",
        fps=0.0,
        source_fps=0.0,
        frame_step=calculate_frame_step(0.0),
    )
    assert session.frame_step == 1
    assert session.source_fps > 0


def _run_mock_video(*, fps: float, n_frames: int, target: float = 30.0):
    frame = _blank_frame()
    fake_cap = MagicMock()
    fake_cap.isOpened.return_value = True
    fake_cap.get.side_effect = lambda prop: {5: fps, 7: float(n_frames)}.get(prop, 0)
    fake_cap.set.return_value = True
    fake_cap.read.side_effect = [(True, frame.copy()) for _ in range(n_frames)] + [
        (False, None)
    ]

    fake_detection = PoseDetectionResult(
        landmarks=None, world_landmarks=None, pose_detected=False
    )
    fake_detector = MagicMock()
    fake_detector.__enter__.return_value = fake_detector
    fake_detector.__exit__.return_value = None
    fake_detector.process_frame.return_value = fake_detection

    video_path = ROOT / "data" / "input" / "input.mp4"
    with (
        patch(
            "video_processor.validate_video_input",
            return_value=(video_path, 10),
        ),
        patch(
            "video_processor._open_video_capture",
            return_value=(fake_cap, fps, n_frames),
        ),
        patch("video_processor.PoseDetector", return_value=fake_detector),
    ):
        out = run_video_analysis(
            video_path=str(video_path),
            exercise_type="squat",
            show_preview=False,
            write_json=False,
            target_processing_fps=target,
        )
    step = calculate_frame_step(fps, target)
    return out, fake_detector, n_frames, step


def test_high_fps_reduces_pose_detector_calls():
    n = 20
    out, det, _read_n, step = _run_mock_video(fps=60.0, n_frames=n, target=30.0)
    assert step == 2
    expected = sum(1 for i in range(n) if should_process_frame(i, step))
    assert expected == 10
    assert det.process_frame.call_count == expected
    assert expected < n
    assert out["metrics"]["total_frames"] == n
    reps = out["ai_result"]["reps"]
    assert reps["total"] == reps["successful"] + reps["failed"]
    assert set(out["ai_result"].keys()) == set(TOP_LEVEL_KEYS)


def test_low_fps_processes_all_frames():
    n = 12
    out, det, _read_n, step = _run_mock_video(fps=15.0, n_frames=n, target=30.0)
    assert step == 1
    assert det.process_frame.call_count == n
    assert out["metrics"]["total_frames"] == n


def test_invalid_fps_processes_all_frames():
    n = 8
    _out, det, _read_n, step = _run_mock_video(fps=0.0, n_frames=n, target=30.0)
    assert step == 1
    assert det.process_frame.call_count == n


def test_session_isolation_resets_frame_counters():
    a = create_analysis_session("squat", fps=60.0, source_fps=60.0)
    a.frames_read = 99
    a.frames_processed = 40
    b = create_analysis_session("squat", fps=60.0, source_fps=60.0)
    assert b.frames_read == 0
    assert b.frames_processed == 0
    assert a.analyzer is not b.analyzer


def test_analyze_frame_state_survives_across_sampled_calls():
    session = create_analysis_session(
        "squat", fps=60.0, source_fps=60.0, frame_step=2
    )
    det = _fake_detector()
    analyze_frame(session, _blank_frame(), det, video_frame_index=0)
    analyze_frame(session, _blank_frame(), det, video_frame_index=2)
    assert session.frames_processed == 2
    assert session.previous_timestamp_ms > 0
    assert session.analyzer.rep_count == 0


def test_target_constant_is_single_source():
    assert TARGET_PROCESSING_FPS == 30.0
    assert calculate_frame_step(60.0) == calculate_frame_step(
        60.0, TARGET_PROCESSING_FPS
    )
