"""Multi-angle squat video evaluation (baseline measurement, no algorithm changes)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

VALID_CAMERA_ANGLES = frozenset(
    {"front", "front_45", "side", "rear_45", "rear", "unknown"}
)

# Evaluation-only thresholds (not production algorithm logic).
MIN_PROCESSED_FRAME_RATIO = 0.10
MIN_MEAN_LANDMARK_VISIBILITY = 0.30


def _resolve_manifest_path(manifest_path: Path) -> Path:
    return manifest_path.expanduser().resolve()


def _resolve_video_path(manifest_path: Path, video_path: str) -> Path:
    raw = Path(video_path)
    if raw.is_absolute():
        return raw.resolve()
    return (manifest_path.parent / raw).resolve()


def validate_manifest_entry(entry: dict[str, Any], *, index: int) -> None:
    """Raise ValueError for invalid manifest entries."""
    if not isinstance(entry, dict):
        raise ValueError(f"Manifest videos[{index}] must be an object")

    video_id = entry.get("id")
    path = entry.get("path")
    if not video_id or not isinstance(video_id, str):
        raise ValueError(f"Manifest videos[{index}] missing string 'id'")
    if not path or not isinstance(path, str):
        raise ValueError(f"Manifest videos[{index}] missing string 'path'")

    angle = entry.get("camera_angle", "unknown")
    if angle not in VALID_CAMERA_ANGLES:
        allowed = ", ".join(sorted(VALID_CAMERA_ANGLES))
        raise ValueError(
            f"Manifest videos[{index}] ({video_id}) has invalid camera_angle "
            f"'{angle}'. Allowed: {allowed}"
        )

    expected_reps = entry.get("expected_reps")
    if expected_reps is not None and not isinstance(expected_reps, int):
        raise ValueError(
            f"Manifest videos[{index}] ({video_id}) expected_reps must be int or null"
        )

    expected_analyzable = entry.get("expected_analyzable")
    if expected_analyzable is not None and not isinstance(expected_analyzable, bool):
        raise ValueError(
            f"Manifest videos[{index}] ({video_id}) expected_analyzable must be bool or null"
        )


def load_squat_manifest(manifest_path: str | Path) -> list[dict[str, Any]]:
    """Load and validate squat evaluation manifest entries."""
    resolved = _resolve_manifest_path(Path(manifest_path))
    if not resolved.is_file():
        raise FileNotFoundError(f"Squat manifest not found: {resolved}")

    with open(resolved, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("Squat manifest root must be an object")
    videos = data.get("videos", [])
    if videos is None:
        videos = []
    if not isinstance(videos, list):
        raise ValueError("Squat manifest 'videos' must be an array")

    for i, entry in enumerate(videos):
        validate_manifest_entry(entry, index=i)
    return videos


def _camera_status_counts(quality: dict[str, Any] | None) -> dict[str, int]:
    quality = quality or {}
    embedded = quality.get("camera_status_counts")
    if isinstance(embedded, dict) and embedded:
        return {
            "too_close": int(embedded.get("too_close") or 0),
            "good": int(embedded.get("good") or 0),
            "too_far": int(embedded.get("too_far") or 0),
            "unknown": int(embedded.get("unknown") or 0),
            "low_confidence_frames": int(quality.get("low_confidence_frames") or 0),
            "camera_too_far_frames": int(quality.get("camera_too_far_frames") or 0),
            "camera_too_close_frames": int(quality.get("camera_too_close_frames") or 0),
            "camera_unknown_frames": int(quality.get("camera_unknown_frames") or 0),
        }
    return {
        "low_confidence_frames": int(quality.get("low_confidence_frames") or 0),
        "camera_too_far_frames": int(quality.get("camera_too_far_frames") or 0),
        "camera_too_close_frames": int(quality.get("camera_too_close_frames") or 0),
        "camera_unknown_frames": int(quality.get("camera_unknown_frames") or 0),
    }


def _compute_observed_analyzable(
    *,
    analysis_completed: bool,
    processed_frames: int,
    processed_frame_ratio: float,
    mean_landmark_visibility: float,
) -> bool:
    if not analysis_completed:
        return False
    if processed_frames <= 0:
        return False
    if processed_frame_ratio < MIN_PROCESSED_FRAME_RATIO:
        return False
    if mean_landmark_visibility < MIN_MEAN_LANDMARK_VISIBILITY:
        return False
    return True


def _match_optional_bool(observed: bool, expected: bool | None) -> bool | None:
    if expected is None:
        return None
    return observed == expected


def _match_optional_reps(rep_count: int, expected_reps: int | None) -> bool | None:
    if expected_reps is None:
        return None
    return rep_count == expected_reps


def evaluate_squat_video(
    video_path: str | Path,
    *,
    video_id: str = "unknown",
    camera_angle: str = "unknown",
    expected_reps: int | None = None,
    expected_analyzable: bool | None = None,
    run_analysis: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Evaluate one squat video using existing run_video_analysis()."""
    if camera_angle not in VALID_CAMERA_ANGLES:
        allowed = ", ".join(sorted(VALID_CAMERA_ANGLES))
        raise ValueError(
            f"Invalid camera_angle '{camera_angle}'. Allowed: {allowed}"
        )

    resolved = Path(video_path).expanduser().resolve()
    base: dict[str, Any] = {
        "video_id": video_id,
        "video_path": str(resolved),
        "camera_angle": camera_angle,
        "expected_reps": expected_reps,
        "expected_analyzable": expected_analyzable,
        "analysis_completed": False,
        "analysis_error": None,
        "rep_count": None,
        "rep_count_match": None,
        "processed_frames": 0,
        "total_frames": 0,
        "processed_frame_ratio": 0.0,
        "mean_landmark_visibility": 0.0,
        "mean_pose_confidence": 0.0,
        "camera_status_counts": _camera_status_counts(None),
        "result_state": None,
        "warnings": [],
        "observed_analyzable": False,
        "analyzable_match": None,
        "mean_knee_angle": None,
        "mean_hip_angle": None,
        "mean_torso_lean": None,
    }

    if not resolved.is_file():
        base["analysis_error"] = f"Video file not found: {resolved}"
        base["warnings"].append(base["analysis_error"])
        base["analyzable_match"] = _match_optional_bool(False, expected_analyzable)
        return base

    if run_analysis is None:
        from video_processor import run_video_analysis

        run_analysis = run_video_analysis

    try:
        result = run_analysis(
            video_path=str(resolved),
            exercise_type="squat",
            show_preview=False,
            write_json=False,
        )
    except Exception as exc:  # noqa: BLE001 - evaluation must capture failures
        base["analysis_error"] = f"{type(exc).__name__}: {exc}"
        base["warnings"].append(base["analysis_error"])
        base["analyzable_match"] = _match_optional_bool(False, expected_analyzable)
        return base

    ai = result.get("ai_result") or {}
    metrics = result.get("metrics") or {}
    quality = metrics.get("quality") or {}

    processed = int(metrics.get("processed_frames") or 0)
    total = int(metrics.get("total_frames") or 0)
    ratio = round(processed / total, 4) if total > 0 else 0.0
    visibility = float(metrics.get("mean_landmark_visibility") or 0.0)
    confidence = float(metrics.get("ai_confidence") or visibility)

    warnings = list(metrics.get("camera_warnings") or [])
    # Prefer schema 1.0 reps.total; fall back to legacy ai_result.rep_count for mocks.
    reps_obj = ai.get("reps") if isinstance(ai.get("reps"), dict) else None
    if reps_obj is not None:
        rep_count = int(reps_obj.get("total") or 0)
    else:
        rep_count = int(ai.get("rep_count") or 0)
    observed_analyzable = _compute_observed_analyzable(
        analysis_completed=True,
        processed_frames=processed,
        processed_frame_ratio=ratio,
        mean_landmark_visibility=visibility,
    )

    base.update(
        {
            "analysis_completed": True,
            "rep_count": rep_count,
            "rep_count_match": _match_optional_reps(rep_count, expected_reps),
            "processed_frames": processed,
            "total_frames": total,
            "processed_frame_ratio": ratio,
            "mean_landmark_visibility": round(visibility, 4),
            "mean_pose_confidence": round(confidence, 4),
            "camera_status_counts": _camera_status_counts(quality),
            "result_state": ai.get("current_state") or ai.get("final_state"),
            "warnings": warnings,
            "observed_analyzable": observed_analyzable,
            "analyzable_match": _match_optional_bool(
                observed_analyzable, expected_analyzable
            ),
            "mean_knee_angle": metrics.get("mean_knee_angle"),
            "mean_hip_angle": metrics.get("mean_hip_angle"),
            "mean_torso_lean": metrics.get("mean_torso_lean"),
            "low_visibility_frames": int(quality.get("low_visibility_frames") or 0),
            "usable_landmark_frame_ratio": float(
                quality.get("usable_landmark_frame_ratio") or 0.0
            ),
        }
    )
    return base


