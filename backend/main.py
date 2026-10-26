from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from database import SessionLocal
from account_recovery import router as account_router
from auth import get_current_user, router as auth_router
from rate_limit import RateLimitExceeded, RateLimiter, client_ip
from social_auth import router as social_router
import analysis_jobs
import json
import migrate
import models
import logging
import os
import re
import traceback
import uuid

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("backend")


class RedactSecretsFilter(logging.Filter):
    """Defense in depth: masks tokens/passwords if they ever reach a log."""

    _PATTERNS = (
        (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"), r"\1[REDACTED]"),
        (
            re.compile(
                r'(?i)("?(?:password|access_token|authorization)"?\s*[:=]\s*)'
                r'"?[^",\s}]+'
            ),
            r"\1[REDACTED]",
        ),
    )

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        redacted = message
        for pattern, replacement in self._PATTERNS:
            redacted = pattern.sub(replacement, redacted)
        if redacted != message:
            record.msg, record.args = redacted, ()
        return True


for _logger_name in ("", "uvicorn", "uvicorn.access", "uvicorn.error"):
    for _handler in logging.getLogger(_logger_name).handlers:
        _handler.addFilter(RedactSecretsFilter())

# APP_ENV=production hides the interactive API docs and enables HSTS.
IS_PRODUCTION = os.environ.get("APP_ENV", "development").lower() == "production"

# Schema changes are versioned with Alembic (backend/migrations).
migrate.upgrade_database()


@asynccontextmanager
async def _lifespan(app: FastAPI):
    analysis_jobs.fail_interrupted_analyses()
    stop_retention = analysis_jobs.start_retention_worker()
    yield
    stop_retention.set()


app = FastAPI(
    lifespan=_lifespan,
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json",
)

app.include_router(auth_router)
app.include_router(account_router)
app.include_router(social_router)

GENERIC_ERROR = "Beklenmeyen bir hata oluştu. Lütfen tekrar dene."


@app.exception_handler(RequestValidationError)
async def _validation_error_handler(request: Request, exc: RequestValidationError):
    # FastAPI's default body echoes the submitted values (passwords included);
    # return only the names of the invalid fields.
    fields = sorted(
        {str(error["loc"][-1]) for error in exc.errors() if error.get("loc")}
    )
    return JSONResponse(
        status_code=422,
        content={"detail": "Gönderilen veriler eksik veya geçersiz.", "fields": fields},
    )


@app.exception_handler(Exception)
async def _unhandled_error_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled error on %s %s\n%s",
        request.method,
        request.url.path,
        "".join(traceback.format_exception(exc)),
    )
    return JSONResponse(status_code=500, content={"detail": GENERIC_ERROR})


# The last middleware added is the outermost: CORS (added below) wraps the
# security headers, which wrap the rate limit, so 429s carry both.
_global_limiter = RateLimiter("global", max_requests=300, window_seconds=60)


@app.middleware("http")
async def _global_rate_limit(request: Request, call_next):
    if request.method != "OPTIONS":
        try:
            _global_limiter.check(client_ip(request))
        except RateLimitExceeded as exc:
            return JSONResponse(
                status_code=429, content={"detail": exc.detail}, headers=exc.headers
            )
    return await call_next(request)


@app.middleware("http")
async def _security_headers(request: Request, call_next):
    response = await call_next(request)
    headers = response.headers
    headers.setdefault("X-Content-Type-Options", "nosniff")
    headers.setdefault("X-Frame-Options", "DENY")
    headers.setdefault("Referrer-Policy", "no-referrer")
    headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    headers.setdefault("Cache-Control", "no-store")
    if not request.url.path.startswith(("/docs", "/redoc")):
        # JSON API: nothing may be loaded or framed from these responses.
        headers.setdefault(
            "Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'"
        )
    if IS_PRODUCTION:
        headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    return response


# ALLOWED_HOSTS: comma-separated host names the API answers to in production.
_allowed_hosts = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "").split(",")
    if host.strip()
]
if _allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts)

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

UPLOAD_FOLDER = analysis_jobs.UPLOAD_FOLDER
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_MB", "200")) * 1024 * 1024
MAX_FILENAME_LENGTH = 255
MAX_ACTIVE_ANALYSES_PER_USER = 3

