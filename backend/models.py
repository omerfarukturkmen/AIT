from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # Holds the normalized (lowercase) e-mail address used to sign in.
    username = Column(String, unique=True)
    full_name = Column(String)
    # PBKDF2 hash produced by auth.hash_password; plaintext is never stored.
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)



class AuthSession(Base):
    """One signed-in device; deleting the row revokes its token."""

    __tablename__ = "auth_sessions"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

    exercise_type = Column(String)
    score = Column(Integer)
    repetition_count = Column(Integer)
    feedback = Column(String)
    

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)

    video_id = Column(Integer, ForeignKey("videos.id"))

    exercise_type = Column(String)
    score = Column(Integer)
    repetition_count = Column(Integer)
    feedback = Column(String)

    status = Column(String, default="pending")

    created_at = Column(DateTime, default=datetime.utcnow)    