from fastapi import FastAPI, UploadFile, File, Form
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
    user_id: int = Form(...)
):
    db = SessionLocal()

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    analysis_result = analyze_video(file_path)

    video = models.Video(
        filename=file.filename,
        owner_id=user_id
    )

    db.add(video)
    db.commit()
    db.close()

    return {
    "status": "success",
    "filename": file.filename,
    "user_id": user_id,
    "analysis": analysis_result
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

    return result