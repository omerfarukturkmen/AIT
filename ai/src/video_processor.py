"""Video read/write and frame iteration."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import cv2
import mediapipe as mp

from angle_utils import (
    calculate_knee_angles,
    calculate_pose_confidence,
    calculate_torso_lean_angle,
    check_camera_distance,
    estimate_body_bbox,
    get_landmark_point,
)
from result_writer import build_result, empty_result, write_result_json
from squat_analyzer import SquatAnalyzer

SOURCE_VIDEO_REL = "data/input/input.mp4"
MIN_POSE_CONFIDENCE = 0.50

_DEFAULT_QUALITY_STATS: dict[str, Any] = {
    "min_pose_confidence": MIN_POSE_CONFIDENCE,
    "low_confidence_frames": 0,
    "camera_too_far_frames": 0,
    "camera_too_close_frames": 0,
    "camera_unknown_frames": 0,
}


class VideoProcessor:
    """Handles input/output video paths."""

    def __init__(self, input_path: str, output_path: str) -> None:
        self.input_path = input_path
        self.output_path = output_path


def _new_quality_stats() -> dict[str, Any]:
    return deepcopy(_DEFAULT_QUALITY_STATS)


def _squat_pose_landmark_indices(pose_landmark_enum: object) -> tuple[Any, ...]:
    L = pose_landmark_enum
    return (
        L.LEFT_HIP,
        L.LEFT_KNEE,
        L.LEFT_ANKLE,
        L.RIGHT_HIP,
        L.RIGHT_KNEE,
        L.RIGHT_ANKLE,
        L.LEFT_SHOULDER,
        L.RIGHT_SHOULDER,
    )


def _camera_display_label(status: str) -> str:
    if status == "good":
        return "Camera: OK"
    if status == "too_far":
        return "Camera: Too far"
    if status == "too_close":
        return "Camera: Too close"
    return "Camera: Unknown"


def _update_quality_stats(
    quality_stats: dict[str, Any],
    *,
    pose_confidence: float,
    camera_status: str,
) -> None:
    if pose_confidence < MIN_POSE_CONFIDENCE:
        quality_stats["low_confidence_frames"] += 1
    if camera_status == "too_far":
        quality_stats["camera_too_far_frames"] += 1
    elif camera_status == "too_close":
        quality_stats["camera_too_close_frames"] += 1
    elif camera_status == "unknown":
        quality_stats["camera_unknown_frames"] += 1


def _draw_knee_labels(
    frame: object,
    plm: object,
    pose_landmarks_enum: object,
    image_width: int,
    image_height: int,
    analysis: dict,
) -> None:
    """Draw raw (R) and smoothed (S) knee angles beside each knee."""
    L = pose_landmarks_enum
    ka = analysis.get("kneeAngle") or {}
    raw_l, raw_r = ka.get("left"), ka.get("right")
    smooth = ka.get("average")

    lk = get_landmark_point(plm, L.LEFT_KNEE, image_width, image_height)
    rk = get_landmark_point(plm, L.RIGHT_KNEE, image_width, image_height)

    if lk is not None and (raw_l is not None or smooth is not None):
        r_s = f"{raw_l:.0f}" if raw_l is not None else "--"
        s_s = f"{smooth:.0f}" if smooth is not None else "--"
        cv2.putText(
            frame,
            f"R:{r_s} S:{s_s}",
            (lk["x"] + 10, lk["y"] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
    if rk is not None and (raw_r is not None or smooth is not None):
        r_s = f"{raw_r:.0f}" if raw_r is not None else "--"
        s_s = f"{smooth:.0f}" if smooth is not None else "--"
        cv2.putText(
            frame,
            f"R:{r_s} S:{s_s}",
            (rk["x"] + 10, rk["y"] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )


def _draw_squat_hud(frame: object, analysis: dict) -> None:
    """Draw rep stats, state, smoothed angle, and latest feedback."""
    y0 = 28
    line_h = 28
    font_scale = 0.68
    ka = analysis.get("kneeAngle") or {}
    smooth = ka.get("average") or ka.get("smoothedAverage")
    fb_list = analysis.get("feedback") or []
    fb = fb_list[0] if fb_list else ""

    lines = [
        f"Rep Count: {analysis.get('rep_count', analysis.get('repCount', 0))}",
        f"Valid Reps: {analysis.get('valid_reps', 0)}",
        f"Invalid Reps: {analysis.get('invalid_reps', 0)}",
        f"State: {analysis.get('current_state', analysis.get('currentPhase', 'unknown'))}",
        f"Smooth Knee: {smooth:.1f}" if smooth is not None else "Smooth Knee: --",
        f"Form: {analysis.get('form_status', 'good')}",
    ]
    if fb:
        lines.append(f"Feedback: {fb}")
    for i, text in enumerate(lines):
        cv2.putText(
            frame,
            text,
            (12, y0 + i * line_h),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )


def _draw_quality_overlay(
    frame: object,
    *,
    pose_confidence: float,
    camera_label: str,
    low_confidence: bool,
    y_start: int = 240,
) -> None:
    """Draw pose confidence and camera distance warnings."""
    line_h = 26
    font_scale = 0.62
    lines = [
        f"Pose confidence: {pose_confidence:.2f}",
        camera_label,
    ]
    if low_confidence:
        lines.append("Low pose confidence")
    for i, text in enumerate(lines):
        cv2.putText(
            frame,
            text,
            (12, y_start + i * line_h),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (0, 220, 255),
            2,
            cv2.LINE_AA,
        )


def normalize_exercise_type(exercise_type: str) -> str:
    """Normalize CLI/backend exercise identifiers."""
    normalized = exercise_type.strip().lower()
    if normalized == "push-up":
        return "pushup"
    return normalized


def _create_analyzer(exercise_type: str) -> SquatAnalyzer:
    normalized = normalize_exercise_type(exercise_type)
    if normalized == "squat":
        return SquatAnalyzer()
    if normalized == "pushup":
        raise NotImplementedError(
            "Push-up analyzer is not implemented yet. Angle utilities are ready."
        )
    raise ValueError(f"Unsupported exercise_type: {exercise_type}")


def _resolve_video_path(project_root: Path, video_path: str) -> Path:
    path = Path(video_path)
    if path.is_absolute():
        return path
    return project_root / path


def analyze_video(
    video_path: str = SOURCE_VIDEO_REL,
    exercise_type: str = "squat",
) -> None:
    """Run pose-based exercise analysis on a video file."""
    exercise_type = normalize_exercise_type(exercise_type)
    project_root = Path(__file__).resolve().parent.parent
    resolved_video = _resolve_video_path(project_root, video_path)

    analyzer = _create_analyzer(exercise_type)
    quality_stats = _new_quality_stats()
    cap: cv2.VideoCapture | None = None
    load_error: str | None = None
    load_feedback: list[str] = []
    analyzed_frames = 0
    last_analysis: dict | None = None

    try:
        cap = cv2.VideoCapture(str(resolved_video))
        if not cap.isOpened():
            load_error = "video_load_error"
            load_feedback = ["Video dosyasi acilamadi."]
            raise RuntimeError(f"Video acilamadi: {resolved_video}")

        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils
        squat_landmarks = _squat_pose_landmark_indices(mp_pose.PoseLandmark)

        window = "AIT video test"
        with mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ) as pose:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                results = pose.process(rgb)
                rgb.flags.writeable = True

                pose_confidence = 0.0
                camera_label = "Camera: Unknown"
                low_confidence = False

                if results.pose_landmarks:
                    plm = results.pose_landmarks
                    L = mp_pose.PoseLandmark
                    h, w = frame.shape[:2]

                    pose_confidence = calculate_pose_confidence(plm, squat_landmarks)
                    body_bbox = estimate_body_bbox(plm, w, h)
                    camera_info = check_camera_distance(body_bbox, h)
                    camera_label = _camera_display_label(camera_info["status"])
                    _update_quality_stats(
                        quality_stats,
                        pose_confidence=pose_confidence,
                        camera_status=camera_info["status"],
                    )
                    low_confidence = pose_confidence < MIN_POSE_CONFIDENCE

                    mp_drawing.draw_landmarks(
                        frame,
                        results.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS,
                    )

                    knee_angles = calculate_knee_angles(plm, L, w, h)
                    if (
                        exercise_type == "squat"
                        and not low_confidence
                        and knee_angles.get("average") is not None
                    ):
                        torso_lean = calculate_torso_lean_angle(plm, L, w, h)
                        analysis = analyzer.analyze_frame(
                            knee_angles,
                            pose_confidence=pose_confidence,
                            torso_lean=torso_lean,
                        )
                        last_analysis = analysis
                        analyzed_frames += 1
                        _draw_squat_hud(frame, analysis)
                        _draw_knee_labels(frame, plm, L, w, h, analysis)
                    elif exercise_type == "squat" and last_analysis is not None:
                        _draw_squat_hud(frame, last_analysis)

                _draw_quality_overlay(
                    frame,
                    pose_confidence=pose_confidence,
                    camera_label=camera_label,
                    low_confidence=low_confidence,
                )

                cv2.imshow(window, frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()

        extra_errors = [load_error] if load_error else None
        if load_error and analyzed_frames == 0:
            result = empty_result(
                video_path,
                extra_errors=extra_errors,
                extra_feedback=load_feedback,
                quality_stats=quality_stats,
            )
        else:
            result = build_result(
                analyzer,
                video_path,
                extra_errors=extra_errors,
                extra_feedback=load_feedback if load_error else None,
                quality_stats=quality_stats,
            )
        write_result_json(project_root, result)

    if load_error:
        raise RuntimeError(f"Video acilamadi: {resolved_video}")


def run_video_test_pipeline() -> None:
    """Backward-compatible entry: default squat video pipeline."""
    return analyze_video(video_path=SOURCE_VIDEO_REL, exercise_type="squat")
