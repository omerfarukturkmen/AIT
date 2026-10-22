"""E-mail/password authentication.

Passwords are hashed with PBKDF2-HMAC-SHA256 (stdlib, no extra dependency)
and sessions use a stateless HMAC-signed token. Set AUTH_SECRET_KEY in the
environment for any shared/production deployment; otherwise a random key is
generated at startup and all tokens become invalid after a restart.
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import SessionLocal
import models

logger = logging.getLogger("backend.auth")

router = APIRouter(prefix="/auth", tags=["auth"])

PBKDF2_ITERATIONS = 390_000
TOKEN_TTL_SECONDS = 60 * 60 * 24 * 30
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Brute-force protection: per IP + e-mail, kept in memory (single process).
MAX_FAILED_LOGINS = 5
LOGIN_LOCKOUT_SECONDS = 15 * 60
_failed_logins: dict[str, list[float]] = {}

_secret_from_env = os.environ.get("AUTH_SECRET_KEY")
if not _secret_from_env:
    # GEÇİCİ: Yalnızca yerel geliştirme için. Üretimde AUTH_SECRET_KEY zorunlu.
    logger.warning(
        "AUTH_SECRET_KEY tanımlı değil; geçici bir anahtar üretildi. "
        "Sunucu yeniden başlatıldığında tüm oturumlar geçersiz olur."
    )
SECRET_KEY = (_secret_from_env or secrets.token_urlsafe(48)).encode("utf-8")


class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_users_table(engine) -> None:
    """Adds auth columns to a users table created by the old schema."""
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("users")}
    missing = {
        "full_name": "VARCHAR",
        "password_hash": "VARCHAR",
        "created_at": "DATETIME",
    }
    with engine.begin() as connection:
        for name, sql_type in missing.items():
            if name not in existing:
                connection.execute(
                    text(f"ALTER TABLE users ADD COLUMN {name} {sql_type}")
                )


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS, salt.hex(), digest.hex()
    )


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False
    try:
        algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$")
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False

    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        int(iterations),
    )
    return hmac.compare_digest(candidate.hex(), digest_hex)


# Used to keep login timing similar for unknown e-mail addresses.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_access_token(user_id: int) -> str:
    payload = json.dumps(
        {"sub": user_id, "exp": int(time.time()) + TOKEN_TTL_SECONDS},
        separators=(",", ":"),
    ).encode("utf-8")
    body = _b64encode(payload)
    signature = hmac.new(SECRET_KEY, body.encode("ascii"), hashlib.sha256)
    return f"{body}.{_b64encode(signature.digest())}"


def decode_access_token(token: str) -> int | None:
    try:
        body, signature = token.split(".")
        expected = hmac.new(SECRET_KEY, body.encode("ascii"), hashlib.sha256)
        if not hmac.compare_digest(_b64encode(expected.digest()), signature):
            return None
        payload = json.loads(_b64decode(body))
    except (ValueError, UnicodeError):
        return None

    if payload.get("exp", 0) < time.time():
        return None
    return payload.get("sub")


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _password_problem(password: str) -> str | None:
    if len(password) < 8:
        return "Şifre en az 8 karakter olmalı."
    if len(password) > 128:
        return "Şifre en fazla 128 karakter olabilir."
    if not re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]", password) or not re.search(
        r"\d", password
    ):
        return "Şifre en az bir harf ve bir rakam içermeli."
    return None


def _user_payload(user: models.User) -> dict:
    return {"id": user.id, "email": user.username, "full_name": user.full_name}


def _session_response(user: models.User) -> dict:
    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer",
        "user": _user_payload(user),
    }


@router.post("/register", status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    full_name = " ".join(request.full_name.split())
    email = _normalize_email(request.email)

    if len(full_name) < 2:
        raise HTTPException(status_code=422, detail="Ad soyad gerekli.")
    if not EMAIL_PATTERN.match(email):
        raise HTTPException(
            status_code=422, detail="Geçerli bir e-posta adresi girin."
        )
    problem = _password_problem(request.password)
    if problem:
        raise HTTPException(status_code=422, detail=problem)

    if db.query(models.User).filter(models.User.username == email).first():
        raise HTTPException(
            status_code=409,
            detail="Bu e-posta adresiyle kayıtlı bir hesap zaten var.",
        )

    user = models.User(
        username=email,
        full_name=full_name,
        password_hash=hash_password(request.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Bu e-posta adresiyle kayıtlı bir hesap zaten var.",
        )
    db.refresh(user)

    logger.info("Yeni kullanıcı kaydı: id=%s", user.id)
    return _session_response(user)


def _recent_failures(key: str) -> list[float]:
    cutoff = time.time() - LOGIN_LOCKOUT_SECONDS
    attempts = [t for t in _failed_logins.get(key, []) if t > cutoff]
    if attempts:
        _failed_logins[key] = attempts
    else:
        _failed_logins.pop(key, None)
    return attempts


@router.post("/login")
def login(
    request: LoginRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    email = _normalize_email(request.email)
    client_ip = http_request.client.host if http_request.client else "unknown"
    limiter_key = f"{client_ip}|{email}"

    if len(_recent_failures(limiter_key)) >= MAX_FAILED_LOGINS:
        raise HTTPException(
            status_code=429,
            detail="Çok fazla hatalı deneme yapıldı. "
            "Lütfen 15 dakika sonra tekrar dene.",
        )

    user = db.query(models.User).filter(models.User.username == email).first()
    if user is None:
        verify_password(request.password, _DUMMY_HASH)
    if user is None or not verify_password(request.password, user.password_hash):
        _failed_logins.setdefault(limiter_key, []).append(time.time())
        logger.warning("Başarısız giriş denemesi: ip=%s", client_ip)
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı.")

    _failed_logins.pop(limiter_key, None)
    return _session_response(user)


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> models.User:
    """FastAPI dependency: resolves the Bearer token or responds 401."""
    scheme, _, token = (authorization or "").partition(" ")
    user_id = decode_access_token(token) if scheme.lower() == "bearer" else None
    user = db.get(models.User, user_id) if user_id is not None else None

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Oturum geçersiz. Lütfen tekrar giriş yap.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.get("/me")
def me(user: models.User = Depends(get_current_user)):
    return _user_payload(user)
