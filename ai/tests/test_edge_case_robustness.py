"""Edge-case robustness tests (Week 3 Task 8).

Covers invalid/corrupt input, dark/synthetic frames, partial landmarks,
no-pose, low visibility, and very short sessions — without inventing
golden expected reps from live actual output.
"""

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

from analysis_response import (  # noqa: E402
    ANALYSIS_SCHEMA_VERSION,
    ANALYSIS_STATUS_INSUFFICIENT_VISIBILITY,
    TOP_LEVEL_KEYS,
)
from frame_analysis import analyze_frame, create_analysis_session  # noqa: E402
from lunge_analyzer import extract_lunge_angles  # noqa: E402
from pose_detector import (  # noqa: E402
    LandmarkListAdapter,
    NormalizedLandmarkPoint,
    PoseDetectionResult,
)
from pose_schema import PoseLandmark  # noqa: E402
from pushup_analyzer import PushupAnalyzer, process_pushup_frame  # noqa: E402
from squat_analyzer import SquatAnalyzer, process_squat_frame  # noqa: E402
from video_processor import (  # noqa: E402
    VideoValidationError,
    run_video_analysis,
    validate_video_input,
)
from visibility_utils import (  # noqa: E402
    MIN_REQUIRED_LANDMARK_VISIBILITY,
    evaluate_exercise_landmark_visibility,
)


W, H = 640, 480


def _blank_points(visibility: float = 0.95) -> list[NormalizedLandmarkPoint]:
    return [
        NormalizedLandmarkPoint(x=0.5, y=0.5, z=0.0, visibility=visibility)
        for _ in range(33)
    ]


def _set(
    points: list[NormalizedLandmarkPoint],
    idx: PoseLandmark,
    x: float,
    y: float,
    visibility: float = 0.95,
) -> None:
    points[int(idx)] = NormalizedLandmarkPoint(
        x=x, y=y, z=0.0, visibility=visibility
    )


def _squat_side_pose(
    *,
    knee_vis: float = 0.95,
    hip_vis: float = 0.95,
    ankle_vis: float = 0.95,
):
    points = _blank_points(0.95)
    _set(points, PoseLandmark.LEFT_SHOULDER, 0.4, 0.2, 0.95)
    _set(points, PoseLandmark.LEFT_HIP, 0.4, 0.45, hip_vis)
    _set(points, PoseLandmark.LEFT_KNEE, 0.4, 0.65, knee_vis)
    _set(points, PoseLandmark.LEFT_ANKLE, 0.4, 0.9, ankle_vis)
    _set(points, PoseLandmark.RIGHT_SHOULDER, 0.6, 0.2, 0.1)
    _set(points, PoseLandmark.RIGHT_HIP, 0.6, 0.45, 0.1)
    _set(points, PoseLandmark.RIGHT_KNEE, 0.6, 0.65, 0.1)
    _set(points, PoseLandmark.RIGHT_ANKLE, 0.6, 0.9, 0.1)
    return LandmarkListAdapter(landmark=points)


def _pushup_side_pose(
    *,
    elbow_vis: float = 0.95,
    shoulder_vis: float = 0.95,
    hip_vis: float = 0.95,
):
    points = _blank_points(0.95)
    _set(points, PoseLandmark.LEFT_SHOULDER, 0.30, 0.35, shoulder_vis)
    _set(points, PoseLandmark.LEFT_ELBOW, 0.25, 0.50, elbow_vis)
    _set(points, PoseLandmark.LEFT_WRIST, 0.20, 0.65, 0.95)
    _set(points, PoseLandmark.LEFT_HIP, 0.40, 0.40, hip_vis)
    _set(points, PoseLandmark.LEFT_KNEE, 0.55, 0.45, 0.95)
    _set(points, PoseLandmark.LEFT_ANKLE, 0.70, 0.50, 0.95)
    for idx in (
        PoseLandmark.RIGHT_SHOULDER,
        PoseLandmark.RIGHT_ELBOW,
        PoseLandmark.RIGHT_WRIST,
        PoseLandmark.RIGHT_HIP,
        PoseLandmark.RIGHT_KNEE,
        PoseLandmark.RIGHT_ANKLE,
    ):
        _set(points, idx, 0.8, 0.5, 0.05)
    return LandmarkListAdapter(landmark=points)


