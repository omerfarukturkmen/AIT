"""Google and Apple sign-in.

The app signs the user in with the provider and sends the provider's ID
token here; the token is verified against the provider's public keys
(signature, issuer, audience, expiry) before an AIT session is issued.

Configuration (comma-separated client ids = accepted token audiences):
- GOOGLE_CLIENT_IDS: OAuth client ids of the web, Android and iOS apps.
- APPLE_CLIENT_IDS: iOS bundle id (com.ait.fitness) and, for web/Android,
  the Sign in with Apple Services ID.
Without them the endpoints answer 503 ("not configured").
"""

import logging
import os

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import auth
import models
from rate_limit import RateLimiter, client_ip

logger = logging.getLogger("backend.social")

router = APIRouter(prefix="/auth", tags=["auth"])

PROVIDERS = {
    "google": {
        "label": "Google",
        "jwks_url": "https://www.googleapis.com/oauth2/v3/certs",
        "issuers": {"accounts.google.com", "https://accounts.google.com"},
        "client_ids_env": "GOOGLE_CLIENT_IDS",
    },
    "apple": {
        "label": "Apple",
        "jwks_url": "https://appleid.apple.com/auth/keys",
        "issuers": {"https://appleid.apple.com"},
        "client_ids_env": "APPLE_CLIENT_IDS",
    },
}

_social_limiter = RateLimiter("social-login", max_requests=20, window_seconds=60)
_jwk_clients: dict[str, jwt.PyJWKClient] = {}


class GoogleSignIn(BaseModel):
    id_token: str = Field(max_length=8192)
    remember_me: bool = True


class AppleSignIn(BaseModel):
    identity_token: str = Field(max_length=8192)
    # Apple sends the name to the app only on the very first sign-in.
    full_name: str | None = Field(default=None, max_length=auth.MAX_NAME_LENGTH)
    remember_me: bool = True


def client_ids(provider: str) -> list[str]:
    raw = os.environ.get(PROVIDERS[provider]["client_ids_env"], "")
    return [value.strip() for value in raw.split(",") if value.strip()]


def signing_key(provider: str, token: str):
    """Public key for the token's `kid`, from the provider's cached JWKS."""
    client = _jwk_clients.get(provider)
    if client is None:
        client = jwt.PyJWKClient(
            PROVIDERS[provider]["jwks_url"], cache_keys=True, lifespan=3600
        )
        _jwk_clients[provider] = client
    return client.get_signing_key_from_jwt(token).key


def verify_id_token(provider: str, token: str) -> dict:
    config = PROVIDERS[provider]
    audiences = client_ids(provider)
    if not audiences:
        raise HTTPException(
            status_code=503,
            detail=f"{config['label']} ile giriş henüz yapılandırılmadı.",
        )

    try:
        claims = jwt.decode(
            token,
            signing_key(provider, token),
            algorithms=["RS256"],
            audience=audiences,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except jwt.PyJWTError as exc:
        logger.warning("%s token rejected: %s", provider, type(exc).__name__)
        raise HTTPException(
            status_code=401,
            detail=f"{config['label']} oturumu doğrulanamadı. Lütfen tekrar dene.",
        )

    if claims.get("iss") not in config["issuers"]:
        raise HTTPException(
            status_code=401,
            detail=f"{config['label']} oturumu doğrulanamadı. Lütfen tekrar dene.",
        )
    return claims


def _email_verified(claims: dict) -> bool:
    # Google sends a boolean, Apple the string "true".
    return claims.get("email_verified") in (True, "true")


def _display_name(candidate: str | None, email: str) -> str:
    name = " ".join((candidate or "").split())
    if name and auth._name_problem(name) is None:
        return name
    return email.split("@")[0][: auth.MAX_NAME_LENGTH] or "AIT Kullanıcısı"


def sign_in(
    db: Session,
    provider: str,
    claims: dict,
    name: str | None,
    remember_me: bool,
) -> dict:
    subject = str(claims["sub"])
    identity = (
        db.query(models.SocialIdentity)
        .filter(
            models.SocialIdentity.provider == provider,
            models.SocialIdentity.subject == subject,
        )
        .first()
    )

    if identity is not None:
        user = db.get(models.User, identity.user_id)
    else:
        email = auth.normalize_email(claims.get("email") or "")
        if not email or not _email_verified(claims):
            raise HTTPException(
                status_code=401,
                detail="Bu hesabın e-posta adresi doğrulanmamış.",
            )
        user = db.query(models.User).filter(models.User.username == email).first()
        if user is None:
            user = models.User(
                username=email,
                full_name=_display_name(name, email),
                password_hash=None,
                email_verified=True,
            )
            db.add(user)
            db.flush()
            logger.info("Yeni kullanıcı kaydı (%s): id=%s", provider, user.id)
        else:
            # The provider has verified this address; link the accounts.
            user.email_verified = True
            logger.info("%s hesabı bağlandı: id=%s", provider, user.id)
        db.add(
            models.SocialIdentity(user_id=user.id, provider=provider, subject=subject)
        )
        db.commit()

    if user is None:
        raise HTTPException(status_code=401, detail="Hesap bulunamadı.")

    ttl = auth.REMEMBERED_SESSION_TTL if remember_me else auth.SHORT_SESSION_TTL
    return auth.session_response(db, user, ttl)


@router.post("/google")
def google_sign_in(
    request: GoogleSignIn,
    http_request: Request,
    db: Session = Depends(auth.get_db),
):
    _social_limiter.check(client_ip(http_request))
    claims = verify_id_token("google", request.id_token)
    return sign_in(db, "google", claims, claims.get("name"), request.remember_me)


@router.post("/apple")
def apple_sign_in(
    request: AppleSignIn,
    http_request: Request,
    db: Session = Depends(auth.get_db),
):
    _social_limiter.check(client_ip(http_request))
    claims = verify_id_token("apple", request.identity_token)
    return sign_in(db, "apple", claims, request.full_name, request.remember_me)
