from fastapi import Depends, FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
from ai_analyzer import AnalysisError, analyze_video
from auth import get_current_user, migrate_users_table, router as auth_router
import models
import logging
import os
import time
import traceback
import uuid

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("backend")

app = FastAPI()

app.include_router(auth_router)

Base.metadata.create_all(bind=engine)
migrate_users_table(engine)

# Auth uses a Bearer header (no cookies), so credentials are not allowed.
# ALLOWED_ORIGINS: comma-separated list for deployed web clients; by default
# only localhost origins (Flutter web dev server) are accepted.
_allowed_origins = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=None
    if _allowed_origins
    else r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploaded_videos")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_MB", "200")) * 1024 * 1024

SUPPORTED_EXERCISES = {"squat", "push-up", "pushup", "push_up"}


def _normalize_incoming_exercise(exercise_type: str) -> str:
    value = (exercise_type or "").strip().lower().replace("_", "-")
    if value == "pushup":
        value = "push-up"
    if value not in {"squat", "push-up"}:
        raise HTTPException(
            status_code=400,
            detail="Desteklenen hareketler: squat, push-up",
        )
    return value


@app.get("/")
def home():
    return {"message": "Backend çalışıyor"}


@app.post("/upload-video")
async def upload_video(
    file: UploadFile = File(...),
    exercise_type: str = Form(...),
    current_user: models.User = Depends(get_current_user),
):
    start_time = time.time()
    # The owner always comes from the session token; a client-sent user_id
    # field is ignored so nobody can upload on behalf of another user.
    user_id = current_user.id
    db = SessionLocal()

    if not file.filename:
        db.close()
        raise HTTPException(
            status_code=400,
            detail="Video dosyası seçilmedi. Lütfen bir video yükleyin."
        )

    try:
        exercise_type = _normalize_incoming_exercise(exercise_type)
    except HTTPException:
        db.close()
        raise

    allowed_extensions = [".mp4", ".mov", ".avi"]
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        db.close()
        raise HTTPException(
            status_code=400,
            detail="Geçersiz video formatı. Desteklenen formatlar: mp4, mov, avi"
        )

    # Never use the client filename on disk (path traversal / overwrites).
    stored_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(UPLOAD_FOLDER, stored_filename)

    written = 0
    with open(file_path, "wb") as buffer:
        while chunk := file.file.read(1024 * 1024):
            written += len(chunk)
            if written > MAX_UPLOAD_BYTES:
                break
            buffer.write(chunk)

    if written > MAX_UPLOAD_BYTES:
        os.remove(file_path)
        db.close()
        raise HTTPException(
            status_code=413,
            detail=f"Video en fazla {MAX_UPLOAD_BYTES // (1024 * 1024)} MB olabilir.",
        )

    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    logger.info(
        "upload saved path=%s size=%s exercise_type=%s user_id=%s",
        file_path,
        file_size,
        exercise_type,
        user_id,
    )

    video = models.Video(
        filename=stored_filename,
        owner_id=user_id
    )

    db.add(video)
    db.commit()
    db.refresh(video)

    analysis = models.AnalysisResult(
        video_id=video.id,
        exercise_type=exercise_type,
        score=0,
        repetition_count=0,
        feedback="Analiz bekleniyor",
        status="pending"
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    try:
        analysis_result = analyze_video(file_path, exercise_type)

        if analysis_result.get("status") != "success":
            analysis.status = "failed"
            analysis.feedback = analysis_result.get(
                "message",
                "Analiz başarısız oldu"
            )
            db.commit()
            db.close()

            raise HTTPException(
                status_code=500,
                detail="Video analiz edilemedi. Lütfen daha net bir video yükleyin."
            )

        analysis.score = analysis_result["score"]
        analysis.repetition_count = analysis_result["repetition_count"]
        analysis.feedback = analysis_result["feedback"]
        analysis.status = "completed"

        db.commit()
        db.refresh(analysis)

        response_time = round(time.time() - start_time, 3)

        video_id = video.id
        analysis_id = analysis.id
        analysis_status = analysis.status
        details = analysis_result.get("details") or {}

        db.close()

        # Keep existing nested `data` schema and also expose Flutter legacy
        # fields so ApiService.AnalysisResult.fromJson can read real values.
        payload = {
            "status": "success",
            "message": "Video başarıyla analiz edildi",
            "accuracy": analysis_result["score"],
            "exercise": analysis_result["exercise_name"],
            "feedback": analysis_result["feedback"],
            "average_motion": details.get(
                "average_motion",
                details.get("average_movement", 0),
            ),
            "total_frames": details.get("total_frames", 0),
            "score": analysis_result["score"],
            "risk_percent": analysis_result.get("risk_percent", 0),
            "repetition_count": analysis_result["repetition_count"],
            "data": {
                "filename": stored_filename,
                "video_id": video_id,
                "analysis_id": analysis_id,
                "user_id": user_id,
                "exercise_type": exercise_type,
                "exercise_name": analysis_result["exercise_name"],
                "exercise": analysis_result["exercise_name"],
                "score": analysis_result["score"],
                "accuracy": analysis_result["score"],
                "risk_percent": analysis_result.get("risk_percent", 0),
                "repetition_count": analysis_result["repetition_count"],
                "valid_reps": analysis_result.get("valid_reps", 0),
                "invalid_reps": analysis_result.get("invalid_reps", 0),
                "analysis_status": analysis_status,
                "camera_warnings": analysis_result.get("camera_warnings", []),
                "errors": analysis_result["errors"],
                "feedback": analysis_result["feedback"],
                "average_motion": details.get(
                    "average_motion",
                    details.get("average_movement", 0),
                ),
                "total_frames": details.get("total_frames", 0),
                "processed_frames": details.get("processed_frames", 0),
                "landmark_frames": details.get("landmark_frames", 0),
                "landmark_detection_ratio": details.get(
                    "landmark_detection_ratio", 0
                ),
                "mean_landmark_visibility": details.get(
                    "mean_landmark_visibility", 0
                ),
                "ai_confidence": details.get("ai_confidence", 0),
                "confidence_percent": details.get("confidence_percent", 0),
                "duration_seconds": details.get("duration_seconds", 0),
                "min_knee_angle": details.get("min_knee_angle"),
                "average_min_knee_angle": details.get("average_min_knee_angle"),
                "knee_range_of_motion": details.get("knee_range_of_motion"),
                "selected_side": details.get("selected_side", "unavailable"),
                "rep_history": details.get("rep_history", []),
                "details": details,
                "response_time_seconds": response_time,
            },
        }
        return payload

    except HTTPException:
        raise

    except AnalysisError as exc:
        logger.error("AnalysisError: %s\n%s", exc.message, traceback.format_exc())
        analysis.status = "failed"
        analysis.feedback = exc.message
        db.commit()
        db.close()

        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )

    except Exception:
        logger.error("Unexpected upload-video error\n%s", traceback.format_exc())
        analysis.status = "failed"
        analysis.feedback = "Analiz sırasında beklenmeyen bir hata oluştu"
        db.commit()
        db.close()

        raise HTTPException(
            status_code=500,
            detail="Analiz sırasında beklenmeyen bir hata oluştu. Lütfen tekrar deneyin."
        )


