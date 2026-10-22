"""Adapter between FastAPI backend and ai/src pose analysis pipeline.

All exercise analysis logic lives in ai/src. This module only validates
inputs, invokes the AI package, and maps results to the API response shape.
"""

from __future__ import annotations

import logging
import sys
import time
import traceback
from pathlib import Path
from typing import Any

logger = logging.getLogger("ai_analyzer")

_BACKEND_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _BACKEND_DIR.parent
_AI_SRC = _REPO_ROOT / "ai" / "src"

if str(_AI_SRC) not in sys.path:
    sys.path.insert(0, str(_AI_SRC))

from exercise_registry import display_exercise_name  # noqa: E402
from video_processor import (  # noqa: E402
    UnsupportedExerciseError,
    VideoValidationError,
    normalize_exercise_type,
    run_video_analysis,
)

# Weighted form-error severities (not unique-count-only scoring)
_ERROR_SEVERITY: dict[str, float] = {
    "insufficient_depth": 18.0,
    "knee_angle_insufficient": 10.0,
    "too_deep_or_unstable": 16.0,
    "too_fast": 8.0,
    "incomplete_rep": 12.0,
    "torso_lean": 10.0,
}


class AnalysisError(Exception):
    """Raised when video analysis fails validation or processing."""

    def __init__(self, message: str, *, status_code: int = 500) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _depth_quality_score(ai_result: dict[str, Any]) -> float:
    """0–100 from completed reps' min knee angles (lower min => better depth)."""
    history = ai_result.get("rep_history") or []
    mins = [
        float(r["min_knee_angle"])
        for r in history
        if r.get("min_knee_angle") is not None and r.get("valid")
    ]
    if not mins:
        avg_min = ai_result.get("average_min_knee_angle")
        if avg_min is None:
            return 35.0
        mins = [float(avg_min)]

    scores: list[float] = []
    for m in mins:
        if m <= 70:
            scores.append(100.0)
        elif m <= 85:
            scores.append(90.0)
        elif m <= 100:
            scores.append(75.0)
        elif m <= 115:
            scores.append(45.0)
        else:
            scores.append(20.0)
    return sum(scores) / len(scores)


def _error_penalty(errors: list[str]) -> float:
    total = 0.0
    for code in errors:
        total += _ERROR_SEVERITY.get(str(code), 6.0)
    return min(40.0, total)


def _compute_score(ai_result: dict[str, Any], metrics: dict[str, Any]) -> int:
    """0–100 score from validity, depth, form severity, detection, confidence."""
    valid = int(ai_result.get("valid_reps") or 0)
    invalid = int(ai_result.get("invalid_reps") or 0)
    completed = valid + invalid
    errors = list(ai_result.get("errors") or [])

    landmark_ratio = float(metrics.get("landmark_detection_ratio") or 0.0)
    mean_vis = float(
        metrics.get("mean_landmark_visibility")
        or metrics.get("ai_confidence")
        or 0.0
    )

    if completed <= 0:
        # No finished reps: keep score modest even with good landmarks.
        base = 20.0 + 15.0 * landmark_ratio + 10.0 * mean_vis
        return max(0, min(45, int(round(base - _error_penalty(errors) * 0.5))))

    validity_ratio = valid / completed
    depth_score = _depth_quality_score(ai_result)
    detection_score = 100.0 * landmark_ratio
    confidence_score = 100.0 * mean_vis

    composite = (
        0.35 * (100.0 * validity_ratio)
        + 0.30 * depth_score
        + 0.15 * detection_score
        + 0.10 * confidence_score
        + 0.10 * (100.0 - _error_penalty(errors) * 2.0)
    )
    score = int(round(composite - _error_penalty(errors) * 0.35))
    return max(0, min(100, score))


def _feedback_text(ai_result: dict[str, Any], score: int) -> str:
    feedback_list = ai_result.get("feedback") or []
    # Prefer human-readable messages; skip raw error codes already in errors.
    human = [
        str(item)
        for item in feedback_list
        if item and str(item) not in (ai_result.get("errors") or [])
    ]
    if human:
        return " | ".join(human)
    if score >= 75:
        return "Hareket formu genel olarak iyi gorunuyor."
    if score >= 50:
        return "Hareket algilandi ancak formda iyilestirme alani var."
    return "Pose veya hareket net algilanamadi. Kamerayi ve aciyi kontrol edin."


