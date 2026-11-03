"""Video read/write and frame iteration."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import cv2

from camera_utils import CameraStatusTracker
from exercise_registry import (
    UnsupportedExerciseError,
    create_analyzer_for_exercise,
    normalize_exercise_type,
    validate_exercise_type,
)
from frame_analysis import (
    AnalysisSession,
    analyze_frame,
    compute_video_timestamp_ms,
    create_analysis_session,
    draw_pose_landmarks,
    draw_quality_overlay,
)
from frame_sampling import (
    TARGET_PROCESSING_FPS,
    calculate_frame_step,
    should_process_frame,
)
from pose_detector import PoseDetector
from pushup_analyzer import draw_pushup_hud
from result_writer import (
    build_result,
    collect_domain_result,
    write_result_json,
)
from squat_analyzer import draw_squat_hud, draw_squat_knee_labels
from visibility_utils import (
    ANALYSIS_STATUS_INSUFFICIENT_VISIBILITY,
    VISIBILITY_WARNING,
    visibility_feedback_messages,
)

# Backward-compatible alias used by older tests/call sites.
_draw_quality_overlay = draw_quality_overlay

SOURCE_VIDEO_REL = "data/input/input.mp4"
MIN_POSE_CONFIDENCE = 0.50

_DEFAULT_QUALITY_STATS: dict[str, Any] = {
    "min_pose_confidence": MIN_POSE_CONFIDENCE,
    "low_confidence_frames": 0,
    "camera_too_far_frames": 0,
    "camera_too_close_frames": 0,
    "camera_unknown_frames": 0,
    "usable_landmark_frames": 0,
    "low_visibility_frames": 0,
    "usable_landmark_frame_ratio": 0.0,
    "confirmed_too_close_frames": 0,
    "confirmed_too_far_frames": 0,
    "camera_status_counts": {
        "too_close": 0,
        "good": 0,
        "too_far": 0,
        "unknown": 0,
    },
}


class VideoProcessor:
    """Handles input/output video paths."""

    def __init__(self, input_path: str, output_path: str) -> None:
        self.input_path = input_path
        self.output_path = output_path


class VideoValidationError(Exception):
    """Raised when an input video cannot be opened or read."""


def _new_quality_stats() -> dict[str, Any]:
    return deepcopy(_DEFAULT_QUALITY_STATS)


def _finalize_quality_stats(
    quality_stats: dict[str, Any],
    *,
    pose_processed_frames: int,
    camera_tracker: CameraStatusTracker | None = None,
) -> None:
    usable = int(quality_stats.get("usable_landmark_frames") or 0)
    if pose_processed_frames > 0:
        quality_stats["usable_landmark_frame_ratio"] = round(
            usable / pose_processed_frames,
            4,
        )
    else:
        quality_stats["usable_landmark_frame_ratio"] = 0.0

    if camera_tracker is not None:
        summary = camera_tracker.build_summary()
        counts = summary["camera_status_counts"]
        quality_stats["camera_status_counts"] = counts
        quality_stats["confirmed_too_close_frames"] = summary["too_close_frames"]
        quality_stats["confirmed_too_far_frames"] = summary["too_far_frames"]
        quality_stats["camera_too_close_frames"] = summary["too_close_frames"]
        quality_stats["camera_too_far_frames"] = summary["too_far_frames"]
        quality_stats["camera_unknown_frames"] = summary["unknown_frames"]


def _apply_camera_session_result(
    ai_result: dict[str, Any],
    camera_tracker: CameraStatusTracker,
) -> None:
    summary = camera_tracker.build_summary()
    ai_result["camera_summary"] = summary
    feedback = list(ai_result.get("feedback") or [])
    for msg in camera_tracker.session_feedback():
        if msg not in feedback:
            feedback.append(msg)
    ai_result["feedback"] = feedback


def _apply_visibility_session_result(
    ai_result: dict[str, Any],
    *,
    landmark_frames: int,
    quality_stats: dict[str, Any],
) -> None:
    """Mark session unusable when no usable landmark frames were observed.

    Covers both:
      - pose detected but never visibility-usable
      - zero pose detections across the whole video (no-pose session)
    Uses the existing ``insufficient_landmark_visibility`` status (no new fields).
    """
    usable = int(quality_stats.get("usable_landmark_frames") or 0)
    if usable > 0:
        return
    # usable == 0: either landmark_frames == 0 (no pose) or all detections unusable.
    _ = landmark_frames  # retained for call-site clarity / future metrics
    ai_result["analysis_status"] = ANALYSIS_STATUS_INSUFFICIENT_VISIBILITY
    feedback = list(ai_result.get("feedback") or [])
    for msg in visibility_feedback_messages():
        if msg not in feedback:
            feedback.append(msg)
    ai_result["feedback"] = feedback


# Backward-compatible HUD aliases (tests / older call sites).
_draw_squat_hud = draw_squat_hud
_draw_knee_labels = draw_squat_knee_labels


def _create_analyzer(
    exercise_type: str,
    *,
    fps: float = 30.0,
) -> Any:
    """Create a fresh analyzer via the exercise registry."""
    return create_analyzer_for_exercise(exercise_type, fps=fps)


def _resolve_video_path(project_root: Path, video_path: str) -> Path:
    path = Path(video_path)
    if path.is_absolute():
        return path
    return project_root / path


def validate_video_input(project_root: Path, video_path: str) -> tuple[Path, int]:
    """Resolve video path and verify the file exists and is non-empty.

    Raises:
        FileNotFoundError: path does not exist
        VideoValidationError: file exists but is empty
    """
    resolved_video = _resolve_video_path(project_root, video_path)
    if not resolved_video.exists():
        raise FileNotFoundError(f"Video dosyasi bulunamadi: {resolved_video}")
    file_size = resolved_video.stat().st_size
    if file_size <= 0:
        raise VideoValidationError(f"Video dosyasi bos: {resolved_video}")
    return resolved_video, file_size


def _open_video_capture(
    resolved_video: Path,
) -> tuple[Any, float, int]:
    """Open video and ensure at least one frame is readable.

    Returns:
        (capture, fps, reported_frame_count) with position reset to frame 0.

    Raises:
        VideoValidationError: cannot open or read frames
    """
    cap = cv2.VideoCapture(str(resolved_video))
    if not cap.isOpened():
        raise VideoValidationError(f"Video acilamadi: {resolved_video}")

    # Phone videos (iPhone .MOV especially) are stored sideways with a
    # rotation tag. Without applying it the person looks lying down: knee
    # angles survive, but torso lean is ~90 deg off and form scores collapse.
    cap.set(cv2.CAP_PROP_ORIENTATION_AUTO, 1)

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    reported_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    ok, first_frame = cap.read()
    if not ok or first_frame is None:
        cap.release()
        raise VideoValidationError(f"Videodan frame okunamadi: {resolved_video}")
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    return cap, fps, reported_frame_count


# Stable codes the app localizes; the texts stay for reports and old clients.
CAMERA_WARNING_TEXTS: dict[str, str] = {
    "video_unreadable": "Video frame okunamadi.",
    "camera_too_far": "Kamera cok uzakta; daha yakina gelin.",
    "camera_too_close": "Kamera cok yakinda; biraz uzaklasin.",
    "low_pose_confidence": "Pose guveni dusuk; vucudunuzun tamamini kadraja alin.",
}


def _camera_warning_codes(quality_stats: dict[str, Any], total_frames: int) -> list[str]:
    if total_frames <= 0:
        return ["video_unreadable"]
    codes: list[str] = []
    far = quality_stats.get("camera_too_far_frames", 0)
    close = quality_stats.get("camera_too_close_frames", 0)
    low = quality_stats.get("low_confidence_frames", 0)
    if far / total_frames > 0.3:
        codes.append("camera_too_far")
    if close / total_frames > 0.3:
        codes.append("camera_too_close")
    if low / total_frames > 0.4:
        codes.append("low_pose_confidence")
    return codes


def _build_camera_warnings(quality_stats: dict[str, Any], total_frames: int) -> list[str]:
    return [
        CAMERA_WARNING_TEXTS[code]
        for code in _camera_warning_codes(quality_stats, total_frames)
    ]


def _preview_enabled_from_env() -> bool:
    import os

    return os.environ.get("AIT_SHOW_PREVIEW", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def _assemble_pipeline_result(
    *,
    project_root: Path,
    resolved_video: Path,
    file_size: int,
    exercise_key: str,
    exercise_name: str,
    analyzer: SquatAnalyzer | PushupAnalyzer,
    quality_stats: dict[str, Any],
    camera_tracker: CameraStatusTracker,
    total_frames: int,
    analyzed_frames: int,
    landmark_frames: int,
    confidence_sum: float,
    motion_sum: float,
    fps: float,
    reported_frame_count: int,
    selected_side_counts: dict[str, int],
    squat_knee_sum: float,
    squat_hip_sum: float,
    squat_torso_sum: float,
    squat_metric_frames: int,
    write_json: bool,
) -> dict[str, Any]:
    """Normalize domain + final schema 1.0 contract and package metrics."""
    if total_frames == 0:
        raise VideoValidationError(f"Videodan frame okunamadi: {resolved_video}")

    _finalize_quality_stats(
        quality_stats,
        pose_processed_frames=landmark_frames,
        camera_tracker=camera_tracker,
    )

    domain_result = collect_domain_result(
        analyzer,
        str(resolved_video),
        quality_stats=quality_stats,
    )
    _apply_visibility_session_result(
        domain_result,
        landmark_frames=landmark_frames,
        quality_stats=quality_stats,
    )
    _apply_camera_session_result(domain_result, camera_tracker)

    average_motion = motion_sum / total_frames if total_frames else 0.0
    landmark_ratio = landmark_frames / total_frames if total_frames else 0.0
    mean_landmark_visibility = (
        confidence_sum / landmark_frames if landmark_frames else 0.0
    )
    duration_seconds = (
        round(total_frames / fps, 3) if fps > 1e-3 else round(total_frames / 30.0, 3)
    )
    camera_warning_codes = _camera_warning_codes(quality_stats, total_frames)
    camera_warnings = [CAMERA_WARNING_TEXTS[code] for code in camera_warning_codes]

    dominant_side = "unavailable"
    if selected_side_counts:
        dominant_side = max(selected_side_counts.items(), key=lambda kv: kv[1])[0]
    if (
        not domain_result.get("selected_side")
        or domain_result.get("selected_side") == "unavailable"
    ):
        domain_result["selected_side"] = dominant_side

    analysis_status = domain_result.get("analysis_status") or "completed"
    ai_result = build_result(
        analyzer,
        str(resolved_video),
        quality_stats=quality_stats,
        frames=total_frames,
        processed_frames=analyzed_frames,
        duration_seconds=duration_seconds,
        status=str(analysis_status),
        warnings=camera_warnings,
        exercise_type=exercise_key,
        extra_feedback=list(domain_result.get("feedback") or []),
    )
    if write_json:
        write_result_json(project_root, ai_result)

    session_biomechanics: dict[str, float | None] = {
        "mean_knee_angle": None,
        "mean_hip_angle": None,
        "mean_torso_lean": None,
    }
    if squat_metric_frames > 0:
        session_biomechanics = {
            "mean_knee_angle": round(squat_knee_sum / squat_metric_frames, 2),
            "mean_hip_angle": round(squat_hip_sum / squat_metric_frames, 2),
            "mean_torso_lean": round(squat_torso_sum / squat_metric_frames, 2),
        }

    return {
        "exercise": exercise_name,
        "ai_result": ai_result,
        "domain_result": domain_result,
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
            "camera_warning_codes": camera_warning_codes,
            "quality": quality_stats,
            "selected_side": dominant_side,
            "video_path": str(resolved_video),
            **session_biomechanics,
        },
    }


def run_video_analysis(
    video_path: str = SOURCE_VIDEO_REL,
    exercise_type: str = "squat",
    *,
    show_preview: bool = False,
    write_json: bool = True,
    pose_model_path: str | None = None,
    target_processing_fps: float = TARGET_PROCESSING_FPS,
) -> dict[str, Any]:
    """Run pose-based exercise analysis and return a structured result dict.

    Orchestration stages:
      1. validate exercise type
      2. validate video input
      3. open video + create analyzer
      4. FPS-aware frame sample + pose analysis loop
      5. assemble domain + final schema 1.0 response

    Raises:
        FileNotFoundError: video path does not exist or pose model missing
        VideoValidationError: video cannot be opened or has no readable frames
        UnsupportedExerciseError: unsupported exercise type
    """
    # --- 1) Exercise validation + session (once) ---
    project_root = Path(__file__).resolve().parent.parent

    # --- 2) Video path validation ---
    resolved_video, file_size = validate_video_input(project_root, video_path)

    cap: cv2.VideoCapture | None = None
    session: AnalysisSession | None = None
    fps = 0.0
    reported_frame_count = 0

    try:
        # --- 3) Open video + session-scoped detector/analyzer ---
        cap, fps, reported_frame_count = _open_video_capture(resolved_video)
        frame_step = calculate_frame_step(fps, target_processing_fps)
        session = create_analysis_session(
            exercise_type,
            fps=fps,
            source_fps=fps,
            frame_step=frame_step,
            target_processing_fps=target_processing_fps,
            show_preview=show_preview,
        )

        window = "AIT video test"
        video_frame_index = 0

        # --- 4) Sequential decode; pose/analyzer only on sampled frames ---
        with PoseDetector(pose_model_path) as pose_detector:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                session.frames_read += 1
                if should_process_frame(video_frame_index, session.frame_step):
                    analyze_frame(
                        session,
                        frame,
                        pose_detector,
                        video_frame_index=video_frame_index,
                    )

                if show_preview:
                    cv2.imshow(window, frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

                video_frame_index += 1
    finally:
        if cap is not None:
            cap.release()
        if show_preview:
            cv2.destroyAllWindows()

    if session is None or session.analyzer is None:
        raise VideoValidationError(f"Video analizi baslatilamadi: {resolved_video}")

    # Prefer decoded count for duration / total_frames metrics.
    total_read = session.frames_read if session.frames_read > 0 else session.total_frames

    # --- 5) Result assembly (domain + schema 1.0) once at end ---
    return _assemble_pipeline_result(
        project_root=project_root,
        resolved_video=resolved_video,
        file_size=file_size,
        exercise_key=session.exercise_key,
        exercise_name=session.exercise_name,
        analyzer=session.analyzer,
        quality_stats=session.quality_stats,
        camera_tracker=session.camera_tracker,
        total_frames=total_read,
        analyzed_frames=session.analyzed_frames,
        landmark_frames=session.landmark_frames,
        confidence_sum=session.confidence_sum,
        motion_sum=session.motion_sum,
        fps=fps,
        reported_frame_count=reported_frame_count,
        selected_side_counts=session.selected_side_counts,
        squat_knee_sum=session.squat_knee_sum,
        squat_hip_sum=session.squat_hip_sum,
        squat_torso_sum=session.squat_torso_sum,
        squat_metric_frames=session.squat_metric_frames,
        write_json=write_json,
    )


def analyze_video(
    video_path: str = SOURCE_VIDEO_REL,
    exercise_type: str = "squat",
) -> dict[str, Any]:
    """Public entry: orchestrate video analysis and write ``result.json``.

    Flow:
      1. validate ``exercise_type`` (deterministic / UnsupportedExerciseError)
      2. delegate frame analysis via ``run_video_analysis``
      3. receive normalized final schema 1.0 payload (+ domain/metrics)

    Preview window is disabled by default so headless/CI runs do not hang.
    Set ``AIT_SHOW_PREVIEW=1`` to enable the OpenCV HUD window.
    """
    # Fail fast on unsupported exercise before opening media.
    validate_exercise_type(exercise_type)
    return run_video_analysis(
        video_path=video_path,
        exercise_type=exercise_type,
        show_preview=_preview_enabled_from_env(),
        write_json=True,
    )


def run_video_test_pipeline() -> dict[str, Any]:
    """Backward-compatible entry: default squat video pipeline."""
    return analyze_video(video_path=SOURCE_VIDEO_REL, exercise_type="squat")
