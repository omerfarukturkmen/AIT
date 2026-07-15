"""Build and write the standard backend result JSON."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

RESULT_JSON_REL = "data/output/result.json"


class _AnalyzerLike(Protocol):
    form_status: str
    errors: list[str]

    def get_result(self, video_path: str = ...) -> dict[str, Any]: ...

    def _compute_form_status(self, error_codes: list[str]) -> str: ...

_DEFAULT_QUALITY_STATS: dict[str, Any] = {
    "min_pose_confidence": 0.5,
    "low_confidence_frames": 0,
    "camera_too_far_frames": 0,
    "camera_too_close_frames": 0,
    "camera_unknown_frames": 0,
}


def _normalize_quality_stats(quality_stats: dict[str, Any] | None) -> dict[str, Any]:
    base = dict(_DEFAULT_QUALITY_STATS)
    if quality_stats:
        base.update(quality_stats)
    return base


def empty_result(
    video_path: str = "data/input/input.mp4",
    *,
    extra_errors: list[str] | None = None,
    extra_feedback: list[str] | None = None,
    quality_stats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a fully populated default result payload."""
    errors = list(extra_errors or [])
    feedback = list(extra_feedback or [])
    form_status = "good"
    if errors:
        form_status = "poor" if len(errors) >= 3 else "needs_improvement"
    return {
        "exercise": "squat",
        "rep_count": 0,
        "valid_reps": 0,
        "invalid_reps": 0,
        "form_status": form_status,
        "current_state": "unknown",
        "depth_valid": False,
        "angles": {
            "left_knee_angle": None,
            "right_knee_angle": None,
            "smoothed_knee_angle": None,
        },
        "errors": errors,
        "feedback": feedback,
        "video_path": video_path,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "quality": _normalize_quality_stats(quality_stats),
    }


def build_result(
    analyzer: _AnalyzerLike,
    video_path: str,
    *,
    extra_errors: list[str] | None = None,
    extra_feedback: list[str] | None = None,
    quality_stats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Collect analyzer state into the fixed backend schema."""
    result = analyzer.get_result(video_path=video_path)
    for code in extra_errors or []:
        if code and code not in result["errors"]:
            result["errors"].append(code)
    for msg in extra_feedback or []:
        if msg and msg not in result["feedback"]:
            result["feedback"].append(msg)
    result["form_status"] = analyzer._compute_form_status(result["errors"])
    result["quality"] = _normalize_quality_stats(quality_stats)
    return result


def write_result_json(project_root: Path, result: dict[str, Any]) -> Path:
    """Write result dict to data/output/result.json (UTF-8, indented)."""
    output_dir = project_root / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Result JSON saved to: {RESULT_JSON_REL}")
    return out_path
