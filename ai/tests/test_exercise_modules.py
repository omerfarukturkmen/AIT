"""Module separation / routing / state isolation tests (Week 3 Task 2)."""

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

from analysis_response import ANALYSIS_SCHEMA_VERSION, TOP_LEVEL_KEYS  # noqa: E402
from pose_detector import PoseDetectionResult  # noqa: E402
from pushup_analyzer import (  # noqa: E402
    PushupAnalyzer,
    create_pushup_analyzer,
    process_pushup_frame,
)
from squat_analyzer import (  # noqa: E402
    SquatAnalyzer,
    create_squat_analyzer,
    process_squat_frame,
)
from video_processor import (  # noqa: E402
    UnsupportedExerciseError,
    _create_analyzer,
    analyze_video,
    run_video_analysis,
)


def test_squat_analyzer_direct_import():
    assert SquatAnalyzer is not None
    a = create_squat_analyzer(fps=30.0)
    assert isinstance(a, SquatAnalyzer)
    assert a.rep_count == 0


def test_pushup_analyzer_direct_import():
    assert PushupAnalyzer is not None
    a = create_pushup_analyzer()
    assert isinstance(a, PushupAnalyzer)
    assert a.rep_count == 0


def test_routing_selects_squat_analyzer():
    analyzer = _create_analyzer("squat", fps=30.0)
    assert isinstance(analyzer, SquatAnalyzer)
    assert not isinstance(analyzer, PushupAnalyzer)


def test_routing_selects_pushup_analyzer():
    analyzer = _create_analyzer("pushup")
    assert isinstance(analyzer, PushupAnalyzer)


def test_unsupported_exercise_still_deterministic():
    with pytest.raises(UnsupportedExerciseError):
        _create_analyzer("lunge")
    with pytest.raises(UnsupportedExerciseError):
        analyze_video("x.mp4", "bench_press")


def test_create_factories_return_isolated_instances():
    a1 = create_squat_analyzer(fps=30.0)
    a2 = create_squat_analyzer(fps=30.0)
    a1.rep_count = 5
    assert a2.rep_count == 0

    p1 = create_pushup_analyzer()
    p2 = create_pushup_analyzer()
    p1.rep_count = 3
    assert p2.rep_count == 0


def test_squat_then_squat_starts_clean():
    first = create_squat_analyzer(fps=30.0)
    first.rep_count = 9
    first.errors.append("too_fast")
    second = create_squat_analyzer(fps=30.0)
    assert second.rep_count == 0
    assert second.errors == []
    assert second.current_state == "unknown"


def test_pushup_then_pushup_starts_clean():
    first = create_pushup_analyzer()
    first.rep_count = 4
    first.state = "bottom"
    second = create_pushup_analyzer()
    assert second.rep_count == 0
    assert second.state == "up"


def test_squat_does_not_affect_pushup_state():
    squat = create_squat_analyzer(fps=30.0)
    push = create_pushup_analyzer()
    squat.rep_count = 2
    squat.errors.append("incomplete_rep")
    assert push.rep_count == 0
    assert push.state == "up"


def test_pushup_does_not_affect_squat_state():
    squat = create_squat_analyzer(fps=30.0)
    push = create_pushup_analyzer()
    push.rep_count = 7
    push.invalid_reps = 1
    assert squat.rep_count == 0
    assert squat.invalid_reps == 0


def _run_mocked(tmp_path: Path, exercise_type: str) -> dict:
    video = tmp_path / "tiny.mp4"
    video.write_bytes(b"placeholder")
    frame = np.zeros((32, 32, 3), dtype=np.uint8)
    fake_cap = MagicMock()
    fake_cap.isOpened.return_value = True
    fake_cap.get.side_effect = lambda prop: {5: 30.0, 7: 1}.get(prop, 0)
    fake_cap.set.return_value = True
    fake_cap.read.side_effect = [
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

    with (
        patch("video_processor.cv2.VideoCapture", return_value=fake_cap),
        patch("video_processor.PoseDetector", return_value=fake_detector),
    ):
        return run_video_analysis(
            video_path=str(video),
            exercise_type=exercise_type,
            show_preview=False,
            write_json=False,
        )


def test_final_json_contract_unchanged_for_routed_exercises(tmp_path: Path):
    for exercise in ("squat", "pushup"):
        out = _run_mocked(tmp_path, exercise)
        ai = out["ai_result"]
        assert set(ai.keys()) == set(TOP_LEVEL_KEYS)
        assert ai["schema_version"] == ANALYSIS_SCHEMA_VERSION
        assert ai["exercise_type"] in ("squat", "pushup")
        reps = ai["reps"]
        assert reps["total"] == reps["successful"] + reps["failed"]


def test_process_helpers_are_callable():
    assert callable(process_squat_frame)
    assert callable(process_pushup_frame)