_upload_limiter = RateLimiter("upload", max_requests=10, window_seconds=600)

# Container signatures: MP4/MOV are ISO-BMFF boxes, AVI is a RIFF file.
_ISO_BMFF_BOXES = {b"ftyp", b"moov", b"mdat", b"wide", b"free", b"skip", b"pnot"}


def _looks_like_video(header: bytes, extension: str) -> bool:
    if extension == ".avi":
        return header[:4] == b"RIFF" and header[8:12] == b"AVI "
    return len(header) >= 8 and header[4:8] in _ISO_BMFF_BOXES


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


@app.post("/upload-video", status_code=202)
async def upload_video(
    file: UploadFile = File(...),
    exercise_type: str = Form(..., max_length=32),
    current_user: models.User = Depends(get_current_user),
):
    """Stores the video and queues the analysis; poll GET /analysis/{id}."""
    # The owner always comes from the session token; a client-sent user_id
    # field is ignored so nobody can upload on behalf of another user.
    user_id = current_user.id
    _upload_limiter.check(str(user_id))

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Video dosyası seçilmedi. Lütfen bir video yükleyin.",
        )
    if len(file.filename) > MAX_FILENAME_LENGTH:
        raise HTTPException(status_code=400, detail="Dosya adı çok uzun.")

    exercise_type = _normalize_incoming_exercise(exercise_type)

    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in (".mp4", ".mov", ".avi"):
        raise HTTPException(
            status_code=400,
            detail="Geçersiz video formatı. Desteklenen formatlar: mp4, mov, avi",
        )

    db = SessionLocal()
    try:
        active = (
            db.query(models.AnalysisResult)
            .join(models.Video, models.AnalysisResult.video_id == models.Video.id)
            .filter(models.Video.owner_id == user_id)
            .filter(models.AnalysisResult.status.in_(analysis_jobs.PENDING_STATES))
            .count()
        )
        if active >= MAX_ACTIVE_ANALYSES_PER_USER:
            raise HTTPException(
                status_code=429,
                detail="Aynı anda en fazla 3 analiz yapılabilir. "
                "Lütfen devam edenlerin bitmesini bekle.",
            )

        # Never use the client filename on disk (path traversal / overwrites).
        stored_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(UPLOAD_FOLDER, stored_filename)

        written = 0
        header = b""
        with open(file_path, "wb") as buffer:
            while chunk := file.file.read(1024 * 1024):
                if not header:
                    header = chunk[:16]
                written += len(chunk)
                if written > MAX_UPLOAD_BYTES:
                    break
                buffer.write(chunk)

        rejection = None
        if written > MAX_UPLOAD_BYTES:
            rejection = HTTPException(
                status_code=413,
                detail=f"Video en fazla {MAX_UPLOAD_BYTES // (1024 * 1024)} MB olabilir.",
            )
        elif written == 0:
            rejection = HTTPException(status_code=400, detail="Video dosyası boş.")
        elif not _looks_like_video(header, file_extension):
            # The extension alone proves nothing (e.g. a renamed .exe).
            rejection = HTTPException(
                status_code=415,
                detail="Dosya geçerli bir video değil. Desteklenen formatlar: mp4, mov, avi",
            )
        if rejection is not None:
            os.remove(file_path)
            raise rejection

        logger.info(
            "upload saved file=%s size=%s exercise_type=%s user_id=%s",
            stored_filename,
            written,
            exercise_type,
            user_id,
        )

        video = models.Video(
            filename=stored_filename,
            owner_id=user_id,
            created_at=models.utcnow(),
        )
        db.add(video)
        db.flush()
        analysis = models.AnalysisResult(
            video_id=video.id,
            exercise_type=exercise_type,
            score=0,
            repetition_count=0,
            feedback="Analiz bekleniyor",
            status="pending",
            created_at=models.utcnow(),
        )
        db.add(analysis)
        db.commit()
        response = {
            "status": "pending",
            "message": "Video alındı, analiz ediliyor.",
            "data": {
                "analysis_id": analysis.id,
                "video_id": video.id,
                "filename": stored_filename,
                "user_id": user_id,
                "exercise_type": exercise_type,
                "analysis_status": "pending",
            },
        }
        analysis_id = analysis.id
    finally:
        db.close()

    analysis_jobs.submit(analysis_id)
    return response


