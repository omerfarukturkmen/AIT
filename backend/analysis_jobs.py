"""Background video analysis and video retention.

Uploads return immediately with status "pending"; a worker thread runs the
analyzer and stores the full result, which clients poll via
GET /analysis/{id}. Workers live in this process: analyses that are still
running when the server stops are marked failed on the next start. For
several server processes, move the work to a queue (e.g. Celery or RQ).

VIDEO_RETENTION_DAYS (default 30) removes uploaded video files after that
many days; analysis results are kept. 0 keeps videos indefinitely.
"""

import json
import logging
import os
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import ai_analyzer
import models
from database import SessionLocal
from models import utcnow

logger = logging.getLogger("backend.jobs")

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploaded_videos")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ANALYSIS_WORKERS = int(os.environ.get("ANALYSIS_WORKERS", "2"))
VIDEO_RETENTION_DAYS = int(os.environ.get("VIDEO_RETENTION_DAYS", "30"))
RETENTION_CHECK_SECONDS = 6 * 60 * 60

PENDING_STATES = ("pending", "processing")

# Analyzer errors contain server paths and internals; clients get these.
SAFE_ANALYSIS_ERRORS = {
    400: "Bu hareket türü desteklenmiyor.",
    422: "Video okunamadı veya analiz için uygun değil. "
    "Lütfen net ve kısa bir video yükleyin.",
    503: "Analiz servisi şu an hazır değil. Lütfen daha sonra tekrar dene.",
}
ANALYSIS_FAILED = "Analiz sırasında beklenmeyen bir hata oluştu. Lütfen tekrar deneyin."
ANALYSIS_INTERRUPTED = (
    "Analiz yarıda kaldı çünkü sunucu yeniden başlatıldı. "
    "Lütfen videoyu tekrar yükle."
)

_executor = ThreadPoolExecutor(
    max_workers=ANALYSIS_WORKERS, thread_name_prefix="analysis"
)


def submit(analysis_id: int) -> None:
    _executor.submit(run_analysis, analysis_id)


def video_path(video: models.Video) -> str:
    return os.path.join(UPLOAD_FOLDER, os.path.basename(video.filename or ""))


def build_payload(
    analysis: models.AnalysisResult,
    video: models.Video,
    result: dict,
    elapsed: float,
) -> dict:
    """Response for a completed analysis (shape the app already parses)."""
    details = result.get("details") or {}
    average_motion = details.get("average_motion", details.get("average_movement", 0))
    return {
        "status": "success",
        "message": "Video başarıyla analiz edildi",
        "accuracy": result["score"],
        "exercise": result["exercise_name"],
        "feedback": result["feedback"],
        "average_motion": average_motion,
        "total_frames": details.get("total_frames", 0),
        "score": result["score"],
        "risk_percent": result.get("risk_percent", 0),
        "repetition_count": result["repetition_count"],
        "data": {
            "filename": video.filename,
            "video_id": video.id,
            "analysis_id": analysis.id,
            "user_id": video.owner_id,
            "exercise_type": analysis.exercise_type,
            "exercise_name": result["exercise_name"],
            "exercise": result["exercise_name"],
            "score": result["score"],
            "accuracy": result["score"],
            "risk_percent": result.get("risk_percent", 0),
            "repetition_count": result["repetition_count"],
            "valid_reps": result.get("valid_reps", 0),
            "invalid_reps": result.get("invalid_reps", 0),
            "analysis_status": "completed",
            "camera_warnings": result.get("camera_warnings", []),
            "errors": result["errors"],
            "feedback": result["feedback"],
            "average_motion": average_motion,
            "total_frames": details.get("total_frames", 0),
            "processed_frames": details.get("processed_frames", 0),
            "landmark_frames": details.get("landmark_frames", 0),
            "landmark_detection_ratio": details.get("landmark_detection_ratio", 0),
            "mean_landmark_visibility": details.get("mean_landmark_visibility", 0),
            "ai_confidence": details.get("ai_confidence", 0),
            "confidence_percent": details.get("confidence_percent", 0),
            "duration_seconds": details.get("duration_seconds", 0),
            "min_knee_angle": details.get("min_knee_angle"),
            "average_min_knee_angle": details.get("average_min_knee_angle"),
            "knee_range_of_motion": details.get("knee_range_of_motion"),
            "selected_side": details.get("selected_side", "unavailable"),
            "rep_history": details.get("rep_history", []),
            "details": details,
            "response_time_seconds": round(elapsed, 3),
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        },
    }


