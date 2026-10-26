"""E-mail verification, one-time codes, social sign-in, background analysis
and video retention.

Revision ID: 0002_product_features
Revises: 0001_baseline
Create Date: 2026-10-26
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_product_features"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(
            sa.Column(
                "email_verified",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )

    with op.batch_alter_table("videos") as batch:
        batch.add_column(sa.Column("created_at", sa.DateTime()))
        batch.add_column(sa.Column("file_deleted_at", sa.DateTime()))

    with op.batch_alter_table("analysis_results") as batch:
        batch.add_column(sa.Column("completed_at", sa.DateTime()))
        batch.add_column(sa.Column("result_json", sa.Text()))

    op.create_table(
        "one_time_codes",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("purpose", sa.String, nullable=False),
        sa.Column("code_hash", sa.String, nullable=False),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("used_at", sa.DateTime),
    )

    op.create_table(
        "social_identities",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("provider", sa.String, nullable=False),
        sa.Column("subject", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("provider", "subject"),
    )


def downgrade() -> None:
    op.drop_table("social_identities")
    op.drop_table("one_time_codes")
    with op.batch_alter_table("analysis_results") as batch:
        batch.drop_column("result_json")
        batch.drop_column("completed_at")
    with op.batch_alter_table("videos") as batch:
        batch.drop_column("file_deleted_at")
        batch.drop_column("created_at")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("email_verified")
