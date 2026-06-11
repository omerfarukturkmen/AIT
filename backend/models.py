from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

    exercise_type = Column(String)
    score = Column(Integer)
    repetition_count = Column(Integer)
    feedback = Column(String)