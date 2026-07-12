from fastapi import APIRouter, HTTPException
from database import SessionLocal
import models

router = APIRouter()

@router.post("/register")
def register(username: str, password: str):
    db = SessionLocal()

    user = models.User(username=username, password=password)
    db.add(user)
    db.commit()

    return {"message": "Kullanıcı oluşturuldu"}


@router.post("/login")
def login(username: str, password: str):
    db = SessionLocal()

    user = db.query(models.User).filter(
        models.User.username == username,
        models.User.password == password
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Hatalı giriş")

    return {"message": "Giriş başarılı"}