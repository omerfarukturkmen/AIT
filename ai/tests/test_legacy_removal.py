"""Regression guards for MediaPipe Legacy Solutions removal."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from angle_utils import calculate_knee_angles, calculate_pushup_angles  # noqa: E402
from pose_detector import LandmarkListAdapter, NormalizedLandmarkPoint  # noqa: E402
from pose_schema import PoseLandmark  # noqa: E402


# Built so this file itself does not contain the forbidden literal substrings.
_LEGACY_RE = re.compile(
    r"(?:mp|mediapipe)\." + r"solutions"
)
_DRAWING_RE = re.compile(r"drawing_" + r"utils")


def _collect_py_sources(*dirs: Path) -> list[Path]:
    files: list[Path] = []
    for d in dirs:
        files.extend(sorted(d.rglob("*.py")))
    return [p for p in files if p.name != Path(__file__).name]


def test_src_has_no_legacy_solutions_usage():
    offenders: list[str] = []
    for path in _collect_py_sources(SRC):
        text = path.read_text(encoding="utf-8")
        if _LEGACY_RE.search(text) or _DRAWING_RE.search(text):
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_tests_have_no_legacy_solutions_usage():
    tests_dir = ROOT / "tests"
    offenders: list[str] = []
    for path in _collect_py_sources(tests_dir):
        text = path.read_text(encoding="utf-8")
        if _LEGACY_RE.search(text) or _DRAWING_RE.search(text):
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_calculate_pushup_angles_no_mediapipe_solutions():
    points = [
        NormalizedLandmarkPoint(0.5, 0.5, 0.0, 0.9) for _ in range(33)
    ]
    points[PoseLandmark.LEFT_SHOULDER] = NormalizedLandmarkPoint(0.4, 0.3, 0.0, 0.95)
    points[PoseLandmark.LEFT_ELBOW] = NormalizedLandmarkPoint(0.35, 0.45, 0.0, 0.95)
    points[PoseLandmark.LEFT_WRIST] = NormalizedLandmarkPoint(0.32, 0.55, 0.0, 0.95)
    points[PoseLandmark.RIGHT_SHOULDER] = NormalizedLandmarkPoint(0.6, 0.3, 0.0, 0.95)
    points[PoseLandmark.RIGHT_ELBOW] = NormalizedLandmarkPoint(0.65, 0.45, 0.0, 0.95)
    points[PoseLandmark.RIGHT_WRIST] = NormalizedLandmarkPoint(0.68, 0.55, 0.0, 0.95)
    points[PoseLandmark.LEFT_HIP] = NormalizedLandmarkPoint(0.42, 0.55, 0.0, 0.95)
    points[PoseLandmark.RIGHT_HIP] = NormalizedLandmarkPoint(0.58, 0.55, 0.0, 0.95)
    points[PoseLandmark.LEFT_ANKLE] = NormalizedLandmarkPoint(0.42, 0.9, 0.0, 0.95)
    points[PoseLandmark.RIGHT_ANKLE] = NormalizedLandmarkPoint(0.58, 0.9, 0.0, 0.95)
    plm = LandmarkListAdapter(landmark=points)
    result = calculate_pushup_angles(plm, 640, 480)
    assert result["left_elbow"] is not None


def test_calculate_knee_angles_with_local_pose_landmark_enum():
    points = [NormalizedLandmarkPoint(0.5, 0.5, 0.0, 0.9) for _ in range(33)]
    points[PoseLandmark.LEFT_HIP] = NormalizedLandmarkPoint(0.4, 0.4, 0.0, 0.95)
    points[PoseLandmark.LEFT_KNEE] = NormalizedLandmarkPoint(0.4, 0.65, 0.0, 0.95)
    points[PoseLandmark.LEFT_ANKLE] = NormalizedLandmarkPoint(0.4, 0.9, 0.0, 0.95)
    points[PoseLandmark.RIGHT_HIP] = NormalizedLandmarkPoint(0.6, 0.4, 0.0, 0.95)
    points[PoseLandmark.RIGHT_KNEE] = NormalizedLandmarkPoint(0.6, 0.65, 0.0, 0.95)
    points[PoseLandmark.RIGHT_ANKLE] = NormalizedLandmarkPoint(0.6, 0.9, 0.0, 0.95)
    plm = LandmarkListAdapter(landmark=points)
    angles = calculate_knee_angles(plm, PoseLandmark, 200, 400)
    assert angles["average"] is not None


def test_show_preview_false_does_not_call_draw(tmp_path: Path):
    from pose_detector import PoseDetectionResult
    from video_processor import run_video_analysis

    video = tmp_path / "tiny.mp4"
    video.write_bytes(b"placeholder")

    frame = np.zeros((32, 32, 3), dtype=np.uint8)
    fake_cap = MagicMock()
    fake_cap.isOpened.return_value = True
    fake_cap.get.side_effect = lambda prop: {
        5: 30.0,  # CAP_PROP_FPS
        7: 1,  # CAP_PROP_FRAME_COUNT
    }.get(prop, 0)
    fake_cap.read.side_effect = [(True, frame.copy()), (False, None)]
    fake_cap.set.return_value = True

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
        patch("video_processor.draw_pose_landmarks") as draw_mock,
        patch("video_processor._draw_squat_hud") as squat_hud,
        patch("video_processor.draw_pushup_hud") as pushup_hud,
        patch("squat_analyzer.draw_squat_hud") as squat_mod_hud,
        patch("pushup_analyzer.draw_pushup_hud") as pushup_mod_hud,
    ):
        # First read validates, then POS_FRAMES reset, then loop read once.
        fake_cap.read.side_effect = [
            (True, frame.copy()),  # validation
            (True, frame.copy()),  # first analysis frame
            (False, None),
        ]
        run_video_analysis(
            video_path=str(video),
            exercise_type="squat",
            show_preview=False,
            write_json=False,
            pose_model_path=str(tmp_path / "unused.task"),
        )
        draw_mock.assert_not_called()
        squat_hud.assert_not_called()
        pushup_hud.assert_not_called()
        squat_mod_hud.assert_not_called()
        pushup_mod_hud.assert_not_called()
