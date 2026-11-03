"""Applies Alembic migrations; called on app startup."""

from pathlib import Path

from alembic import command
from alembic.config import Config

from database import engine

_BACKEND_DIR = Path(__file__).resolve().parent


def upgrade_database() -> None:
    config = Config(str(_BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(_BACKEND_DIR / "migrations"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