def _fake_detector(pose_detected: bool = False, landmarks=None):
    det = MagicMock()
    det.process_frame.return_value = PoseDetectionResult(
        landmarks=landmarks,
        world_landmarks=None,
        pose_detected=pose_detected,
    )
    return det


def _run_no_pose_video(tmp_path: Path, *, n_frames: int = 3, exercise: str = "squat"):
    video = tmp_path / f"edge_{exercise}_{n_frames}.mp4"
    video.write_bytes(b"placeholder")
    frame = np.zeros((48, 48, 3), dtype=np.uint8)
    reads = [(True, frame.copy()) for _ in range(n_frames)] + [(False, None)]
    fake_cap = MagicMock()
    fake_cap.isOpened.return_value = True
    fake_cap.get.side_effect = lambda prop: {5: 30.0, 7: float(n_frames)}.get(prop, 0)
    fake_cap.set.return_value = True
    fake_cap.read.side_effect = [(True, frame.copy())] + reads

    fake_detector = MagicMock()
    fake_detector.__enter__.return_value = fake_detector
    fake_detector.__exit__.return_value = None
    fake_detector.process_frame.return_value = PoseDetectionResult(
        landmarks=None, world_landmarks=None, pose_detected=False
    )

    with (
        patch("video_processor.cv2.VideoCapture", return_value=fake_cap),
        patch("video_processor.PoseDetector", return_value=fake_detector),
    ):
        out = run_video_analysis(
            video_path=str(video),
            exercise_type=exercise,
            show_preview=False,
            write_json=False,
        )
    return out, fake_detector, fake_cap


def test_nonexistent_path_controlled_failure(tmp_path: Path):
    missing = tmp_path / "gone.mp4"
    with pytest.raises(FileNotFoundError):
        run_video_analysis(str(missing), "squat", show_preview=False, write_json=False)


def test_zero_byte_video_controlled_failure(tmp_path: Path):
    empty = tmp_path / "empty.mp4"
    empty.write_bytes(b"")
    with pytest.raises(VideoValidationError):
        validate_video_input(ROOT, str(empty))


def test_corrupt_video_controlled_failure(tmp_path: Path):
    bad = tmp_path / "corrupt.mp4"
    bad.write_bytes(b"not-a-real-mp4-payload")
    fake_cap = MagicMock()
    fake_cap.isOpened.return_value = False
    with patch("video_processor.cv2.VideoCapture", return_value=fake_cap):
        with pytest.raises(VideoValidationError):
            run_video_analysis(str(bad), "squat", show_preview=False, write_json=False)


def test_zero_readable_frame_after_open_controlled_failure(tmp_path: Path):
    video = tmp_path / "noread.mp4"
    video.write_bytes(b"placeholder")
    fake_cap = MagicMock()
    fake_cap.isOpened.return_value = True
    fake_cap.get.side_effect = lambda prop: {5: 30.0, 7: 10}.get(prop, 0)
    fake_cap.set.return_value = True
    fake_cap.read.return_value = (False, None)
    with patch("video_processor.cv2.VideoCapture", return_value=fake_cap):
        with pytest.raises(VideoValidationError):
            run_video_analysis(str(video), "pushup", show_preview=False, write_json=False)
    fake_cap.release.assert_called()


def test_synthetic_dark_frame_no_crash_no_fake_rep():
    session = create_analysis_session("squat", fps=30.0)
    det = _fake_detector(pose_detected=False)
    dark = np.zeros((64, 64, 3), dtype=np.uint8)
    out1 = analyze_frame(session, dark, det)
    out2 = analyze_frame(session, dark, det)
    assert out1["no_pose"] is True and out2["no_pose"] is True
    assert session.analyzer.rep_count == 0


def test_no_pose_video_no_fake_reps_and_contract(tmp_path: Path):
    out, _det, _cap = _run_no_pose_video(tmp_path, n_frames=4, exercise="squat")
    ai = out["ai_result"]
    assert set(ai.keys()) == set(TOP_LEVEL_KEYS)
    assert ai["schema_version"] == ANALYSIS_SCHEMA_VERSION
    reps = ai["reps"]
    assert reps == {"successful": 0, "failed": 0, "total": 0}
    assert ai["score"]["overall"] == 0
    assert ai["analysis"]["status"] == ANALYSIS_STATUS_INSUFFICIENT_VISIBILITY


