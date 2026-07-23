"""Scope operators by contract address.

Revision ID: 007
Revises: 006
Create Date: 2026-07-23
"""

from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("operators", sa.Column("contract_address", sa.String(length=100), nullable=True))
    op.create_index("ix_operators_contract_address", "operators", ["contract_address"])

    # Backfill from JSON metadata where available so current rows are immediately usable.
    op.execute(
        """
        UPDATE operators
        SET contract_address = metadata->>'contract_address'
        WHERE contract_address IS NULL
          AND metadata ? 'contract_address'
        """
    )

    # Drop legacy global uniqueness and replace it with contract-scoped uniqueness.
    op.execute("ALTER TABLE operators DROP CONSTRAINT IF EXISTS operators_address_key")
    op.create_unique_constraint(
        "uq_operators_address_contract_address",
        "operators",
        ["address", "contract_address"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_operators_address_contract_address", "operators", type_="unique")
    op.execute("ALTER TABLE operators ADD CONSTRAINT operators_address_key UNIQUE (address)")
    op.drop_index("ix_operators_contract_address", table_name="operators")
    op.drop_column("operators", "contract_address")
