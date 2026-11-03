"""Store why a failed analysis failed, as a code the app can localize.

Revision ID: 0004_analysis_error_code
Revises: 0003_drop_plaintext_password
Create Date: 2026-11-03
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_analysis_error_code"
down_revision = "0003_drop_plaintext_password"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("analysis_results") as batch:
        batch.add_column(sa.Column("error_code", sa.String()))


def downgrade() -> None:
    with op.batch_alter_table("analysis_results") as batch:
        batch.drop_column("error_code")
