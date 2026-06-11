from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
from ai_analyzer import analyze_video
import models
import shutil
import os

app = FastAPI()

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
    db = SessionLocal()

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")

    if not file.filename:
        db.close()
        raise HTTPException(status_code=400, detail="Video dosyası seçilmedi")

    allowed_extensions = [".mp4", ".mov", ".avi"]
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        db.close()
        raise HTTPException(status_code=400, detail="Geçersiz video formatı")

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    analysis_result = analyze_video(file_path, exercise_type)

    if analysis_result["status"] != "success":
        db.close()
        raise HTTPException(status_code=500, detail=analysis_result["message"])

    video = models.Video(
        filename=file.filename,
        owner_id=user_id,
        exercise_type=exercise_type,
        score=analysis_result["score"],
        repetition_count=analysis_result["repetition_count"],
        feedback=analysis_result["feedback"]
    )

    db.add(video)
    db.commit()
    db.close()

    return {
        "status": "success",
        "message": "Video başarıyla analiz edildi",
        "data": {
            "filename": file.filename,
            "user_id": user_id,
            "exercise_type": exercise_type,
            "exercise_name": analysis_result["exercise_name"],
            "score": analysis_result["score"],
            "repetition_count": analysis_result["repetition_count"],
            "errors": analysis_result["errors"],
            "feedback": analysis_result["feedback"],
            "details": analysis_result["details"]
        }
    }


@app.get("/user-videos/{user_id}")
def get_user_videos(user_id: int):
    db = SessionLocal()

    videos = db.query(models.Video).filter(
        models.Video.owner_id == user_id
    ).all()

    result = []

    for v in videos:
        result.append({
            "id": v.id,
            "filename": v.filename
        })

    db.close()

    return result


@app.get("/user-analysis-history/{user_id}")
def get_analysis_history(user_id: int):
    db = SessionLocal()

    videos = db.query(models.Video).filter(
        models.Video.owner_id == user_id
    ).all()

    result = []

    for video in videos:
        result.append({
            "video_id": video.id,
            "filename": video.filename,
            "exercise_type": video.exercise_type,
            "score": video.score,
            "repetition_count": video.repetition_count,
            "feedback": video.feedback
        })

    db.close()

    return {
        "status": "success",
        "user_id": user_id,
        "analysis_history": result
    }