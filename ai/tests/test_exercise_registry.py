"""Tests for the exercise analyzer registry (Week 3 Task 3)."""

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
from exercise_registry import (  # noqa: E402
    ExerciseSpec,
    UnsupportedExerciseError,
    _reset_registry_for_tests,
    create_analyzer_for_exercise,
    get_exercise_spec,
    normalize_exercise_type,
    register_exercise,
    registered_exercise_keys,
)
from pose_detector import PoseDetectionResult  # noqa: E402
from pushup_analyzer import PushupAnalyzer  # noqa: E402
from squat_analyzer import SquatAnalyzer  # noqa: E402
from video_processor import (  # noqa: E402
    UnsupportedExerciseError as VPUnsupported,
    _create_analyzer,
    run_video_analysis,
)


@pytest.fixture(autouse=True)
def _restore_registry():
    yield
    _reset_registry_for_tests()


def test_builtin_exercises_registered():
    assert registered_exercise_keys() == ("pushup", "squat")


def test_normalize_aliases_via_registry():
    assert normalize_exercise_type("squat") == "squat"
    assert normalize_exercise_type("PUSH-UP") == "pushup"
    assert normalize_exercise_type("push_up") == "pushup"
    assert normalize_exercise_type("push up") == "pushup"


def test_unsupported_exercise_raises_registry_error():
    with pytest.raises(UnsupportedExerciseError):
        normalize_exercise_type("lunge")
    with pytest.raises(VPUnsupported):
        normalize_exercise_type("bench_press")


def test_create_analyzer_for_exercise_routing():
    squat = create_analyzer_for_exercise("squat", fps=30.0)
    push = create_analyzer_for_exercise("pushup", fps=30.0)
    assert isinstance(squat, SquatAnalyzer)
    assert isinstance(push, PushupAnalyzer)
    assert _create_analyzer("squat", fps=25.0).__class__ is SquatAnalyzer


def test_get_exercise_spec_has_required_hooks():
    for key in ("squat", "pushup"):
        spec = get_exercise_spec(key)
        assert callable(spec.create_analyzer)
        assert callable(spec.get_landmark_indices)
        assert callable(spec.process_frame)
        assert spec.score_component_keys


def test_register_custom_exercise_without_touching_video_processor_branches():
    """New exercise can be registered; dispatch uses spec.process_frame."""

    created = {"n": 0}

    def _create(*, fps: float = 30.0):
        created["n"] += 1
        return {"fps": fps, "kind": "dummy"}

    def _landmarks(_enum):
        return (1, 2, 3)

    def _process(analyzer, *args, **kwargs):
        return {
            "analysis": {"ok": True, "analyzer": analyzer},
            "counted_analyzed_frame": False,
            "selected_side": None,
            "biomechanics": None,
        }

    register_exercise(
        ExerciseSpec(
            key="dummy_press",
            display_name="dummy-press",
            aliases=frozenset({"dummy_press", "dummy-press"}),
            create_analyzer=_create,
            get_landmark_indices=_landmarks,
            process_frame=_process,
            score_component_keys=("form",),
        )
    )
    assert normalize_exercise_type("dummy-press") == "dummy_press"
    analyzer = create_analyzer_for_exercise("dummy_press", fps=12.0)
    assert analyzer["kind"] == "dummy"
    assert created["n"] == 1
    out = get_exercise_spec("dummy_press").process_frame(analyzer)
    assert out["analysis"]["ok"] is True


def test_pipeline_still_returns_schema_contract(tmp_path: Path):
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
        out = run_video_analysis(
            video_path=str(video),
            exercise_type="squat",
            show_preview=False,
            write_json=False,
        )
    ai = out["ai_result"]
    assert set(ai.keys()) == set(TOP_LEVEL_KEYS)
    assert ai["schema_version"] == ANALYSIS_SCHEMA_VERSION
    reps = ai["reps"]
    assert reps["total"] == reps["successful"] + reps["failed"]
