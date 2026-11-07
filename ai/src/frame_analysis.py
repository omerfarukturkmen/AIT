"""Session-scoped frame analysis API for low-overhead live/video pipelines.

Separates single-frame work from video I/O and final JSON assembly.
PoseDetector and exercise registry resolution belong to the session, not
each frame.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

import cv2

from angle_utils import calculate_pose_confidence, estimate_body_bbox
from camera_utils import CameraStatusTracker
from exercise_registry import (
    ExerciseSpec,
    create_analyzer_for_exercise,
    display_exercise_name,
    get_exercise_spec,
    validate_exercise_type,
)
from frame_sampling import TARGET_PROCESSING_FPS, calculate_frame_step
from pose_detector import PoseDetector, PoseDetectionResult
from pose_schema import POSE_CONNECTIONS, PoseLandmark
from visibility_utils import evaluate_exercise_landmark_visibility

MIN_POSE_CONFIDENCE = 0.50
_LANDMARK_COLOR = (0, 255, 0)
_CONNECTION_COLOR = (0, 200, 255)


def draw_pose_landmarks(
    frame: Any,
    landmarks: Any,
    connections: Sequence[tuple[int, int]] = POSE_CONNECTIONS,
    *,
    visibility_threshold: float = 0.5,
) -> None:
    """Draw pose landmarks and connections with OpenCV (no MediaPipe drawers)."""
    try:
        lm_list = landmarks.landmark
    except AttributeError:
        return

    h, w = frame.shape[:2]
    points: list[tuple[int, int] | None] = []
    for p in lm_list:
        vis = float(getattr(p, "visibility", 0.0) or 0.0)
        if vis < visibility_threshold:
            points.append(None)
            continue
        x = int(round(float(p.x) * w))
        y = int(round(float(p.y) * h))
        points.append((x, y))
        cv2.circle(frame, (x, y), 3, _LANDMARK_COLOR, -1, lineType=cv2.LINE_AA)

    for start_idx, end_idx in connections:
        if start_idx < 0 or end_idx < 0:
            continue
        if start_idx >= len(points) or end_idx >= len(points):
            continue
        a = points[start_idx]
        b = points[end_idx]
        if a is None or b is None:
            continue
        cv2.line(frame, a, b, _CONNECTION_COLOR, 2, lineType=cv2.LINE_AA)


def draw_quality_overlay(
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


def _camera_display_label(status: str) -> str:
    if status == "good":
        return "Camera: OK"
    if status == "too_far":
        return "Camera: Too far"
    if status == "too_close":
        return "Camera: Too close"
    return "Camera: Unknown"


def _new_quality_stats() -> dict[str, Any]:
    return {
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


def _update_quality_stats(
    quality_stats: dict[str, Any],
    *,
    pose_confidence: float,
    camera_status: str,
    landmark_visibility_usable: bool | None = None,
) -> None:
    if pose_confidence < MIN_POSE_CONFIDENCE:
        quality_stats["low_confidence_frames"] += 1
    if camera_status == "too_far":
        quality_stats["camera_too_far_frames"] += 1
    elif camera_status == "too_close":
        quality_stats["camera_too_close_frames"] += 1
    elif camera_status == "unknown":
        quality_stats["camera_unknown_frames"] += 1
    if landmark_visibility_usable is True:
        quality_stats["usable_landmark_frames"] += 1
    elif landmark_visibility_usable is False:
        quality_stats["low_visibility_frames"] += 1


def compute_video_timestamp_ms(
    frame_index: int,
    effective_fps: float,
    previous_timestamp_ms: int,
) -> int:
    """Monotonic VIDEO-mode timestamp from frame index and FPS."""
    fps = effective_fps if effective_fps > 1e-3 else 30.0
    calculated = int(frame_index * 1000.0 / fps)
    return max(calculated, previous_timestamp_ms + 1)


@dataclass
class AnalysisSession:
    """Mutable per-analysis-session context (not shared across sessions)."""

    exercise_key: str
    exercise_name: str
    exercise_spec: ExerciseSpec
    analyzer: Any
    landmark_indices: tuple[Any, ...]
    camera_tracker: CameraStatusTracker
    quality_stats: dict[str, Any]
    effective_fps: float
    source_fps: float = TARGET_PROCESSING_FPS
    frame_step: int = 1
    show_preview: bool = False
    # frames_read: decoded frames (video loop). total_frames kept as alias for
    # pose-processed count for Task-5 compatibility; prefer frames_processed.
    frames_read: int = 0
    total_frames: int = 0
    analyzed_frames: int = 0
    landmark_frames: int = 0
    confidence_sum: float = 0.0
    motion_sum: float = 0.0
    selected_side_counts: dict[str, int] = field(default_factory=dict)
    squat_knee_sum: float = 0.0
    squat_hip_sum: float = 0.0
    squat_torso_sum: float = 0.0
    squat_metric_frames: int = 0
    last_analysis: dict[str, Any] | None = None
    previous_timestamp_ms: int = -1
    prev_gray: Any | None = None
    # Structural counters for lifecycle tests / benchmarks (not final JSON).
    registry_resolve_count: int = 1
    frames_processed: int = 0


def create_analysis_session(
    exercise_type: str,
    *,
    fps: float = 30.0,
    show_preview: bool = False,
    frame_step: int | None = None,
    source_fps: float | None = None,
    target_processing_fps: float = TARGET_PROCESSING_FPS,
) -> AnalysisSession:
    """Validate exercise once and build a fresh isolated analysis session."""
    exercise_key = validate_exercise_type(exercise_type)
    exercise_spec = get_exercise_spec(exercise_key)

    raw_source = float(source_fps) if source_fps is not None else float(fps)
    resolved_source = raw_source if raw_source > 1e-3 else TARGET_PROCESSING_FPS
    step = (
        max(1, int(frame_step))
        if frame_step is not None
        else calculate_frame_step(resolved_source, target_processing_fps)
    )
    # Analyzer time helpers see the *processed* rate (source / step).
    effective_fps = resolved_source / step if step > 0 else resolved_source
    if effective_fps <= 1e-3:
        effective_fps = TARGET_PROCESSING_FPS

    analyzer = create_analyzer_for_exercise(exercise_key, fps=effective_fps)
    return AnalysisSession(
        exercise_key=exercise_key,
        exercise_name=display_exercise_name(exercise_key),
        exercise_spec=exercise_spec,
        analyzer=analyzer,
        landmark_indices=exercise_spec.get_landmark_indices(PoseLandmark),
        camera_tracker=CameraStatusTracker(),
        quality_stats=_new_quality_stats(),
        effective_fps=effective_fps,
        source_fps=resolved_source,
        frame_step=step,
        show_preview=bool(show_preview),
        registry_resolve_count=1,
    )


def _soft_no_pose_result(frame_index: int) -> dict[str, Any]:
    """Lightweight frame result for missing / unusable frames (no exceptions)."""
    return {
        "pose_detected": False,
        "no_pose": True,
        "pose_confidence": 0.0,
        "camera_label": "Camera: Unknown",
        "counted_analyzed_frame": False,
        "analysis": None,
        "frame_index": frame_index,
        "skipped": False,
    }


def _is_usable_bgr_frame(frame: Any) -> bool:
    """True when ``frame`` looks like a non-empty HxWxC image array."""
    if frame is None:
        return False
    try:
        shape = getattr(frame, "shape", None)
        if shape is None or len(shape) < 2:
            return False
        h = int(shape[0])
        w = int(shape[1])
        if h <= 0 or w <= 0:
            return False
        # Reject scalar / 1-D buffers that would crash cvtColor.
        if len(shape) == 1:
            return False
    except (TypeError, ValueError, AttributeError):
        return False
    return True


def analyze_frame(
    session: AnalysisSession,
    frame: Any,
    pose_detector: PoseDetector,
    *,
    video_frame_index: int | None = None,
) -> dict[str, Any]:
    """Analyze one BGR frame using an existing session + detector.

    Does not open videos, write JSON, recreate PoseDetector / registry
    lookups, or decide frame skipping (callers skip before invoking this).

    ``video_frame_index`` is the source-video decode index used for MediaPipe
    VIDEO timestamps; when omitted, uses the pose-processed counter.

    Returns a lightweight internal frame result (not schema 1.0).
    """
    session.frames_processed += 1
    processed_ordinal = session.total_frames
    session.total_frames += 1

    frame_index = (
        int(video_frame_index)
        if video_frame_index is not None
        else processed_ordinal
    )

    if not _is_usable_bgr_frame(frame):
        return _soft_no_pose_result(frame_index)

    # Motion metric (BGR gray) — separate from MediaPipe RGB conversion.
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    except cv2.error:
        return _soft_no_pose_result(frame_index)

    if session.prev_gray is not None:
        try:
            session.motion_sum += float(cv2.absdiff(session.prev_gray, gray).mean())
        except cv2.error:
            pass
    session.prev_gray = gray

    # Timestamps follow source timeline (not processed-only ordinal).
    timestamp_ms = compute_video_timestamp_ms(
        frame_index,
        session.source_fps,
        session.previous_timestamp_ms,
    )
    session.previous_timestamp_ms = timestamp_ms

    detection: PoseDetectionResult = pose_detector.process_frame(frame, timestamp_ms)

    pose_confidence = 0.0
    camera_label = "Camera: Unknown"
    low_confidence = False
    counted = False
    analysis: dict[str, Any] | None = None

    if detection.pose_detected and detection.landmarks is not None:
        session.landmark_frames += 1
        plm = detection.landmarks
        h, w = frame.shape[:2]

        # Single landmark pass for confidence / bbox / visibility / exercise.
        pose_confidence = calculate_pose_confidence(plm, session.landmark_indices)
        session.confidence_sum += pose_confidence
        body_bbox = estimate_body_bbox(plm, w, h)
        camera_info = session.camera_tracker.update(body_bbox, w, h)
        camera_label = _camera_display_label(camera_info["status"])
        visibility_result = evaluate_exercise_landmark_visibility(
            plm,
            session.exercise_key,
        )
        landmark_visibility_usable = visibility_result.is_usable
        _update_quality_stats(
            session.quality_stats,
            pose_confidence=pose_confidence,
            camera_status=camera_info["status"],
            landmark_visibility_usable=landmark_visibility_usable,
        )
        low_confidence = pose_confidence < MIN_POSE_CONFIDENCE

        if session.show_preview:
            draw_pose_landmarks(frame, plm, POSE_CONNECTIONS)

        visibility_dict = visibility_result.as_dict()
        frame_out = session.exercise_spec.process_frame(
            session.analyzer,
            plm,
            PoseLandmark,
            w,
            h,
            pose_confidence=pose_confidence,
            effective_fps=session.effective_fps,
            landmark_visibility_usable=landmark_visibility_usable,
            visibility_dict=visibility_dict,
            camera_info=camera_info,
            low_confidence=low_confidence,
            show_preview=session.show_preview,
            frame=frame,
            last_analysis=session.last_analysis,
            world_landmarks=detection.world_landmarks,
        )
        side = frame_out.get("selected_side")
        if side:
            key = str(side)
            session.selected_side_counts[key] = (
                session.selected_side_counts.get(key, 0) + 1
            )
        bio = frame_out.get("biomechanics")
        if bio is not None:
            session.squat_knee_sum += float(bio["avg_knee"])
            session.squat_hip_sum += float(bio["avg_hip"])
            session.squat_torso_sum += float(bio["torso_lean"])
            session.squat_metric_frames += 1
        counted = bool(frame_out.get("counted_analyzed_frame"))
        if counted:
            session.analyzed_frames += 1
        analysis = frame_out.get("analysis")
        if analysis is not None:
            session.last_analysis = analysis
    else:
        # Expected no-pose path — lightweight, no exception control flow.
        pass

    if session.show_preview:
        draw_quality_overlay(
            frame,
            pose_confidence=pose_confidence,
            camera_label=camera_label,
            low_confidence=low_confidence,
        )

    return {
        "pose_detected": bool(detection.pose_detected and detection.landmarks is not None),
        "no_pose": not (detection.pose_detected and detection.landmarks is not None),
        "pose_confidence": float(pose_confidence),
        "camera_label": camera_label,
        "counted_analyzed_frame": counted,
        "analysis": analysis,
        "frame_index": frame_index,
        "skipped": False,
    }
