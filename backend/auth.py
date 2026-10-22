"""E-mail/password authentication.

Passwords are hashed with PBKDF2-HMAC-SHA256 (stdlib, no extra dependency).
Sessions use an HMAC-signed token that carries a random session id (jti);
the id is stored server-side so logout, account deletion and "log out
everywhere" revoke tokens immediately. Set AUTH_SECRET_KEY in the environment
for any shared/production deployment; otherwise a random key is generated at
startup and all tokens become invalid after a restart.
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
import unicodedata
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import SessionLocal
from rate_limit import RateLimiter, client_ip
import models

logger = logging.getLogger("backend.auth")

router = APIRouter(prefix="/auth", tags=["auth"])

PBKDF2_ITERATIONS = 390_000
REMEMBERED_SESSION_TTL = timedelta(days=30)
SHORT_SESSION_TTL = timedelta(hours=12)
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MAX_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 254
MAX_PASSWORD_LENGTH = 128

# Brute-force protection: per IP + e-mail, kept in memory (single process).
MAX_FAILED_LOGINS = 5
LOGIN_LOCKOUT_SECONDS = 15 * 60
_failed_logins: dict[str, list[float]] = {}

# Request volume limits per client IP (see rate_limit.py).
_register_limiter = RateLimiter("register", max_requests=5, window_seconds=3600)
_login_limiter = RateLimiter("login", max_requests=20, window_seconds=60)

_secret_from_env = os.environ.get("AUTH_SECRET_KEY")
if not _secret_from_env:
    # GEÇİCİ: Yalnızca yerel geliştirme için. Üretimde AUTH_SECRET_KEY zorunlu.
    logger.warning(
        "AUTH_SECRET_KEY tanımlı değil; geçici bir anahtar üretildi. "
        "Sunucu yeniden başlatıldığında tüm oturumlar geçersiz olur."
    )
SECRET_KEY = (_secret_from_env or secrets.token_urlsafe(48)).encode("utf-8")


class RegisterRequest(BaseModel):
    full_name: str = Field(max_length=MAX_NAME_LENGTH)
    email: str = Field(max_length=MAX_EMAIL_LENGTH)
    password: str = Field(max_length=MAX_PASSWORD_LENGTH)


class LoginRequest(BaseModel):
    email: str = Field(max_length=MAX_EMAIL_LENGTH)
    password: str = Field(max_length=MAX_PASSWORD_LENGTH)
    remember_me: bool = True


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


def _utcnow() -> datetime:
    # SQLite stores naive datetimes; keep everything in naive UTC.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_access_token(
    db: Session, user_id: int, ttl: timedelta = REMEMBERED_SESSION_TTL
) -> str:
    """Stores a new server-side session and returns its signed token."""
    now = _utcnow()
    expires_at = now + ttl
    jti = secrets.token_urlsafe(24)
    db.add(
        models.AuthSession(
            jti=jti, user_id=user_id, created_at=now, expires_at=expires_at
        )
    )
    db.commit()

    payload = json.dumps(
        {
            "sub": user_id,
            "jti": jti,
            "exp": int(expires_at.replace(tzinfo=timezone.utc).timestamp()),
        },
        separators=(",", ":"),
    ).encode("utf-8")
    body = _b64encode(payload)
    signature = hmac.new(SECRET_KEY, body.encode("ascii"), hashlib.sha256)
    return f"{body}.{_b64encode(signature.digest())}"


def decode_access_token(token: str) -> dict | None:
    """Returns the payload of a correctly signed, unexpired token."""
    try:
        body, signature = token.split(".")
        expected = hmac.new(SECRET_KEY, body.encode("ascii"), hashlib.sha256)
        if not hmac.compare_digest(_b64encode(expected.digest()), signature):
            return None
        payload = json.loads(_b64decode(body))
    except (ValueError, UnicodeError):
        return None

    if not isinstance(payload, dict) or payload.get("exp", 0) < time.time():
        return None
    if not isinstance(payload.get("sub"), int) or not payload.get("jti"):
        return None
    return payload


def _purge_expired_sessions(db: Session) -> None:
    db.query(models.AuthSession).filter(
        models.AuthSession.expires_at < _utcnow()
    ).delete()
    db.commit()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _name_problem(full_name: str) -> str | None:
    if len(full_name) < 2:
        return "Ad soyad gerekli."
    if any(unicodedata.category(char).startswith("C") for char in full_name):
        return "Ad soyad geçersiz karakter içeriyor."
    if not any(char.isalpha() for char in full_name):
        return "Ad soyad en az bir harf içermeli."
    return None


def _password_problem(password: str) -> str | None:
    if len(password) < 8:
        return "Şifre en az 8 karakter olmalı."
    if len(password) > MAX_PASSWORD_LENGTH:
        return "Şifre en fazla 128 karakter olabilir."
    if not re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]", password) or not re.search(
        r"\d", password
    ):
        return "Şifre en az bir harf ve bir rakam içermeli."
    return None


def _user_payload(user: models.User) -> dict:
    return {"id": user.id, "email": user.username, "full_name": user.full_name}


def _session_response(
    db: Session, user: models.User, ttl: timedelta = REMEMBERED_SESSION_TTL
) -> dict:
    return {
        "access_token": create_access_token(db, user.id, ttl),
        "token_type": "bearer",
        "expires_in": int(ttl.total_seconds()),
        "user": _user_payload(user),
    }


@router.post("/register", status_code=201)
def register(
    request: RegisterRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    _register_limiter.check(client_ip(http_request))

    full_name = " ".join(request.full_name.split())
    email = _normalize_email(request.email)

    problem = _name_problem(full_name)
    if problem:
        raise HTTPException(status_code=422, detail=problem)
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
    return _session_response(db, user)


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
    ip = client_ip(http_request)
    _login_limiter.check(ip)

    email = _normalize_email(request.email)
    limiter_key = f"{ip}|{email}"

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
        logger.warning("Başarısız giriş denemesi: ip=%s", ip)
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı.")

    _failed_logins.pop(limiter_key, None)
    _purge_expired_sessions(db)
    ttl = REMEMBERED_SESSION_TTL if request.remember_me else SHORT_SESSION_TTL
    return _session_response(db, user, ttl)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Oturum geçersiz. Lütfen tekrar giriş yap.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_session(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> models.AuthSession:
    """Resolves the Bearer token to a live server-side session or 401."""
    scheme, _, token = (authorization or "").partition(" ")
    payload = decode_access_token(token) if scheme.lower() == "bearer" else None
    if payload is None:
        raise _unauthorized()

    session = (
        db.query(models.AuthSession)
        .filter(models.AuthSession.jti == payload["jti"])
        .filter(models.AuthSession.user_id == payload["sub"])
        .first()
    )
    if session is None or session.expires_at < _utcnow():
        raise _unauthorized()
    return session


def get_current_user(
    session: models.AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> models.User:
    """FastAPI dependency: the signed-in user or 401."""
    user = db.get(models.User, session.user_id)
    if user is None:
        raise _unauthorized()
    return user


@router.get("/me")
def me(user: models.User = Depends(get_current_user)):
    return _user_payload(user)


@router.post("/logout", status_code=204)
def logout(
    all_devices: bool = False,
    session: models.AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    """Revokes this token, or every session of the user with all_devices."""
    query = db.query(models.AuthSession)
    if all_devices:
        query = query.filter(models.AuthSession.user_id == session.user_id)
    else:
        query = query.filter(models.AuthSession.id == session.id)
    query.delete()
    db.commit()
    return Response(status_code=204)
