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
    calculate_pushup_angles,
    calculate_torso_lean_angle,
    check_camera_distance,
    estimate_body_bbox,
    get_landmark_point,
)
from pushup_analyzer import PushupAnalyzer
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


class VideoValidationError(Exception):
    """Raised when an input video cannot be opened or read."""


class UnsupportedExerciseError(ValueError):
    """Raised when exercise_type is not supported."""


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


def _pushup_pose_landmark_indices(pose_landmark_enum: object) -> tuple[Any, ...]:
    L = pose_landmark_enum
    return (
        L.LEFT_SHOULDER,
        L.LEFT_ELBOW,
        L.LEFT_WRIST,
        L.RIGHT_SHOULDER,
        L.RIGHT_ELBOW,
        L.RIGHT_WRIST,
        L.LEFT_HIP,
        L.RIGHT_HIP,
        L.LEFT_ANKLE,
        L.RIGHT_ANKLE,
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


def _draw_pushup_hud(
    frame: object,
    analyzer: PushupAnalyzer,
    pose_confidence: float | None,
    camera_distance: dict[str, Any] | None,
) -> None:
    """Draw push-up HUD with safe formatting for None values."""
    y0 = 28
    line_h = 28
    font_scale = 0.65
    angles = getattr(analyzer, "current_angles", {}) or {}
    fb_list = getattr(analyzer, "feedback", None) or []
    fb = fb_list[0] if fb_list else ""

    def _fmt_angle(value: Any) -> str:
        if value is None:
            return "N/A"
        try:
            return f"{float(value):.1f}"
        except (TypeError, ValueError):
            return "N/A"

    cam_status = (camera_distance or {}).get("status", "unknown")
    if cam_status == "good":
        cam_label = "OK"
    elif cam_status == "too_far":
        cam_label = "Too far"
    elif cam_status == "too_close":
        cam_label = "Too close"
    else:
        cam_label = "Unknown"

    conf_label = (
        f"{float(pose_confidence):.2f}" if pose_confidence is not None else "N/A"
    )

    lines = [
        "Exercise: Push-up",
        f"Reps: {getattr(analyzer, 'rep_count', 0)}",
        f"State: {getattr(analyzer, 'state', 'up')}",
        f"Elbow: {_fmt_angle(angles.get('avg_elbow'))}",
        f"Shoulder: {_fmt_angle(angles.get('avg_shoulder'))}",
        f"Hip: {_fmt_angle(angles.get('avg_hip'))}",
        f"Pose Conf: {conf_label}",
        f"Camera: {cam_label}",
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


# Backward-compatible alias used by older call sites.
draw_pushup_hud = _draw_pushup_hud


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
    """Normalize CLI/backend exercise identifiers to canonical keys."""
    normalized = (exercise_type or "").strip().lower().replace("_", "-")
    if normalized == "push-up":
        normalized = "pushup"
    if normalized == "push up":
        normalized = "pushup"
    if normalized not in ("squat", "pushup"):
        raise ValueError(f"Unsupported exercise_type: {exercise_type}")
    return normalized


def display_exercise_name(normalized: str) -> str:
    if normalized == "pushup":
        return "push-up"
    return normalized


def _create_analyzer(
    exercise_type: str,
    *,
    fps: float = 30.0,
) -> SquatAnalyzer | PushupAnalyzer:
    normalized = normalize_exercise_type(exercise_type)
    if normalized == "squat":
        return SquatAnalyzer(fps=fps)
    if normalized == "pushup":
        return PushupAnalyzer()
    raise ValueError(f"Unsupported exercise_type: {exercise_type}")


def _resolve_video_path(project_root: Path, video_path: str) -> Path:
    path = Path(video_path)
    if path.is_absolute():
        return path
    return project_root / path


def _elbow_angles_from_pushup(pushup_angles: dict[str, float | None]) -> dict[str, float | None]:
    return {
        "left": pushup_angles.get("left_elbow"),
        "right": pushup_angles.get("right_elbow"),
        "average": pushup_angles.get("avg_elbow"),
    }


def _build_camera_warnings(quality_stats: dict[str, Any], total_frames: int) -> list[str]:
    warnings: list[str] = []
    if total_frames <= 0:
        return ["Video frame okunamadi."]
    far = quality_stats.get("camera_too_far_frames", 0)
    close = quality_stats.get("camera_too_close_frames", 0)
    low = quality_stats.get("low_confidence_frames", 0)
    if far / total_frames > 0.3:
        warnings.append("Kamera cok uzakta; daha yakina gelin.")
    if close / total_frames > 0.3:
        warnings.append("Kamera cok yakinda; biraz uzaklasin.")
    if low / total_frames > 0.4:
        warnings.append("Pose guveni dusuk; vucudunuzun tamamini kadraja alin.")
    return warnings


def run_video_analysis(
    video_path: str = SOURCE_VIDEO_REL,
    exercise_type: str = "squat",
    *,
    show_preview: bool = False,
    write_json: bool = True,
) -> dict[str, Any]:
    """Run pose-based exercise analysis and return a structured result dict.

    Raises:
        FileNotFoundError: video path does not exist
        VideoValidationError: video cannot be opened or has no readable frames
        UnsupportedExerciseError: unsupported exercise type
    """
    exercise_key = normalize_exercise_type(exercise_type)
    exercise_name = display_exercise_name(exercise_key)
    project_root = Path(__file__).resolve().parent.parent
    resolved_video = _resolve_video_path(project_root, video_path)

    if not resolved_video.exists():
        raise FileNotFoundError(f"Video dosyasi bulunamadi: {resolved_video}")

    file_size = resolved_video.stat().st_size
    if file_size <= 0:
        raise VideoValidationError(f"Video dosyasi bos: {resolved_video}")

    quality_stats = _new_quality_stats()
    cap: cv2.VideoCapture | None = None
    analyzed_frames = 0
    total_frames = 0
    landmark_frames = 0
    confidence_sum = 0.0
    motion_sum = 0.0
    prev_gray = None
    last_analysis: dict | None = None
    fps = 0.0
    selected_side_counts: dict[str, int] = {}
    analyzer: SquatAnalyzer | PushupAnalyzer | None = None
    reported_frame_count = 0

    try:
        cap = cv2.VideoCapture(str(resolved_video))
        if not cap.isOpened():
            raise VideoValidationError(f"Video acilamadi: {resolved_video}")

        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        reported_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        analyzer = _create_analyzer(exercise_key, fps=fps if fps > 1e-3 else 30.0)

        # Validate at least one frame is readable before full analysis.
        ok, first_frame = cap.read()
        if not ok or first_frame is None:
            raise VideoValidationError(
                f"Videodan frame okunamadi: {resolved_video}"
            )
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils
        landmark_indices = (
            _squat_pose_landmark_indices(mp_pose.PoseLandmark)
            if exercise_key == "squat"
            else _pushup_pose_landmark_indices(mp_pose.PoseLandmark)
        )

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

                total_frames += 1
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if prev_gray is not None:
                    motion_sum += float(cv2.absdiff(prev_gray, gray).mean())
                prev_gray = gray

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                results = pose.process(rgb)
                rgb.flags.writeable = True

                pose_confidence = 0.0
                camera_label = "Camera: Unknown"
                low_confidence = False

                if results.pose_landmarks:
                    landmark_frames += 1
                    plm = results.pose_landmarks
                    L = mp_pose.PoseLandmark
                    h, w = frame.shape[:2]

                    pose_confidence = calculate_pose_confidence(plm, landmark_indices)
                    confidence_sum += pose_confidence
                    body_bbox = estimate_body_bbox(plm, w, h)
                    camera_info = check_camera_distance(body_bbox, h)
                    camera_label = _camera_display_label(camera_info["status"])
                    _update_quality_stats(
                        quality_stats,
                        pose_confidence=pose_confidence,
                        camera_status=camera_info["status"],
                    )
                    low_confidence = pose_confidence < MIN_POSE_CONFIDENCE

                    if show_preview:
                        mp_drawing.draw_landmarks(
                            frame,
                            results.pose_landmarks,
                            mp_pose.POSE_CONNECTIONS,
                        )

                    if exercise_key == "squat":
                        knee_angles = calculate_knee_angles(plm, L, w, h)
                        side = str(knee_angles.get("selected_side") or "unavailable")
                        selected_side_counts[side] = (
                            selected_side_counts.get(side, 0) + 1
                        )
                        if (
                            not low_confidence
                            and knee_angles.get("average") is not None
                        ):
                            torso_lean = calculate_torso_lean_angle(plm, L, w, h)
                            analysis = analyzer.analyze_frame(
                                knee_angles,
                                pose_confidence=pose_confidence,
                                torso_lean=torso_lean,
                                fps=fps if fps > 1e-3 else 30.0,
                            )
                            last_analysis = analysis
                            analyzed_frames += 1
                            if show_preview:
                                _draw_squat_hud(frame, analysis)
                                _draw_knee_labels(frame, plm, L, w, h, analysis)
                        elif show_preview and last_analysis is not None:
                            _draw_squat_hud(frame, last_analysis)
                    elif exercise_key == "pushup":
                        assert isinstance(analyzer, PushupAnalyzer)
                        pushup_angles = calculate_pushup_angles(plm, w, h)
                        analysis = analyzer.analyze_frame(
                            pushup_angles,
                            pose_confidence=pose_confidence,
                            camera_status=camera_info["status"],
                        )
                        last_analysis = analysis
                        analyzed_frames += 1
                        if show_preview:
                            draw_pushup_hud(
                                frame,
                                analyzer,
                                pose_confidence,
                                camera_info,
                            )

                if show_preview:
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
        if show_preview:
            cv2.destroyAllWindows()

    if total_frames == 0:
        raise VideoValidationError(f"Videodan frame okunamadi: {resolved_video}")

    if analyzer is None:
        raise VideoValidationError(f"Video analizi baslatilamadi: {resolved_video}")

    ai_result = build_result(
        analyzer,
        str(resolved_video),
        quality_stats=quality_stats,
    )
    if write_json:
        write_result_json(project_root, ai_result)

    average_motion = motion_sum / total_frames if total_frames else 0.0
    landmark_ratio = landmark_frames / total_frames if total_frames else 0.0
    mean_landmark_visibility = (
        confidence_sum / landmark_frames if landmark_frames else 0.0
    )
    duration_seconds = (
        round(total_frames / fps, 3) if fps > 1e-3 else round(total_frames / 30.0, 3)
    )
    camera_warnings = _build_camera_warnings(quality_stats, total_frames)

    dominant_side = "unavailable"
    if selected_side_counts:
        dominant_side = max(selected_side_counts.items(), key=lambda kv: kv[1])[0]
    if not ai_result.get("selected_side") or ai_result.get("selected_side") == "unavailable":
        ai_result["selected_side"] = dominant_side

    return {
        "exercise": exercise_name,
        "ai_result": ai_result,
        "metrics": {
            "file_size_bytes": file_size,
            "total_frames": total_frames,
            "reported_frame_count": reported_frame_count,
            "processed_frames": analyzed_frames,
            "landmark_frames": landmark_frames,
            "landmark_detection_ratio": round(landmark_ratio, 4),
            "mean_landmark_visibility": round(mean_landmark_visibility, 4),
            "ai_confidence": round(mean_landmark_visibility, 4),
            "average_movement": round(average_motion, 2),
            "duration_seconds": duration_seconds,
            "fps": round(fps, 2),
            "camera_warnings": camera_warnings,
            "quality": quality_stats,
            "selected_side": dominant_side,
            "video_path": str(resolved_video),
        },
    }


def analyze_video(
    video_path: str = SOURCE_VIDEO_REL,
    exercise_type: str = "squat",
) -> dict[str, Any]:
    """CLI-oriented entry: analyze video and always write result.json.

    Preview window is disabled by default so headless/CI runs do not hang.
    Set AIT_SHOW_PREVIEW=1 to enable the OpenCV HUD window.
    """
    import os

    show_preview = os.environ.get("AIT_SHOW_PREVIEW", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    return run_video_analysis(
        video_path=video_path,
        exercise_type=exercise_type,
        show_preview=show_preview,
        write_json=True,
    )


def run_video_test_pipeline() -> dict[str, Any]:
    """Backward-compatible entry: default squat video pipeline."""
    return analyze_video(video_path=SOURCE_VIDEO_REL, exercise_type="squat")
