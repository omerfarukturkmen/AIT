"""Build and write the standard backend result JSON (schema 1.0)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from analysis_response import (
    ANALYSIS_SCHEMA_VERSION,
    ANALYSIS_STATUS_COMPLETED,
    empty_analysis_response,
    serialize_analysis_response,
)
from exercise_registry import (
    UnsupportedExerciseError,
    default_score_components,
    normalize_exercise_type,
)

RESULT_JSON_REL = "data/output/result.json"

_DEFAULT_QUALITY_STATS: dict[str, Any] = {
    "min_pose_confidence": 0.5,
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


def _normalize_quality_stats(quality_stats: dict[str, Any] | None) -> dict[str, Any]:
    base = dict(_DEFAULT_QUALITY_STATS)
    if quality_stats:
        base.update(quality_stats)
    return base


def _default_components(exercise_type: str) -> dict[str, int]:
    try:
        return default_score_components(normalize_exercise_type(exercise_type))
    except UnsupportedExerciseError:
        return {}


def collect_domain_result(
    analyzer: Any,
    video_path: str | None = None,
    *,
    extra_errors: list[str] | None = None,
    extra_feedback: list[str] | None = None,
    quality_stats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Legacy domain payload from analyzer.get_result (not the final contract).

    Kept for session feedback/camera/visibility mutation and internal tests.
    ``rep_count`` and other analyzer fields remain here — not in the final
    schema 1.0 top-level contract.
    """
    if hasattr(analyzer, "get_result"):
        try:
            result = analyzer.get_result(video_path=video_path or "data/input/input.mp4")
        except TypeError:
            result = analyzer.get_result()
    else:
        result = {
            "exercise": "squat",
            "rep_count": 0,
            "feedback": [],
            "errors": [],
        }

    if not isinstance(result, dict):
        result = {}

    if "errors" in result:
        for code in extra_errors or []:
            if code and code not in result["errors"]:
                result["errors"].append(code)
    if "feedback" in result:
        for msg in extra_feedback or []:
            if msg and msg not in result["feedback"]:
                result["feedback"].append(msg)

    if hasattr(analyzer, "_compute_form_status") and "errors" in result:
        try:
            result["form_status"] = analyzer._compute_form_status(result["errors"])
        except Exception:
            pass

    result["quality"] = _normalize_quality_stats(quality_stats)
    return result


def empty_result(
    video_path: str = "data/input/input.mp4",
    *,
    extra_errors: list[str] | None = None,
    extra_feedback: list[str] | None = None,
    quality_stats: dict[str, Any] | None = None,
    exercise_type: str = "squat",
) -> dict[str, Any]:
    """Return an empty final-contract payload (schema 1.0)."""
    _ = video_path, extra_errors, extra_feedback, quality_stats
    return empty_analysis_response(
        exercise_type=exercise_type,
        component_defaults=_default_components(exercise_type),
    )


def build_result(
    analyzer: Any,
    video_path: str | None = None,
    *,
    extra_errors: list[str] | None = None,
    extra_feedback: list[str] | None = None,
    quality_stats: dict[str, Any] | None = None,
    frames: int = 0,
    processed_frames: int = 0,
    duration_seconds: float = 0.0,
    status: str | None = None,
    warnings: Sequence[str] | None = None,
    exercise_type: str | None = None,
) -> dict[str, Any]:
    """Build the final schema 1.0 analysis response for backend / result.json.

    Domain scoring, feedback, and rep summary are read from the analyzer;
    this function only maps them into the versioned contract.
    """
    domain = collect_domain_result(
        analyzer,
        video_path,
        extra_errors=extra_errors,
        extra_feedback=extra_feedback,
        quality_stats=quality_stats,
    )

    resolved_status = status or domain.get("analysis_status") or ANALYSIS_STATUS_COMPLETED
    session_feedback = list(domain.get("feedback") or [])

    return serialize_analysis_response(
        analyzer,
        frames=frames,
        processed_frames=processed_frames,
        duration_seconds=duration_seconds,
        status=str(resolved_status),
        extra_feedback_messages=session_feedback,
        warnings=list(warnings or []),
        exercise_type=exercise_type or domain.get("exercise"),
    )


def write_result_json(project_root: Path, result: dict[str, Any]) -> Path:
    """Write result dict to data/output/result.json (UTF-8, indented)."""
    output_dir = project_root / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Result JSON saved to: {RESULT_JSON_REL}")
    return out_path


# Re-export for callers / docs
__all__ = [
    "ANALYSIS_SCHEMA_VERSION",
    "RESULT_JSON_REL",
    "build_result",
    "collect_domain_result",
    "empty_result",
    "write_result_json",
]
