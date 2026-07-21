"""Unit tests for PoseDetector (mocked MediaPipe Tasks)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pose_detector import PoseDetector, resolve_pose_model_path  # noqa: E402
from video_processor import compute_video_timestamp_ms, draw_pose_landmarks  # noqa: E402


def test_model_missing_raises_clear_file_not_found(tmp_path: Path):
    missing = tmp_path / "missing.task"
    with pytest.raises(FileNotFoundError) as exc:
        PoseDetector(missing)
    msg = str(exc.value)
    assert "Pose Landmarker model file not found" in msg
    assert "scripts/download_pose_model.py" in msg


def test_resolve_pose_model_path_priority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    explicit = tmp_path / "explicit.task"
    env_model = tmp_path / "env.task"
    explicit.write_bytes(b"x")
    env_model.write_bytes(b"y")
    monkeypatch.setenv("AIT_POSE_MODEL_PATH", str(env_model))
    assert resolve_pose_model_path(explicit) == explicit.resolve()
    assert resolve_pose_model_path(None) == env_model.resolve()


def test_process_frame_converts_bgr_and_passes_timestamp(tmp_path: Path):
    model = tmp_path / "pose.task"
    model.write_bytes(b"fake-model")

    fake_landmarker = MagicMock()
    fake_result = SimpleNamespace(pose_landmarks=[], pose_world_landmarks=[])
    fake_landmarker.detect_for_video.return_value = fake_result

    with (
        patch("pose_detector.mp_pose_landmarker.PoseLandmarker") as landmarker_cls,
        patch("pose_detector.mp.Image") as image_cls,
        patch("pose_detector.cv2.cvtColor") as cvt,
    ):
        landmarker_cls.create_from_options.return_value = fake_landmarker
        rgb = np.zeros((4, 4, 3), dtype=np.uint8)
        cvt.return_value = rgb
        image_cls.return_value = MagicMock(name="mp_image")

        detector = PoseDetector(model)
        bgr = np.zeros((4, 4, 3), dtype=np.uint8)
        bgr[:, :] = (10, 20, 30)
        out = detector.process_frame(bgr, timestamp_ms=123)

        assert out.pose_detected is False
        assert out.landmarks is None
        cvt.assert_called_once()
        # BGR→RGB conversion
        assert cvt.call_args[0][1] is not None
        image_cls.assert_called_once()
        fake_landmarker.detect_for_video.assert_called_once()
        args = fake_landmarker.detect_for_video.call_args[0]
        assert args[1] == 123
        detector.close()


def test_process_frame_adapts_first_pose(tmp_path: Path):
    model = tmp_path / "pose.task"
    model.write_bytes(b"fake-model")

    raw_lms = [
        SimpleNamespace(x=0.1 * i, y=0.2, z=0.0, visibility=0.9) for i in range(33)
    ]
    fake_landmarker = MagicMock()
    fake_landmarker.detect_for_video.return_value = SimpleNamespace(
        pose_landmarks=[raw_lms],
        pose_world_landmarks=[[SimpleNamespace(x=1.0)]],
    )

    with patch("pose_detector.mp_pose_landmarker.PoseLandmarker") as landmarker_cls:
        landmarker_cls.create_from_options.return_value = fake_landmarker
        detector = PoseDetector(model)
        frame = np.zeros((8, 8, 3), dtype=np.uint8)
        result = detector.process_frame(frame, 50)
        assert result.pose_detected is True
        assert result.landmarks is not None
        assert len(result.landmarks.landmark) == 33
        assert result.world_landmarks is not None
        detector.close()


def test_timestamp_never_goes_backwards():
    prev = -1
    stamps: list[int] = []
    for i in range(5):
        ts = compute_video_timestamp_ms(i, 30.0, prev)
        stamps.append(ts)
        prev = ts
    assert stamps == sorted(stamps)
    assert all(stamps[i] > stamps[i - 1] for i in range(1, len(stamps)))


def test_timestamp_uses_fallback_fps_when_invalid():
    ts0 = compute_video_timestamp_ms(0, 0.0, -1)
    ts1 = compute_video_timestamp_ms(1, 0.0, ts0)
    assert ts0 == 0
    assert ts1 == max(int(1000 / 30.0), ts0 + 1)


def test_draw_pose_landmarks_skips_low_visibility():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    from pose_detector import LandmarkListAdapter, NormalizedLandmarkPoint

    landmarks = LandmarkListAdapter(
        landmark=[
            NormalizedLandmarkPoint(0.1, 0.1, 0.0, 0.9),
            NormalizedLandmarkPoint(0.2, 0.2, 0.0, 0.1),
        ]
    )
    before = frame.copy()
    draw_pose_landmarks(frame, landmarks, connections=((0, 1),), visibility_threshold=0.5)
    # Point 0 drawn; connection skipped because point 1 invisible.
    assert not np.array_equal(frame, before)
