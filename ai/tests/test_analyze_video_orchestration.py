"""Orchestration / validation regression tests for analyze_video pipeline."""

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
from video_processor import (  # noqa: E402
    UnsupportedExerciseError,
    VideoValidationError,
    analyze_video,
    normalize_exercise_type,
    run_video_analysis,
    validate_exercise_type,
    validate_video_input,
)


def test_normalize_exercise_type_canonical_and_existing_aliases():
    assert normalize_exercise_type("squat") == "squat"
    assert normalize_exercise_type("Squat") == "squat"
    assert normalize_exercise_type("pushup") == "pushup"
    assert normalize_exercise_type("push-up") == "pushup"
    assert normalize_exercise_type("push_up") == "pushup"
    assert validate_exercise_type("PUSH-UP") == "pushup"


def test_unsupported_exercise_type_is_deterministic():
    with pytest.raises(UnsupportedExerciseError) as exc:
        normalize_exercise_type("bench_press")
    assert "Unsupported exercise_type" in str(exc.value)

    with pytest.raises(UnsupportedExerciseError):
        analyze_video(video_path="missing.mp4", exercise_type="bench_press")


def test_nonexistent_video_path_raises_file_not_found(tmp_path: Path):
    missing = tmp_path / "does_not_exist.mp4"
    with pytest.raises(FileNotFoundError) as exc:
        run_video_analysis(
            video_path=str(missing),
            exercise_type="squat",
            show_preview=False,
            write_json=False,
        )
    assert "Video dosyasi bulunamadi" in str(exc.value)


def test_empty_video_file_raises_validation_error(tmp_path: Path):
    empty = tmp_path / "empty.mp4"
    empty.write_bytes(b"")
    project_root = Path(__file__).resolve().parents[1]
    with pytest.raises(VideoValidationError) as exc:
        validate_video_input(project_root, str(empty))
    assert "Video dosyasi bos" in str(exc.value)


def _run_mocked_analysis(tmp_path: Path, exercise_type: str) -> dict:
    video = tmp_path / "tiny.mp4"
    video.write_bytes(b"placeholder")
    frame = np.zeros((32, 32, 3), dtype=np.uint8)

    fake_cap = MagicMock()
    fake_cap.isOpened.return_value = True
    fake_cap.get.side_effect = lambda prop: {5: 30.0, 7: 1}.get(prop, 0)
    fake_cap.set.return_value = True
    fake_cap.read.side_effect = [
        (True, frame.copy()),  # validation peek
        (True, frame.copy()),  # loop frame
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


def test_valid_squat_orchestration_returns_schema_contract(tmp_path: Path):
    out = _run_mocked_analysis(tmp_path, "squat")
    ai = out["ai_result"]
    assert set(ai.keys()) == set(TOP_LEVEL_KEYS)
    assert ai["schema_version"] == ANALYSIS_SCHEMA_VERSION
    assert ai["exercise_type"] == "squat"
    reps = ai["reps"]
    assert reps["total"] == reps["successful"] + reps["failed"]
    assert reps["total"] == 0
    assert ai["analysis"]["status"] == "insufficient_landmark_visibility"
    assert out["exercise"] == "squat"
    assert "domain_result" in out
    assert "metrics" in out


def test_valid_pushup_orchestration_returns_schema_contract(tmp_path: Path):
    out = _run_mocked_analysis(tmp_path, "pushup")
    ai = out["ai_result"]
    assert set(ai.keys()) == set(TOP_LEVEL_KEYS)
    assert ai["exercise_type"] == "pushup"
    reps = ai["reps"]
    assert reps["total"] == reps["successful"] + reps["failed"]
    assert ai["analysis"]["status"] == "insufficient_landmark_visibility"
    assert out["exercise"] == "push-up"


def test_unreadable_video_raises_validation_error(tmp_path: Path):
    video = tmp_path / "bad.mp4"
    video.write_bytes(b"not-a-real-video")
    fake_cap = MagicMock()
    fake_cap.isOpened.return_value = False

    with patch("video_processor.cv2.VideoCapture", return_value=fake_cap):
        with pytest.raises(VideoValidationError) as exc:
            run_video_analysis(
                video_path=str(video),
                exercise_type="squat",
                show_preview=False,
                write_json=False,
            )
    assert "Video acilamadi" in str(exc.value)
