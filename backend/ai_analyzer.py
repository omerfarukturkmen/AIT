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
from pose_detector import resolve_pose_model_path  # noqa: E402
from visibility_utils import ANALYSIS_STATUS_INSUFFICIENT_VISIBILITY  # noqa: E402
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

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 500,
        user_message: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        # Safe, specific text for the user; None = use the generic text.
        self.user_message = user_message


NO_PERSON_MESSAGE = (
    "Videoda vücudun net görünmedi. Telefonu sabitle, tüm vücudun "
    "kadrajda olsun ve iyi ışıkta tekrar çek."
)
NO_REPS_CODE = "no_completed_reps"
UNREADABLE_MESSAGE = (
    "Video açılamadı ya da eksik. Dosya bozuk olabilir; telefonunun "
    "kamerasıyla yeniden çekip tekrar yükle."
)
TOO_SHORT_MESSAGE = (
    "Video çok kısa. En az 2 saniyelik ve en az bir tam tekrar içeren "
    "bir video yükle."
)
PARTIAL_BODY_MESSAGE = (
    "Vücudunun bir kısmı (çoğunlukla ayaklar veya dizler) kadraj dışında "
    "kaldı. Telefonu biraz uzaklaştır, baştan ayağa görünecek şekilde çek."
)
LOW_FPS_WARNING = "Video kare hızı düşük; sonuçlar daha az güvenilir olabilir."
PARTIAL_BODY_WARNING = "Vücudun bazı karelerde tam görünmedi; sonuçları kontrol et."

# Thresholds measured on IMG_5512 variants (03.11.2026): an 8 fps copy still
# counted 2/2 reps; a copy cropped below the knees had 41% usable frames and
# lost one of two reps.
MIN_DURATION_SECONDS = 2.0
MIN_DECODED_FRAME_SHARE = 0.5
MIN_USABLE_FRAME_RATIO = 0.5
WARN_USABLE_FRAME_RATIO = 0.8
MIN_FPS = 5.0
WARN_FPS = 15.0


def _check_video_quality(
    ai_result: dict[str, Any], metrics: dict[str, Any]
) -> list[str]:
    """Stops on videos whose result would mislead; returns soft warnings.

    Order matters: a truncated or very short file is reported as such before
    it is judged on body visibility.
    """
    total = int(metrics.get("total_frames") or 0)
    reported = int(metrics.get("reported_frame_count") or 0)
    if reported > 0 and total < reported * MIN_DECODED_FRAME_SHARE:
        raise AnalysisError(
            f"Decoded {total} of {reported} frames", status_code=422,
            user_message=UNREADABLE_MESSAGE,
        )
    fps = float(metrics.get("fps") or 0.0)
    if 0.0 < fps < MIN_FPS:
        raise AnalysisError(
            f"Frame rate too low: {fps}", status_code=422,
            user_message=UNREADABLE_MESSAGE,
        )
    duration = float(metrics.get("duration_seconds") or 0.0)
    if 0.0 < duration < MIN_DURATION_SECONDS:
        raise AnalysisError(
            f"Video too short: {duration}s", status_code=422,
            user_message=TOO_SHORT_MESSAGE,
        )
    if ai_result.get("analysis_status") == ANALYSIS_STATUS_INSUFFICIENT_VISIBILITY:
        # No usable body landmarks in the whole video: nothing to score.
        raise AnalysisError(
            "No usable pose landmarks in the video", status_code=422,
            user_message=NO_PERSON_MESSAGE,
        )
    quality = metrics.get("quality") or {}
    usable = quality.get("usable_landmark_frame_ratio")
    warnings: list[str] = []
    if isinstance(usable, (int, float)):
        if usable < MIN_USABLE_FRAME_RATIO:
            raise AnalysisError(
                f"Only {usable:.0%} of pose frames had the required landmarks",
                status_code=422,
                user_message=PARTIAL_BODY_MESSAGE,
            )
        if usable < WARN_USABLE_FRAME_RATIO:
            warnings.append(PARTIAL_BODY_WARNING)
    if 0.0 < fps < WARN_FPS:
        warnings.append(LOW_FPS_WARNING)
    return warnings


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


