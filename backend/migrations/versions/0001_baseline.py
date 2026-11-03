"""Baseline schema (auth, videos, analyses).

Databases created before Alembic (via Base.metadata.create_all and the old
migrate_users_table helper) have no alembic_version table, so this revision
is idempotent: it only creates missing tables and adds missing legacy
columns, and leaves existing data untouched.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-10-26
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _columns(table: str) -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    tables = _tables()

    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer, primary_key=True, index=True),
            sa.Column("username", sa.String, unique=True),
            sa.Column("full_name", sa.String),
            sa.Column("password_hash", sa.String),
            sa.Column("created_at", sa.DateTime),
        )
    else:
        # Pre-auth schema: (id, username, password).
        existing = _columns("users")
        with op.batch_alter_table("users") as batch:
            for name, type_ in (
                ("full_name", sa.String()),
                ("password_hash", sa.String()),
                ("created_at", sa.DateTime()),
            ):
                if name not in existing:
                    batch.add_column(sa.Column(name, type_))

    if "auth_sessions" not in tables:
        op.create_table(
            "auth_sessions",
            sa.Column("id", sa.Integer, primary_key=True, index=True),
            sa.Column("jti", sa.String, nullable=False, unique=True, index=True),
            sa.Column(
                "user_id",
                sa.Integer,
                sa.ForeignKey("users.id"),
                nullable=False,
                index=True,
            ),
            sa.Column("created_at", sa.DateTime, nullable=False),
            sa.Column("expires_at", sa.DateTime, nullable=False),
        )

    if "videos" not in tables:
        op.create_table(
            "videos",
            sa.Column("id", sa.Integer, primary_key=True, index=True),
            sa.Column("filename", sa.String),
            sa.Column("owner_id", sa.Integer, sa.ForeignKey("users.id")),
            sa.Column("exercise_type", sa.String),
            sa.Column("score", sa.Integer),
            sa.Column("repetition_count", sa.Integer),
            sa.Column("feedback", sa.String),
        )

    if "analysis_results" not in tables:
        op.create_table(
            "analysis_results",
            sa.Column("id", sa.Integer, primary_key=True, index=True),
            sa.Column("video_id", sa.Integer, sa.ForeignKey("videos.id")),
            sa.Column("exercise_type", sa.String),
            sa.Column("score", sa.Integer),
            sa.Column("repetition_count", sa.Integer),
            sa.Column("feedback", sa.String),
            sa.Column("status", sa.String),
            sa.Column("created_at", sa.DateTime),
        )


def downgrade() -> None:
    raise NotImplementedError("The baseline revision cannot be downgraded.")
