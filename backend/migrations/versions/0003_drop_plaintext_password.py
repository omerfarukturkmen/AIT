"""Drop the legacy plaintext users.password column.

Databases from before the auth rewrite still carry the original
(id, username, password) column. Nothing reads it any more and accounts
without a password_hash cannot sign in, so the plaintext values are only a
liability. The user rows themselves are kept.

Revision ID: 0003_drop_plaintext_password
Revises: 0002_product_features
Create Date: 2026-10-28
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_drop_plaintext_password"
down_revision = "0002_product_features"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("users")}
    if "password" in columns:
        with op.batch_alter_table("users") as batch:
            batch.drop_column("password")


def downgrade() -> None:
    # The plaintext values are intentionally not restored.
    pass
