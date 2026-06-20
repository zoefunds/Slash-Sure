import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    address: Mapped[str] = mapped_column(String(42), unique=True, nullable=False, index=True)
    encrypted_private_key: Mapped[str] = mapped_column(Text, nullable=False)
    encryption_salt: Mapped[str] = mapped_column(String(64), nullable=False)
    encryption_nonce: Mapped[str] = mapped_column(String(64), nullable=False)
    master_encrypted_private_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    master_encryption_nonce: Mapped[str | None] = mapped_column(String(64), nullable=True)
    chain_id: Mapped[int] = mapped_column(default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="wallet")
