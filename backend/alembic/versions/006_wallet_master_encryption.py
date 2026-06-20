"""Add master-key-encrypted wallet columns for server-side signing

Revision ID: 006
Revises: 005
Create Date: 2026-06-20
"""

from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("wallets", sa.Column("master_encrypted_private_key", sa.Text(), nullable=True))
    op.add_column("wallets", sa.Column("master_encryption_nonce", sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column("wallets", "master_encryption_nonce")
    op.drop_column("wallets", "master_encrypted_private_key")