def _analysis_summary(analysis: models.AnalysisResult, video: models.Video) -> dict:
    return {
        "analysis_id": analysis.id,
        "video_id": video.id,
        "exercise_type": analysis.exercise_type,
        "score": analysis.score,
        "repetition_count": analysis.repetition_count,
        "feedback": analysis.feedback,
        "analysis_status": analysis.status,
        "created_at": analysis.created_at,
        "completed_at": analysis.completed_at,
    }


def _owned_analysis(db, analysis_id: int, user: models.User):
    # Other users' analyses answer 404 too, so IDs cannot be probed.
    row = (
        db.query(models.AnalysisResult, models.Video)
        .join(models.Video, models.AnalysisResult.video_id == models.Video.id)
        .filter(models.AnalysisResult.id == analysis_id)
        .filter(models.Video.owner_id == user.id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Analiz bulunamadı.")
    return row


@app.get("/analysis/{analysis_id}")
def get_analysis_detail(
    analysis_id: int,
    current_user: models.User = Depends(get_current_user),
):
    """Polled by the app: pending/processing, failed, or the full result."""
    db = SessionLocal()
    try:
        analysis, video = _owned_analysis(db, analysis_id, current_user)
        if analysis.status == "completed" and analysis.result_json:
            return json.loads(analysis.result_json)
        return {"status": analysis.status, "data": _analysis_summary(analysis, video)}
    finally:
        db.close()


@app.get("/analyses")
def list_analyses(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: models.User = Depends(get_current_user),
):
    """The signed-in user's analyses, newest first, with full results."""
    db = SessionLocal()
    try:
        rows = (
            db.query(models.AnalysisResult, models.Video)
            .join(models.Video, models.AnalysisResult.video_id == models.Video.id)
            .filter(models.Video.owner_id == current_user.id)
            .order_by(models.AnalysisResult.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        items = []
        for analysis, video in rows:
            item = _analysis_summary(analysis, video)
            item["result"] = (
                json.loads(analysis.result_json) if analysis.result_json else None
            )
            items.append(item)
        return {"status": "success", "analyses": items}
    finally:
        db.close()


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
        file_path = analysis_jobs.video_path(video)
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
        for table in (
            models.AuthSession,
            models.OneTimeCode,
            models.SocialIdentity,
        ):
            db.query(table).filter(table.user_id == current_user.id).delete()
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
    try:
        videos = (
            db.query(models.Video).filter(models.Video.owner_id == user_id).all()
        )
        return [{"id": video.id, "filename": video.filename} for video in videos]
    finally:
        db.close()


@app.get("/user-analysis-history/{user_id}")
def get_analysis_history(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
):
    _require_same_user(user_id, current_user)
    db = SessionLocal()
    try:
        rows = (
            db.query(models.AnalysisResult, models.Video)
            .join(models.Video, models.AnalysisResult.video_id == models.Video.id)
            .filter(models.Video.owner_id == user_id)
            .all()
        )
        history = [
            {**_analysis_summary(analysis, video), "status": analysis.status}
            for analysis, video in rows
        ]
        return {"status": "success", "user_id": user_id, "analysis_history": history}
    finally:
        db.close()


@app.get("/analysis-history")
def get_filtered_analysis_history(
    exercise_type: str | None = Query(default=None, max_length=32),
    current_user: models.User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        query = (
            db.query(models.AnalysisResult, models.Video)
            .join(models.Video, models.AnalysisResult.video_id == models.Video.id)
            .filter(models.Video.owner_id == current_user.id)
        )
        if exercise_type:
            exercise_type = _normalize_incoming_exercise(exercise_type)
            query = query.filter(models.AnalysisResult.exercise_type == exercise_type)

        history = [
            {**_analysis_summary(analysis, video), "status": analysis.status}
            for analysis, video in query.all()
        ]
        return {
            "status": "success",
            "exercise_type_filter": exercise_type,
            "analysis_history": history,
        }
    finally:
        db.close()
