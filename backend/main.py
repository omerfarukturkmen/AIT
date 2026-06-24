from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
from ai_analyzer import analyze_video
from auth import router as auth_router
import models
import shutil
import os
import time

app = FastAPI()

app.include_router(auth_router)

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploaded_videos"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/")
def home():
    return {"message": "Backend çalışıyor"}


@app.post("/upload-video")
async def upload_video(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    exercise_type: str = Form(...)
):
    start_time = time.time()
    db = SessionLocal()

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Kullanıcı bulunamadı. Lütfen geçerli bir user_id gönderin."
        )

    if not file.filename:
        db.close()
        raise HTTPException(
            status_code=400,
            detail="Video dosyası seçilmedi. Lütfen bir video yükleyin."
        )

    if exercise_type not in ["squat", "push-up"]:
        db.close()
        raise HTTPException(
            status_code=400,
            detail="Desteklenen hareketler: squat, push-up"
        )

    allowed_extensions = [".mp4", ".mov", ".avi"]
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        db.close()
        raise HTTPException(
            status_code=400,
            detail="Geçersiz video formatı. Desteklenen formatlar: mp4, mov, avi"
        )

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    video = models.Video(
        filename=file.filename,
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

        if analysis_result["status"] != "success":
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

        db.close()

        return {
            "status": "success",
            "message": "Video başarıyla analiz edildi",
            "data": {
                "filename": file.filename,
                "video_id": video_id,
                "analysis_id": analysis_id,
                "user_id": user_id,
                "exercise_type": exercise_type,
                "exercise_name": analysis_result["exercise_name"],
                "score": analysis_result["score"],
                "repetition_count": analysis_result["repetition_count"],
                "analysis_status": analysis_status,
                "camera_warnings": analysis_result.get("camera_warnings", []),
                "errors": analysis_result["errors"],
                "feedback": analysis_result["feedback"],
                "details": analysis_result["details"],
                "response_time_seconds": response_time
            }
        }

    except HTTPException:
        raise

    except Exception:
        analysis.status = "failed"
        analysis.feedback = "Analiz sırasında beklenmeyen bir hata oluştu"
        db.commit()
        db.close()

        raise HTTPException(
            status_code=500,
            detail="Analiz sırasında beklenmeyen bir hata oluştu. Lütfen tekrar deneyin."
        )


@app.get("/user-videos/{user_id}")
def get_user_videos(user_id: int):
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
def get_analysis_history(user_id: int):
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
def get_analysis_detail(analysis_id: int):
    db = SessionLocal()

    result = (
        db.query(models.AnalysisResult, models.Video)
        .join(models.Video, models.AnalysisResult.video_id == models.Video.id)
        .filter(models.AnalysisResult.id == analysis_id)
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
def get_filtered_analysis_history(exercise_type: str | None = None):
    db = SessionLocal()

    query = (
        db.query(models.AnalysisResult, models.Video)
        .join(models.Video, models.AnalysisResult.video_id == models.Video.id)
    )

    if exercise_type:
        if exercise_type not in ["squat", "push-up"]:
            db.close()
            raise HTTPException(
                status_code=400,
                detail="Desteklenen filtreler: squat, push-up"
            )

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
    frame_data: str = Form(...)
):
    start_time = time.time()

    if exercise_type not in ["squat", "push-up"]:
        raise HTTPException(
            status_code=400,
            detail="Desteklenen hareketler: squat, push-up"
        )

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