def _require_same_user(user_id: int, current_user: models.User) -> None:
    if user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Bu kullanıcının verilerine erişim yetkin yok.",
        )


def _delete_videos(db, videos) -> None:
    """Removes videos, their analyses and the files on disk."""
    for video in videos:
        db.query(models.AnalysisResult).filter(
            models.AnalysisResult.video_id == video.id
        ).delete()
        file_path = os.path.join(UPLOAD_FOLDER, os.path.basename(video.filename or ""))
        if video.filename and os.path.isfile(file_path):
            os.remove(file_path)
        db.delete(video)


@app.delete("/videos/{video_id}")
def delete_video(
    video_id: int,
    current_user: models.User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        video = (
            db.query(models.Video)
            .filter(models.Video.id == video_id)
            .filter(models.Video.owner_id == current_user.id)
            .first()
        )
        if video is None:
            raise HTTPException(status_code=404, detail="Video bulunamadı.")
        _delete_videos(db, [video])
        db.commit()
    finally:
        db.close()

    logger.info("video deleted id=%s user_id=%s", video_id, current_user.id)
    return {"status": "success", "message": "Video ve analizleri silindi."}


@app.delete("/auth/me")
def delete_account(current_user: models.User = Depends(get_current_user)):
    """KVKK: deletes the account together with every video and analysis."""
    db = SessionLocal()
    try:
        videos = (
            db.query(models.Video)
            .filter(models.Video.owner_id == current_user.id)
            .all()
        )
        _delete_videos(db, videos)
        db.query(models.User).filter(models.User.id == current_user.id).delete()
        db.commit()
    finally:
        db.close()

    logger.info("account deleted user_id=%s", current_user.id)
    return {"status": "success", "message": "Hesabın ve tüm verilerin silindi."}


@app.get("/user-videos/{user_id}")
def get_user_videos(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
):
    _require_same_user(user_id, current_user)
    db = SessionLocal()

    videos = db.query(models.Video).filter(
        models.Video.owner_id == user_id
    ).all()

    result = []

    for video in videos:
        result.append({
            "id": video.id,
            "filename": video.filename
        })

    db.close()

    return result


@app.get("/user-analysis-history/{user_id}")
def get_analysis_history(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
):
    _require_same_user(user_id, current_user)
    db = SessionLocal()

    analyses = (
        db.query(models.AnalysisResult, models.Video)
        .join(models.Video, models.AnalysisResult.video_id == models.Video.id)
        .filter(models.Video.owner_id == user_id)
        .all()
    )

    result = []

    for analysis, video in analyses:
        result.append({
            "analysis_id": analysis.id,
            "video_id": video.id,
            "filename": video.filename,
            "exercise_type": analysis.exercise_type,
            "score": analysis.score,
            "repetition_count": analysis.repetition_count,
            "feedback": analysis.feedback,
            "status": analysis.status,
            "created_at": analysis.created_at
        })

    db.close()

    return {
        "status": "success",
        "user_id": user_id,
        "analysis_history": result
    }


@app.get("/analysis/{analysis_id}")
def get_analysis_detail(
    analysis_id: int,
    current_user: models.User = Depends(get_current_user),
):
    db = SessionLocal()

    # Other users' analyses answer 404 too, so IDs cannot be probed.
    result = (
        db.query(models.AnalysisResult, models.Video)
        .join(models.Video, models.AnalysisResult.video_id == models.Video.id)
        .filter(models.AnalysisResult.id == analysis_id)
        .filter(models.Video.owner_id == current_user.id)
        .first()
    )

    if not result:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Analiz bulunamadı. Lütfen geçerli bir analysis_id gönderin."
        )

    analysis, video = result

    response = {
        "status": "success",
        "data": {
            "analysis_id": analysis.id,
            "video_id": video.id,
            "filename": video.filename,
            "exercise_type": analysis.exercise_type,
            "score": analysis.score,
            "repetition_count": analysis.repetition_count,
            "feedback": analysis.feedback,
            "analysis_status": analysis.status,
            "created_at": analysis.created_at
        }
    }

    db.close()

    return response


