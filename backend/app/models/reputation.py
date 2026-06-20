import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReputationScore(Base):
    __tablename__ = "reputation_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("operators.id", ondelete="CASCADE"), unique=True
    )
    reliability_score: Mapped[float] = mapped_column(Float, default=100.0)
    security_score: Mapped[float] = mapped_column(Float, default=100.0)
    slashing_risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    insurance_premium_score: Mapped[float] = mapped_column(Float, default=1.0)
    overall_score: Mapped[float] = mapped_column(Float, default=100.0)

    # On-chain anchor
    on_chain_score_hash: Mapped[str] = mapped_column(String(100), nullable=True)
    genlayer_tx_hash: Mapped[str] = mapped_column(String(100), nullable=True)

    # Predictive risk
    predicted_failure_probability: Mapped[float] = mapped_column(Float, default=0.0)
    predicted_slash_probability: Mapped[float] = mapped_column(Float, default=0.0)
    risk_trend: Mapped[str] = mapped_column(String(20), default="stable")  # improving/stable/degrading

    score_breakdown: Mapped[dict] = mapped_column(JSONB, default=dict)
    last_calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    operator: Mapped["Operator"] = relationship("Operator", back_populates="reputation_score")
    history: Mapped[list["ReputationHistory"]] = relationship(
        "ReputationHistory", back_populates="reputation_score"
    )


class ReputationHistory(Base):
    __tablename__ = "reputation_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reputation_score_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reputation_scores.id", ondelete="CASCADE")
    )
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    reliability_score: Mapped[float] = mapped_column(Float, nullable=False)
    security_score: Mapped[float] = mapped_column(Float, nullable=False)
    slashing_risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    change_reason: Mapped[str] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    reputation_score: Mapped["ReputationScore"] = relationship(
        "ReputationScore", back_populates="history"
    )