def _select_score(
    ai_result: dict[str, Any],
    schema: dict[str, Any],
    metrics: dict[str, Any],
) -> tuple[int, dict[str, Any]]:
    """Prefer the analyzer's exercise-specific score (schema 1.0 ``score``).

    The squat/push-up analyzers score each finished rep on their own
    components (depth, alignment, tempo...). _compute_score is squat-shaped
    (knee depth) and capped push-ups at ~80, so it is only the fallback for
    videos without a finished rep.
    """
    schema_score = schema.get("score") if isinstance(schema, dict) else None
    schema_score = schema_score if isinstance(schema_score, dict) else {}
    components = dict(schema_score.get("components") or {})
    overall = schema_score.get("overall")
    completed = int(ai_result.get("valid_reps") or 0) + int(
        ai_result.get("invalid_reps") or 0
    )
    if completed == 0:
        # No finished rep means nothing was scored; a "43" here read as a
        # real (poor) result. The app shows the no_completed_reps issue.
        return 0, components
    if isinstance(overall, (int, float)):
        return max(0, min(100, int(round(overall)))), components
    return _compute_score(ai_result, metrics), components


def _is_missing_pose_model(exc: FileNotFoundError) -> bool:
    return "pose landmarker model" in str(exc).lower()


def warn_if_pose_model_missing() -> bool:
    """Logs a clear startup error when the pose model file is absent.

    Returns True when the model is present. Without it every analysis fails.
    """
    path = resolve_pose_model_path()
    if path.is_file():
        return True
    logger.error(
        "Pose model not found at %s: every analysis will fail. Run "
        "`python ai/scripts/download_pose_model.py` or set AIT_POSE_MODEL_PATH.",
        path,
    )
    return False


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
    logger.info("video_file=%s", path.name)
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

        # The flat per-rep fields (rep_count, valid_reps, rep_history, knee
        # angles...) live in domain_result; ai_result is the versioned
        # summary schema. Reading ai_result here reported 0 reps.
        ai_result = analysis.get("domain_result") or analysis["ai_result"]
        metrics = analysis["metrics"]
        quality_warnings = _check_video_quality(ai_result, metrics)
        schema = analysis.get("ai_result") or {}
        score, score_components = _select_score(ai_result, schema, metrics)
        top_feedback = list((schema.get("feedback") or {}).get("top") or [])
        risk_percent = max(0, min(100, 100 - score))
        repetition_count = int(ai_result.get("rep_count") or 0)
        valid_reps = int(ai_result.get("valid_reps") or 0)
        invalid_reps = int(ai_result.get("invalid_reps") or 0)
        errors = list(ai_result.get("errors") or [])
        if valid_reps + invalid_reps == 0 and NO_REPS_CODE not in errors:
            errors.insert(0, NO_REPS_CODE)
        camera_warnings = list(metrics.get("camera_warnings") or [])
        camera_warnings += [w for w in quality_warnings if w not in camera_warnings]
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
            "score_components": score_components,
            "top_feedback": top_feedback,
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
        raise AnalysisError(
            str(exc), status_code=422, user_message=UNREADABLE_MESSAGE
        ) from exc
    except UnsupportedExerciseError as exc:
        logger.error("UnsupportedExerciseError\n%s", traceback.format_exc())
        raise AnalysisError(str(exc), status_code=400) from exc
    except FileNotFoundError as exc:
        if _is_missing_pose_model(exc):
            # A server setup problem, not a bad video: say so in the logs and
            # do not tell the user their video is unreadable.
            logger.error(
                "Pose model missing; run ai/scripts/download_pose_model.py "
                "or set AIT_POSE_MODEL_PATH.\n%s",
                traceback.format_exc(),
            )
            raise AnalysisError(str(exc), status_code=503) from exc
        logger.error("FileNotFoundError\n%s", traceback.format_exc())
        raise AnalysisError(str(exc), status_code=422) from exc
    except Exception as exc:
        logger.error("Unexpected analysis failure\n%s", traceback.format_exc())
        raise AnalysisError(
            f"Video analizi sirasinda hata olustu: {exc}",
            status_code=500,
        ) from exc
