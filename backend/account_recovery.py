"""Password reset and e-mail verification with short e-mailed codes.

Codes are 6 digits, stored only as an HMAC, valid for 15 minutes and
invalidated after 5 wrong attempts. Codes (not links) work the same on
mobile and web without deep-link setup.
"""

import hashlib
import hmac
import logging
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import auth
import mailer
import models
from models import utcnow
from rate_limit import RateLimiter, client_ip

logger = logging.getLogger("backend.account")

router = APIRouter(prefix="/auth", tags=["auth"])

PASSWORD_RESET = "password_reset"
EMAIL_VERIFICATION = "email_verification"
CODE_TTL = timedelta(minutes=15)
MAX_CODE_ATTEMPTS = 5

_reset_request_ip_limiter = RateLimiter("reset-request-ip", 5, 3600)
_reset_request_email_limiter = RateLimiter("reset-request-email", 3, 3600)
_reset_confirm_limiter = RateLimiter("reset-confirm", 10, 900)
_verify_request_limiter = RateLimiter("verify-request", 3, 3600)
_verify_confirm_limiter = RateLimiter("verify-confirm", 10, 900)

GENERIC_RESET_REPLY = (
    "Bu e-posta adresiyle kayıtlı bir hesap varsa doğrulama kodu gönderildi."
)
INVALID_CODE = "Kod geçersiz veya süresi dolmuş. Yeni bir kod isteyebilirsin."
MAIL_UNAVAILABLE = "E-posta gönderimi şu anda kullanılamıyor. Lütfen daha sonra tekrar dene."


class ResetRequest(BaseModel):
    email: str = Field(max_length=auth.MAX_EMAIL_LENGTH)


class ResetConfirm(BaseModel):
    email: str = Field(max_length=auth.MAX_EMAIL_LENGTH)
    code: str = Field(min_length=6, max_length=6)
    new_password: str = Field(max_length=auth.MAX_PASSWORD_LENGTH)


class VerifyConfirm(BaseModel):
    code: str = Field(min_length=6, max_length=6)


def _hash_code(code: str) -> str:
    return hmac.new(auth.SECRET_KEY, code.encode("ascii"), hashlib.sha256).hexdigest()


def issue_code(db: Session, user: models.User, purpose: str) -> str:
    """Replaces any open code of this purpose with a fresh one."""
    db.query(models.OneTimeCode).filter(
        models.OneTimeCode.user_id == user.id,
        models.OneTimeCode.purpose == purpose,
        models.OneTimeCode.used_at.is_(None),
    ).delete()
    code = f"{secrets.randbelow(1_000_000):06d}"
    now = utcnow()
    db.add(
        models.OneTimeCode(
            user_id=user.id,
            purpose=purpose,
            code_hash=_hash_code(code),
            created_at=now,
            expires_at=now + CODE_TTL,
        )
    )
    db.commit()
    return code


def check_code(db: Session, user: models.User, purpose: str, code: str) -> bool:
    record = (
        db.query(models.OneTimeCode)
        .filter(
            models.OneTimeCode.user_id == user.id,
            models.OneTimeCode.purpose == purpose,
            models.OneTimeCode.used_at.is_(None),
        )
        .order_by(models.OneTimeCode.id.desc())
        .first()
    )
    if record is None or record.expires_at < utcnow():
        return False
    if record.attempts >= MAX_CODE_ATTEMPTS:
        return False

    record.attempts += 1
    valid = code.isdigit() and hmac.compare_digest(record.code_hash, _hash_code(code))
    if valid:
        record.used_at = utcnow()
    db.commit()
    return valid


