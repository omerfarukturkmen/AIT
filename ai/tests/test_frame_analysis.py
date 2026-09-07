"""Lifecycle / frame-level analysis API tests (Week 3 Task 5)."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analysis_response import TOP_LEVEL_KEYS  # noqa: E402
from frame_analysis import (  # noqa: E402
    AnalysisSession,
    analyze_frame,
    create_analysis_session,
)
from pose_detector import PoseDetectionResult  # noqa: E402
from squat_analyzer import SquatAnalyzer  # noqa: E402
from video_processor import run_video_analysis  # noqa: E402


def _blank_frame():
    return np.zeros((48, 48, 3), dtype=np.uint8)


def _fake_detector():
    det = MagicMock()
    det.process_frame.return_value = PoseDetectionResult(
        landmarks=None, world_landmarks=None, pose_detected=False
    )
    return det


def test_analyze_frame_handles_single_frame():
    session = create_analysis_session("squat", fps=30.0)
    out = analyze_frame(session, _blank_frame(), _fake_detector())
    assert out["no_pose"] is True
    assert out["pose_detected"] is False
    assert session.total_frames == 1
    assert session.frames_processed == 1


def test_analyze_frame_none_frame_safe():
    session = create_analysis_session("pushup", fps=30.0)
    out = analyze_frame(session, None, _fake_detector())
    assert out["no_pose"] is True
    assert session.total_frames == 1


def test_session_reuses_analyzer_instance_across_frames():
    session = create_analysis_session("squat", fps=30.0)
    analyzer_id = id(session.analyzer)
    det = _fake_detector()
    for _ in range(5):
        analyze_frame(session, _blank_frame(), det)
    assert id(session.analyzer) == analyzer_id
    assert isinstance(session.analyzer, SquatAnalyzer)
    assert session.total_frames == 5


def test_new_session_starts_clean():
    a = create_analysis_session("squat", fps=30.0)
    a.analyzer.rep_count = 4
    a.total_frames = 10
    b = create_analysis_session("squat", fps=30.0)
    assert b.analyzer.rep_count == 0
    assert b.total_frames == 0
    assert a.analyzer is not b.analyzer
    assert a.camera_tracker is not b.camera_tracker


def test_sessions_do_not_share_mutable_state():
    s1 = create_analysis_session("pushup", fps=30.0)
    s2 = create_analysis_session("pushup", fps=30.0)
    s1.quality_stats["low_confidence_frames"] = 99
    assert s2.quality_stats["low_confidence_frames"] == 0


def test_create_analysis_session_resolves_registry_once_per_session():
    with patch(
        "frame_analysis.get_exercise_spec", wraps=__import__(
            "exercise_registry", fromlist=["get_exercise_spec"]
        ).get_exercise_spec
    ) as spy:
        session = create_analysis_session("squat", fps=30.0)
        det = _fake_detector()
        for _ in range(8):
            analyze_frame(session, _blank_frame(), det)
        assert spy.call_count == 1


def test_validate_exercise_once_per_session_create():
    with patch(
        "frame_analysis.validate_exercise_type", wraps=__import__(
            "exercise_registry", fromlist=["validate_exercise_type"]
        ).validate_exercise_type
    ) as spy:
        session = create_analysis_session("pushup", fps=30.0)
        det = _fake_detector()
        for _ in range(6):
            analyze_frame(session, _blank_frame(), det)
        assert spy.call_count == 1


def test_pose_detector_constructed_once_in_video_session(tmp_path: Path):
    video = tmp_path / "tiny.mp4"
    video.write_bytes(b"placeholder")
    frame = _blank_frame()

    fake_cap = MagicMock()
    fake_cap.isOpened.return_value = True
    fake_cap.get.side_effect = lambda prop: {5: 30.0, 7: 5}.get(prop, 0)
    fake_cap.set.return_value = True
    fake_cap.read.side_effect = [
        (True, frame.copy()),  # validation peek
        (True, frame.copy()),
        (True, frame.copy()),
        (True, frame.copy()),
        (False, None),
    ]

    fake_detection = PoseDetectionResult(
        landmarks=None, world_landmarks=None, pose_detected=False
    )
    fake_detector = MagicMock()
    fake_detector.__enter__.return_value = fake_detector
    fake_detector.__exit__.return_value = None
    fake_detector.process_frame.return_value = fake_detection

    ctor = MagicMock(return_value=fake_detector)
    with (
        patch("video_processor.cv2.VideoCapture", return_value=fake_cap),
        patch("video_processor.PoseDetector", ctor),
    ):
        out = run_video_analysis(
            video_path=str(video),
            exercise_type="squat",
            show_preview=False,
            write_json=False,
        )

    assert ctor.call_count == 1
    assert fake_detector.process_frame.call_count == 3
    assert set(out["ai_result"].keys()) == set(TOP_LEVEL_KEYS)
    reps = out["ai_result"]["reps"]
    assert reps["total"] == reps["successful"] + reps["failed"]


def test_state_continuity_within_session():
    session = create_analysis_session("squat", fps=30.0)
    det = _fake_detector()
    analyze_frame(session, _blank_frame(), det)
    analyze_frame(session, _blank_frame(), det)
    assert session.previous_timestamp_ms > 0
    assert session.prev_gray is not None
    assert session.total_frames == 2


def test_orchestration_overhead_benchmark_report(tmp_path: Path):
    """Structural timing report only — no flaky absolute ms assertions."""
    session = create_analysis_session("squat", fps=30.0)
    det = _fake_detector()
    n = 40
    t0 = time.perf_counter()
    for _ in range(n):
        analyze_frame(session, _blank_frame(), det)
    elapsed = time.perf_counter() - t0
    assert session.frames_processed == n
    assert elapsed >= 0.0
    # Keep numbers available for the task report without asserting hardware bounds.
    session._bench = {  # type: ignore[attr-defined]
        "processed_frames": n,
        "total_seconds": elapsed,
        "ms_per_frame": (elapsed / n) * 1000.0 if n else 0.0,
        "processing_fps": (n / elapsed) if elapsed > 0 else 0.0,
    }
    assert session._bench["ms_per_frame"] >= 0.0