def test_no_pose_pushup_video_no_fake_reps(tmp_path: Path):
    out, _det, _cap = _run_no_pose_video(tmp_path, n_frames=3, exercise="pushup")
    ai = out["ai_result"]
    assert ai["reps"]["total"] == 0
    assert ai["score"]["overall"] == 0
    assert ai["analysis"]["status"] == ANALYSIS_STATUS_INSUFFICIENT_VISIBILITY


def test_no_pose_video_deterministic(tmp_path: Path):
    a, _, _ = _run_no_pose_video(tmp_path, n_frames=2, exercise="squat")
    b, _, _ = _run_no_pose_video(tmp_path, n_frames=2, exercise="squat")
    assert a["ai_result"]["reps"] == b["ai_result"]["reps"]
    assert a["ai_result"]["score"]["overall"] == b["ai_result"]["score"]["overall"]
    assert a["ai_result"]["analysis"]["status"] == b["ai_result"]["analysis"]["status"]


def test_distant_person_low_visibility_freezes_squat():
    plm = _squat_side_pose()
    for idx in range(33):
        p = plm.landmark[idx]
        plm.landmark[idx] = NormalizedLandmarkPoint(
            x=p.x, y=p.y, z=p.z, visibility=0.2
        )
    vis = evaluate_exercise_landmark_visibility(plm, "squat")
    assert vis.is_usable is False
    a = SquatAnalyzer(fps=30.0)
    out = process_squat_frame(
        a,
        plm,
        PoseLandmark,
        W,
        H,
        pose_confidence=0.9,
        effective_fps=30.0,
        landmark_visibility_usable=False,
        visibility_dict=vis.as_dict(),
        camera_info={"status": "too_far"},
        low_confidence=False,
        show_preview=False,
        frame=None,
        last_analysis=None,
    )
    assert a.rep_count == 0
    assert out.get("counted_analyzed_frame") is False


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(knee_vis=0.05),
        dict(hip_vis=0.05),
        dict(ankle_vis=0.05),
    ],
)
def test_squat_missing_critical_landmark_safe(kwargs):
    plm = _squat_side_pose(**kwargs)
    vis = evaluate_exercise_landmark_visibility(plm, "squat")
    a = SquatAnalyzer(fps=30.0)
    process_squat_frame(
        a,
        plm,
        PoseLandmark,
        W,
        H,
        pose_confidence=0.85,
        effective_fps=30.0,
        landmark_visibility_usable=vis.is_usable,
        visibility_dict=vis.as_dict(),
        camera_info={"status": "unknown"},
        low_confidence=False,
        show_preview=False,
        frame=None,
        last_analysis=None,
    )
    if not vis.is_usable:
        assert a.rep_count == 0


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(elbow_vis=0.05),
        dict(shoulder_vis=0.05),
        dict(hip_vis=0.05),
    ],
)
def test_pushup_missing_critical_landmark_safe(kwargs):
    plm = _pushup_side_pose(**kwargs)
    vis = evaluate_exercise_landmark_visibility(plm, "pushup")
    a = PushupAnalyzer()
    process_pushup_frame(
        a,
        plm,
        W,
        H,
        pose_confidence=0.85,
        landmark_visibility_usable=vis.is_usable,
        visibility_dict=vis.as_dict(),
        camera_info={"status": "unknown"},
        low_confidence=False,
        show_preview=False,
        frame=None,
    )
    assert a.rep_count == 0
    assert a.invalid_reps == 0


def test_low_visibility_below_threshold_constant():
    assert MIN_REQUIRED_LANDMARK_VISIBILITY == pytest.approx(0.60)
    plm = _squat_side_pose(knee_vis=0.59, hip_vis=0.95, ankle_vis=0.95)
    assert evaluate_exercise_landmark_visibility(plm, "squat").is_usable is False


