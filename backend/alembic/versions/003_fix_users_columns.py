"""fix users table: add missing columns, remove stale ones

Revision ID: 003
Revises: 002
Create Date: 2026-06-20
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns the model expects but the DB is missing
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))

    # Remove stale columns that are in the DB but not in the model
    op.drop_column("users", "is_superuser")
    op.drop_column("users", "role")
    op.drop_column("users", "organization_id")


def downgrade() -> None:
    op.drop_column("users", "email_verified_at")
    op.add_column("users", sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("users", sa.Column("role", sa.String(50), nullable=False, server_default="viewer"))
    op.add_column("users", sa.Column("organization_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
