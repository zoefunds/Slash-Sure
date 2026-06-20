import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class NetworkType(str, Enum):
    EIGENLAYER = "eigenlayer"
    SYMBIOTIC = "symbiotic"
    BABYLON = "babylon"
    COSMOS = "cosmos"
    OTHER = "other"


class OperatorStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    JAILED = "jailed"
    SLASHED = "slashed"
    SUSPENDED = "suspended"


class Operator(Base):
    __tablename__ = "operators"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    network: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default=OperatorStatus.ACTIVE)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    website: Mapped[str] = mapped_column(String(500), nullable=True)
    logo_url: Mapped[str] = mapped_column(String(500), nullable=True)
    total_stake: Mapped[float] = mapped_column(Float, default=0.0)
    delegator_count: Mapped[int] = mapped_column(Integer, default=0)
    commission_rate: Mapped[float] = mapped_column(Float, default=0.0)
    uptime_percentage: Mapped[float] = mapped_column(Float, default=100.0)
    slash_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    on_chain_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="operators")
    networks: Mapped[list["OperatorNetwork"]] = relationship(
        "OperatorNetwork", back_populates="operator"
    )
    incidents: Mapped[list["Incident"]] = relationship("Incident", back_populates="operator")
    reputation_score: Mapped["ReputationScore"] = relationship(
        "ReputationScore", back_populates="operator", uselist=False
    )
    slashing_cases: Mapped[list["SlashingCase"]] = relationship(
        "SlashingCase", back_populates="operator"
    )


class OperatorNetwork(Base):
    __tablename__ = "operator_networks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("operators.id", ondelete="CASCADE")
    )
    network: Mapped[str] = mapped_column(String(50), nullable=False)
    avs_address: Mapped[str] = mapped_column(String(100), nullable=True)
    avs_name: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    stake_amount: Mapped[float] = mapped_column(Float, default=0.0)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    operator: Mapped["Operator"] = relationship("Operator", back_populates="networks")
