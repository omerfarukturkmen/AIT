"""Tests for backend ai_analyzer adapter (no large video fixtures)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
AI_SRC = REPO_ROOT / "ai" / "src"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(AI_SRC) not in sys.path:
    sys.path.insert(0, str(AI_SRC))

from ai_analyzer import AnalysisError, analyze_video  # noqa: E402
from video_processor import (  # noqa: E402
    UnsupportedExerciseError,
    normalize_exercise_type,
)


def test_analyze_video_missing_file_raises():
    missing = BACKEND_DIR / "uploaded_videos" / "__does_not_exist__.mp4"
    with pytest.raises(AnalysisError) as exc_info:
        analyze_video(str(missing), "squat")
    assert exc_info.value.status_code == 422
    assert "bulunamadi" in exc_info.value.message.lower() or "bulunamadı" in exc_info.value.message.lower() or "bulunamadi" in str(exc_info.value).lower() or "bulunamad" in str(exc_info.value).lower()


def test_analyze_video_rejects_unsupported_exercise(tmp_path: Path):
    fake_video = tmp_path / "clip.mp4"
    fake_video.write_bytes(b"not-a-real-video")
    with pytest.raises(AnalysisError) as exc_info:
        analyze_video(str(fake_video), "plank")
    assert exc_info.value.status_code == 400
    assert "unsupported" in exc_info.value.message.lower() or "desteklenen" in exc_info.value.message.lower()


def test_analyze_video_invalid_video_does_not_return_fake_success(tmp_path: Path):
    fake_video = tmp_path / "broken.mp4"
    fake_video.write_bytes(b"this-is-not-a-valid-mp4-file")
    with pytest.raises(AnalysisError) as exc_info:
        analyze_video(str(fake_video), "squat")
    # Must fail validation / open, never a success payload with zeros.
    assert exc_info.value.status_code in (422, 500)
    assert exc_info.value.message


def test_normalize_exercise_type_aliases():
    assert normalize_exercise_type("Squat") == "squat"
    assert normalize_exercise_type("push-up") == "pushup"
    assert normalize_exercise_type("pushup") == "pushup"
    assert normalize_exercise_type("PUSH_UP") == "pushup"
    with pytest.raises(UnsupportedExerciseError):
        normalize_exercise_type("burpee")


def test_real_video_reports_reps_without_server_paths():
    video = BACKEND_DIR / "uploaded_videos" / "IMG_5512.mp4"
    model = REPO_ROOT / "ai" / "models" / "pose_landmarker_full.task"
    if not video.exists() or not model.exists():
        pytest.skip("IMG_5512.mp4 or pose model not present")

    result = analyze_video(str(video), "squat")

    # Same expectation as ai/tests/test_squat_false_positives.py.
    assert result["repetition_count"] == 2
    assert result["valid_reps"] == 2
    assert result["details"]["average_min_knee_angle"] is not None
    assert str(BACKEND_DIR) not in repr(result)
    assert "video_path" not in result["details"]