def _fail(analysis: models.AnalysisResult, message: str) -> None:
    analysis.status = "failed"
    analysis.feedback = message
    analysis.completed_at = utcnow()


def run_analysis(analysis_id: int) -> None:
    db = SessionLocal()
    try:
        analysis = db.get(models.AnalysisResult, analysis_id)
        if analysis is None:
            return
        video = db.get(models.Video, analysis.video_id)
        analysis.status = "processing"
        db.commit()

        started = time.time()
        try:
            result = ai_analyzer.analyze_video(video_path(video), analysis.exercise_type)
            if result.get("status") != "success":
                _fail(analysis, ANALYSIS_FAILED)
            else:
                payload = build_payload(analysis, video, result, time.time() - started)
                analysis.score = result["score"]
                analysis.repetition_count = result["repetition_count"]
                analysis.feedback = result["feedback"]
                analysis.status = "completed"
                analysis.completed_at = utcnow()
                analysis.result_json = json.dumps(payload, ensure_ascii=False, default=str)
        except ai_analyzer.AnalysisError as exc:
            logger.error("AnalysisError id=%s: %s\n%s", analysis_id, exc.message, traceback.format_exc())
            _fail(analysis, SAFE_ANALYSIS_ERRORS.get(exc.status_code, ANALYSIS_FAILED))
        except Exception:
            logger.error("Unexpected analysis error id=%s\n%s", analysis_id, traceback.format_exc())
            _fail(analysis, ANALYSIS_FAILED)
        db.commit()
    finally:
        db.close()


def fail_interrupted_analyses() -> int:
    """Marks analyses left pending by a previous server process as failed."""
    db = SessionLocal()
    try:
        stale = (
            db.query(models.AnalysisResult)
            .filter(models.AnalysisResult.status.in_(PENDING_STATES))
            .all()
        )
        for analysis in stale:
            _fail(analysis, ANALYSIS_INTERRUPTED)
        db.commit()
        if stale:
            logger.warning("marked %s interrupted analyses as failed", len(stale))
        return len(stale)
    finally:
        db.close()


def delete_expired_videos(retention_days: int | None = None) -> int:
    """Deletes video files older than the retention period; keeps results.

    Only videos uploaded since retention was introduced (they have
    created_at) are considered; older rows predate the policy.
    """
    days = VIDEO_RETENTION_DAYS if retention_days is None else retention_days
    if days <= 0:
        return 0

    cutoff = utcnow() - timedelta(days=days)
    db = SessionLocal()
    try:
        busy = (
            db.query(models.AnalysisResult.video_id)
            .filter(models.AnalysisResult.status.in_(PENDING_STATES))
        )
        expired = (
            db.query(models.Video)
            .filter(
                models.Video.created_at.is_not(None),
                models.Video.created_at < cutoff,
                models.Video.file_deleted_at.is_(None),
                models.Video.id.not_in(busy),
            )
            .all()
        )
        for video in expired:
            path = video_path(video)
            if os.path.isfile(path):
                os.remove(path)
            video.file_deleted_at = utcnow()
        db.commit()
        if expired:
            logger.info("retention: deleted %s video files", len(expired))
        return len(expired)
    finally:
        db.close()


def start_retention_worker() -> threading.Event:
    """Runs delete_expired_videos now and every 6 hours; returns a stop flag."""
    stop = threading.Event()

    def loop() -> None:
        while not stop.is_set():
            try:
                delete_expired_videos()
            except Exception:
                logger.exception("retention run failed")
            stop.wait(RETENTION_CHECK_SECONDS)

    threading.Thread(target=loop, name="video-retention", daemon=True).start()
    return stop