def analyze_video(video_path: str, exercise_type: str) -> dict[str, Any]:
    """Analyze an uploaded video using ai/src and return API-ready payload."""
    started = time.time()
    path = Path(video_path)

    logger.info("=== AI analysis start ===")
    logger.info("video_path=%s", path)
    logger.info("exercise_type=%s", exercise_type)

    try:
        if not path.exists():
            raise AnalysisError(
                f"Video dosyasi bulunamadi: {path}",
                status_code=422,
            )

        file_size = path.stat().st_size
        logger.info("file_size_bytes=%s", file_size)
        if file_size <= 0:
            raise AnalysisError(
                f"Video dosyasi bos: {path}",
                status_code=422,
            )

        try:
            normalized = normalize_exercise_type(exercise_type)
        except UnsupportedExerciseError as exc:
            raise AnalysisError(str(exc), status_code=400) from exc

        exercise_name = display_exercise_name(normalized)
        logger.info("normalized_exercise=%s", exercise_name)

        analysis = run_video_analysis(
            video_path=str(path.resolve()),
            exercise_type=normalized,
            show_preview=False,
            write_json=False,
        )

        ai_result = analysis["ai_result"]
        metrics = analysis["metrics"]
        score = _compute_score(ai_result, metrics)
        risk_percent = max(0, min(100, 100 - score))
        repetition_count = int(ai_result.get("rep_count") or 0)
        valid_reps = int(ai_result.get("valid_reps") or 0)
        invalid_reps = int(ai_result.get("invalid_reps") or 0)
        errors = list(ai_result.get("errors") or [])
        camera_warnings = list(metrics.get("camera_warnings") or [])
        feedback = _feedback_text(ai_result, score)
        rep_history = list(ai_result.get("rep_history") or [])

        total_frames = int(metrics.get("total_frames") or 0)
        processed_frames = int(metrics.get("processed_frames") or 0)
        landmark_frames = int(metrics.get("landmark_frames") or 0)
        landmark_ratio = float(metrics.get("landmark_detection_ratio") or 0.0)
        mean_visibility = float(
            metrics.get("mean_landmark_visibility")
            or metrics.get("ai_confidence")
            or 0.0
        )
        average_movement = float(metrics.get("average_movement") or 0.0)
        duration_seconds = float(metrics.get("duration_seconds") or 0.0)
        confidence_percent = round(mean_visibility * 100.0, 1)
        selected_side = str(
            ai_result.get("selected_side")
            or metrics.get("selected_side")
            or "unavailable"
        )

        elapsed = round(time.time() - started, 3)
        logger.info("total_frames=%s", total_frames)
        logger.info("processed_frames=%s", processed_frames)
        logger.info("repetition_count=%s", repetition_count)
        logger.info("score=%s risk_percent=%s", score, risk_percent)
        logger.info("selected_side=%s", selected_side)
        logger.info("analysis_elapsed_seconds=%s", elapsed)
        logger.info("=== AI analysis end ===")

        details = {
            "average_motion": average_movement,
            "average_movement": average_movement,
            "total_frames": total_frames,
            "processed_frames": processed_frames,
            "landmark_frames": landmark_frames,
            "landmark_detection_ratio": landmark_ratio,
            "mean_landmark_visibility": mean_visibility,
            "ai_confidence": mean_visibility,
            "confidence_percent": confidence_percent,
            "duration_seconds": duration_seconds,
            "fps": metrics.get("fps"),
            "form_status": ai_result.get("form_status"),
            "valid_reps": valid_reps,
            "invalid_reps": invalid_reps,
            "current_state": ai_result.get("current_state"),
            "angles": ai_result.get("angles"),
            "quality": ai_result.get("quality") or metrics.get("quality"),
            "rep_history": rep_history,
            "min_knee_angle": ai_result.get("min_knee_angle"),
            "average_min_knee_angle": ai_result.get("average_min_knee_angle"),
            "knee_range_of_motion": ai_result.get("knee_range_of_motion"),
            "selected_side": selected_side,
            "risk_percent": risk_percent,
            "video_path": str(path),
            "analysis_elapsed_seconds": elapsed,
        }

        return {
            "status": "success",
            "exercise_name": exercise_name,
            "exercise": exercise_name,
            "accuracy": score,
            "average_motion": average_movement,
            "total_frames": total_frames,
            "score": score,
            "risk_percent": risk_percent,
            "repetition_count": repetition_count,
            "valid_reps": valid_reps,
            "invalid_reps": invalid_reps,
            "errors": errors,
            "camera_warnings": camera_warnings,
            "feedback": feedback,
            "details": details,
            "ai_confidence": mean_visibility,
            "confidence_percent": confidence_percent,
            "duration_seconds": duration_seconds,
            "processed_frames": processed_frames,
            "landmark_frames": landmark_frames,
            "landmark_detection_ratio": landmark_ratio,
            "mean_landmark_visibility": mean_visibility,
            "min_knee_angle": ai_result.get("min_knee_angle"),
            "average_min_knee_angle": ai_result.get("average_min_knee_angle"),
            "knee_range_of_motion": ai_result.get("knee_range_of_motion"),
            "selected_side": selected_side,
            "rep_history": rep_history,
        }

    except AnalysisError:
        logger.error("AnalysisError\n%s", traceback.format_exc())
        raise
    except VideoValidationError as exc:
        logger.error("VideoValidationError\n%s", traceback.format_exc())
        raise AnalysisError(str(exc), status_code=422) from exc
    except UnsupportedExerciseError as exc:
        logger.error("UnsupportedExerciseError\n%s", traceback.format_exc())
        raise AnalysisError(str(exc), status_code=400) from exc
    except FileNotFoundError as exc:
        logger.error("FileNotFoundError\n%s", traceback.format_exc())
        raise AnalysisError(str(exc), status_code=422) from exc
    except Exception as exc:
        logger.error("Unexpected analysis failure\n%s", traceback.format_exc())
        raise AnalysisError(
            f"Video analizi sirasinda hata olustu: {exc}",
            status_code=500,
        ) from exc