def test_lunge_missing_left_side_safe():
    points = _blank_points(0.95)
    _set(points, PoseLandmark.RIGHT_SHOULDER, 0.7, 0.2)
    _set(points, PoseLandmark.RIGHT_HIP, 0.7, 0.45)
    _set(points, PoseLandmark.RIGHT_KNEE, 0.7, 0.65)
    _set(points, PoseLandmark.RIGHT_ANKLE, 0.7, 0.9)
    for idx in (
        PoseLandmark.LEFT_SHOULDER,
        PoseLandmark.LEFT_HIP,
        PoseLandmark.LEFT_KNEE,
        PoseLandmark.LEFT_ANKLE,
    ):
        _set(points, idx, 0.3, 0.5, 0.0)
    plm = LandmarkListAdapter(landmark=points)
    out = extract_lunge_angles(plm, PoseLandmark, W, H)
    assert "left_knee_angle" in out
    assert "right_knee_angle" in out
    assert extract_lunge_angles(None, PoseLandmark, W, H)["landmarks_valid"] is False


def test_lunge_all_low_visibility_safe():
    points = _blank_points(0.01)
    plm = LandmarkListAdapter(landmark=points)
    out = extract_lunge_angles(plm, PoseLandmark, W, H)
    assert out["left_knee_angle"] is None
    assert out["right_knee_angle"] is None
    assert out["left_hip_angle"] is None
    assert out["right_hip_angle"] is None


def test_one_frame_video_no_crash(tmp_path: Path):
    out, det, cap = _run_no_pose_video(tmp_path, n_frames=1, exercise="squat")
    assert out["ai_result"]["reps"]["total"] == 0
    assert set(out["ai_result"].keys()) == set(TOP_LEVEL_KEYS)
    assert det.__exit__.called
    cap.release.assert_called()


def test_empty_ndarray_frame_safe():
    session = create_analysis_session("pushup", fps=30.0)
    det = _fake_detector()
    empty = np.zeros((0, 0, 3), dtype=np.uint8)
    out = analyze_frame(session, empty, det)
    assert out["no_pose"] is True
    det.process_frame.assert_not_called()


def test_none_and_invalid_shape_frames_safe():
    session = create_analysis_session("squat", fps=30.0)
    det = _fake_detector()
    assert analyze_frame(session, None, det)["no_pose"] is True
    assert analyze_frame(session, np.zeros((10,), dtype=np.uint8), det)["no_pose"] is True
    assert analyze_frame(session, "not-an-array", det)["no_pose"] is True
    assert det.process_frame.call_count == 0


def test_visibility_block_does_not_advance_squat_with_stale_angles():
    a = SquatAnalyzer(fps=30.0)
    a._smoothed_average = 120.0
    a.previous_smoothed_knee = 120.0
    before_reps = a.rep_count
    before_state = a.current_state
    snap = a.analyze_frame(
        {"average": 90.0, "left": 90.0, "right": 90.0},
        pose_confidence=0.9,
        landmark_visibility_ok=False,
    )
    assert a.rep_count == before_reps
    assert a.current_state == before_state
    assert snap.get("rep_count") == before_reps
    # Visibility-blocked frames must not finalize a new attempt.
    assert a.invalid_reps == 0

def test_pushup_visibility_block_no_failed_rep_from_stale():
    a = PushupAnalyzer()
    a.smoothed_avg_elbow = 160.0
    before = (a.rep_count, a.invalid_reps)
    a.analyze_frame(
        {
            "avg_elbow": 80.0,
            "left_elbow": 80.0,
            "right_elbow": 80.0,
            "body_alignment_angle": 170.0,
            "body_line_offset": 0.01,
        },
        landmark_visibility_ok=False,
    )
    assert (a.rep_count, a.invalid_reps) == before


def test_no_pose_frames_keep_same_analyzer_instance():
    session = create_analysis_session("squat", fps=30.0)
    analyzer_id = id(session.analyzer)
    det = _fake_detector(False)
    analyze_frame(session, np.zeros((32, 32, 3), dtype=np.uint8), det)
    analyze_frame(session, None, det)
    analyze_frame(session, np.zeros((32, 32, 3), dtype=np.uint8), det)
    assert id(session.analyzer) == analyzer_id
    assert session.analyzer.rep_count == 0


def test_detector_closed_after_no_pose_session(tmp_path: Path):
    _out, det, cap = _run_no_pose_video(tmp_path, n_frames=2)
    assert det.__exit__.called
    cap.release.assert_called()


def test_sampling_first_frame_short_video(tmp_path: Path):
    out, det, _cap = _run_no_pose_video(tmp_path, n_frames=1)
    assert det.process_frame.call_count >= 1
    assert out["metrics"]["total_frames"] == 1
