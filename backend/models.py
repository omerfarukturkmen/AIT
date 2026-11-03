from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from database import Base


def utcnow() -> datetime:
    """Naive UTC timestamp (SQLite stores datetimes without a zone)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # Holds the normalized (lowercase) e-mail address used to sign in.
    username = Column(String, unique=True)
    full_name = Column(String)
    # PBKDF2 hash produced by auth.hash_password; plaintext is never stored.
    # Empty for accounts created through Google/Apple sign-in.
    password_hash = Column(String)
    email_verified = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=utcnow)


class AuthSession(Base):
    """One signed-in device; deleting the row revokes its token."""

    __tablename__ = "auth_sessions"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)


class OneTimeCode(Base):
    """Short-lived code e-mailed for password reset or e-mail verification."""

    __tablename__ = "one_time_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    purpose = Column(String, nullable=False)
    # HMAC of the code; the code itself is never stored.
    code_hash = Column(String, nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime)


class SocialIdentity(Base):
    """Links a Google/Apple account (provider + subject id) to a user."""

    __tablename__ = "social_identities"
    __table_args__ = (UniqueConstraint("provider", "subject"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    provider = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utcnow)


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

    exercise_type = Column(String)
    score = Column(Integer)
    repetition_count = Column(Integer)
    feedback = Column(String)
    created_at = Column(DateTime, default=utcnow)
    # Set when the retention job removes the file; results are kept.
    file_deleted_at = Column(DateTime)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)

    video_id = Column(Integer, ForeignKey("videos.id"))

    exercise_type = Column(String)
    score = Column(Integer)
    repetition_count = Column(Integer)
    feedback = Column(String)

    # pending -> processing -> completed | failed
    status = Column(String, default="pending")

    created_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime)
    # Full response payload of a completed analysis (JSON).
    result_json = Column(Text)
    # Why a failed analysis failed (e.g. "video_too_short"); the app shows
    # it in the user's language. feedback holds the Turkish text.
    error_code = Column(String)