def _init_angle_bucket() -> dict[str, Any]:
    return {
        "video_count": 0,
        "analysis_success_count": 0,
        "analysis_success_rate": 0.0,
        "rep_match_known_count": 0,
        "rep_match_count": 0,
        "rep_match_rate": 0.0,
        "visibility_sum": 0.0,
        "mean_visibility": 0.0,
        "observed_analyzable_count": 0,
    }


def _build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_angle: dict[str, dict[str, Any]] = {}
    rep_known_total = 0
    rep_match_total = 0

    for item in results:
        angle = str(item.get("camera_angle") or "unknown")
        bucket = by_angle.setdefault(angle, _init_angle_bucket())
        bucket["video_count"] += 1

        if item.get("analysis_completed"):
            bucket["analysis_success_count"] += 1
            bucket["visibility_sum"] += float(item.get("mean_landmark_visibility") or 0.0)
        if item.get("observed_analyzable"):
            bucket["observed_analyzable_count"] += 1

        rep_match = item.get("rep_count_match")
        if rep_match is not None:
            bucket["rep_match_known_count"] += 1
            rep_known_total += 1
            if rep_match:
                bucket["rep_match_count"] += 1
                rep_match_total += 1

    for bucket in by_angle.values():
        count = bucket["video_count"]
        if count > 0:
            bucket["analysis_success_rate"] = round(
                bucket["analysis_success_count"] / count, 4
            )
            if bucket["analysis_success_count"] > 0:
                bucket["mean_visibility"] = round(
                    bucket["visibility_sum"] / bucket["analysis_success_count"], 4
                )
        known = bucket["rep_match_known_count"]
        if known > 0:
            bucket["rep_match_rate"] = round(bucket["rep_match_count"] / known, 4)

    analyzed = sum(1 for r in results if r.get("analysis_completed"))
    rep_accuracy = round(rep_match_total / rep_known_total, 4) if rep_known_total else None

    return {
        "total_videos": len(results),
        "analyzed_videos": analyzed,
        "rep_accuracy_known_samples": rep_accuracy,
        "by_camera_angle": by_angle,
    }


def evaluate_squat_manifest(
    manifest_path: str | Path,
    *,
    run_analysis: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Evaluate all videos listed in a squat manifest."""
    resolved_manifest = _resolve_manifest_path(Path(manifest_path))
    entries = load_squat_manifest(resolved_manifest)

    results: list[dict[str, Any]] = []
    for entry in entries:
        video_path = _resolve_video_path(resolved_manifest, entry["path"])
        results.append(
            evaluate_squat_video(
                video_path,
                video_id=str(entry["id"]),
                camera_angle=str(entry.get("camera_angle") or "unknown"),
                expected_reps=entry.get("expected_reps"),
                expected_analyzable=entry.get("expected_analyzable"),
                run_analysis=run_analysis,
            )
        )

    return {
        "manifest_path": str(resolved_manifest),
        "results": results,
        "summary": _build_summary(results),
    }
