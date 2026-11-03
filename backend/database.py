import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLite for local development; production should use PostgreSQL, e.g.
# DATABASE_URL=postgresql+psycopg://user:password@host:5432/ait
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./test.db")

_is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    # SQLite connections are used from FastAPI's thread pool and the
    # analysis worker threads.
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    pool_pre_ping=not _is_sqlite,
)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()