@app.get("/analysis-history")
def get_filtered_analysis_history(
    exercise_type: str | None = None,
    current_user: models.User = Depends(get_current_user),
):
    db = SessionLocal()

    query = (
        db.query(models.AnalysisResult, models.Video)
        .join(models.Video, models.AnalysisResult.video_id == models.Video.id)
        .filter(models.Video.owner_id == current_user.id)
    )

    if exercise_type:
        try:
            exercise_type = _normalize_incoming_exercise(exercise_type)
        except HTTPException:
            db.close()
            raise

        query = query.filter(models.AnalysisResult.exercise_type == exercise_type)

    analyses = query.all()

    result = []

    for analysis, video in analyses:
        result.append({
            "analysis_id": analysis.id,
            "video_id": video.id,
            "filename": video.filename,
            "exercise_type": analysis.exercise_type,
            "score": analysis.score,
            "repetition_count": analysis.repetition_count,
            "feedback": analysis.feedback,
            "status": analysis.status,
            "created_at": analysis.created_at
        })

    db.close()

    return {
        "status": "success",
        "exercise_type_filter": exercise_type,
        "analysis_history": result
    }


@app.post("/live-analysis")
def live_analysis(
    exercise_type: str = Form(...),
    frame_data: str = Form(...),
    current_user: models.User = Depends(get_current_user),
):
    start_time = time.time()

    exercise_type = _normalize_incoming_exercise(exercise_type)

    if not frame_data:
        raise HTTPException(
            status_code=400,
            detail="Canlı analiz için frame_data gönderilmelidir."
        )

    camera_warnings = []

    if len(frame_data) < 20:
        camera_warnings.append(
            "Kamera görüntüsü yetersiz veya çok kısa veri gönderildi."
        )

    if exercise_type == "squat":
        feedback = "Squat canlı analiz verisi alındı."
    elif exercise_type == "push-up":
        feedback = "Push-up canlı analiz verisi alındı."
    else:
        feedback = "Canlı analiz verisi alındı."

    response_time = round(time.time() - start_time, 3)

    return {
        "status": "success",
        "message": "Canlı analiz verisi alındı",
        "data": {
            "exercise_type": exercise_type,
            "score": 70,
            "repetition_count": 0,
            "feedback": feedback,
            "camera_warnings": camera_warnings,
            "analysis_status": "completed",
            "response_time_seconds": response_time
        }
    }