def _code_email(code: str, purpose: str) -> tuple[str, str]:
    if purpose == PASSWORD_RESET:
        subject = "AIT şifre sıfırlama kodu / Password reset code"
        intro_tr = "Şifreni sıfırlamak için kodun"
        intro_en = "Your password reset code is"
    else:
        subject = "AIT e-posta doğrulama kodu / E-mail verification code"
        intro_tr = "E-posta adresini doğrulamak için kodun"
        intro_en = "Your e-mail verification code is"
    body = (
        f"{intro_tr}: {code}\n"
        "Kod 15 dakika geçerlidir. Bu isteği sen yapmadıysan bu e-postayı yok sayabilirsin.\n\n"
        f"{intro_en}: {code}\n"
        "The code is valid for 15 minutes. If you did not request it, ignore this e-mail.\n"
    )
    return subject, body


def send_code(db: Session, user: models.User, purpose: str) -> None:
    code = issue_code(db, user, purpose)
    subject, body = _code_email(code, purpose)
    mailer.send_email(user.username, subject, body)


def send_verification_after_signup(db: Session, user: models.User) -> None:
    """Best effort: sign-up succeeds even if the e-mail cannot be sent."""
    try:
        send_code(db, user, EMAIL_VERIFICATION)
    except Exception:
        logger.exception("verification e-mail failed user_id=%s", user.id)


@router.post("/password-reset/request", status_code=202)
def request_password_reset(
    request: ResetRequest,
    http_request: Request,
    db: Session = Depends(auth.get_db),
):
    if not mailer.is_configured():
        raise HTTPException(status_code=503, detail=MAIL_UNAVAILABLE)

    email = auth.normalize_email(request.email)
    _reset_request_ip_limiter.check(client_ip(http_request))
    _reset_request_email_limiter.check(email)

    user = db.query(models.User).filter(models.User.username == email).first()
    if user is not None:
        try:
            send_code(db, user, PASSWORD_RESET)
        except Exception:
            # Same reply either way, so the response reveals nothing.
            logger.exception("password reset e-mail failed user_id=%s", user.id)
    return {"message": GENERIC_RESET_REPLY}


@router.post("/password-reset/confirm")
def confirm_password_reset(
    request: ResetConfirm,
    http_request: Request,
    db: Session = Depends(auth.get_db),
):
    _reset_confirm_limiter.check(client_ip(http_request))

    problem = auth.password_problem(request.new_password)
    if problem:
        raise HTTPException(status_code=422, detail=problem)

    email = auth.normalize_email(request.email)
    user = db.query(models.User).filter(models.User.username == email).first()
    if user is None or not check_code(db, user, PASSWORD_RESET, request.code):
        raise HTTPException(status_code=400, detail=INVALID_CODE)

    user.password_hash = auth.hash_password(request.new_password)
    # Receiving the code proves the user owns this address.
    user.email_verified = True
    # A reset usually follows a lost/stolen password: end every session.
    db.query(models.AuthSession).filter(
        models.AuthSession.user_id == user.id
    ).delete()
    db.commit()
    logger.info("password reset user_id=%s", user.id)
    return {"message": "Şifren değiştirildi. Yeni şifrenle giriş yapabilirsin."}


@router.post("/email-verification/request", status_code=202)
def request_email_verification(
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(auth.get_db),
):
    if user.email_verified:
        return {"message": "E-posta adresin zaten doğrulanmış."}
    if not mailer.is_configured():
        raise HTTPException(status_code=503, detail=MAIL_UNAVAILABLE)

    _verify_request_limiter.check(str(user.id))
    user = db.get(models.User, user.id)
    try:
        send_code(db, user, EMAIL_VERIFICATION)
    except Exception:
        logger.exception("verification e-mail failed user_id=%s", user.id)
        raise HTTPException(status_code=503, detail=MAIL_UNAVAILABLE)
    return {"message": "Doğrulama kodu e-posta adresine gönderildi."}


@router.post("/email-verification/confirm")
def confirm_email_verification(
    request: VerifyConfirm,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(auth.get_db),
):
    _verify_confirm_limiter.check(str(user.id))
    user = db.get(models.User, user.id)
    if not check_code(db, user, EMAIL_VERIFICATION, request.code):
        raise HTTPException(status_code=400, detail=INVALID_CODE)

    user.email_verified = True
    db.commit()
    return {"message": "E-posta adresin doğrulandı.", "email_verified": True}
