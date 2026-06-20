import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SlashingStatus(str, Enum):
    PENDING = "pending"
    AI_ANALYSIS = "ai_analysis"
    RECOMMENDED = "recommended"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    APPEALED = "appealed"


class ReviewType(str, Enum):
    AI = "ai"
    HUMAN = "human"
    HYBRID = "hybrid"


class SlashingCase(Base):
    __tablename__ = "slashing_cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("operators.id", ondelete="SET NULL"), nullable=True
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True
    )
    case_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default=SlashingStatus.PENDING, index=True)
    review_type: Mapped[str] = mapped_column(String(50), default=ReviewType.AI)
    network: Mapped[str] = mapped_column(String(50), nullable=False)
    violation_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Amounts
    stake_at_risk: Mapped[float] = mapped_column(Float, default=0.0)
    recommended_slash_percentage: Mapped[float] = mapped_column(Float, nullable=True)
    recommended_slash_amount: Mapped[float] = mapped_column(Float, nullable=True)
    executed_slash_amount: Mapped[float] = mapped_column(Float, nullable=True)

    # AI scores
    ai_fault_probability: Mapped[float] = mapped_column(Float, nullable=True)
    ai_severity_score: Mapped[float] = mapped_column(Float, nullable=True)
    ai_confidence_score: Mapped[float] = mapped_column(Float, nullable=True)
    ai_rationale: Mapped[str] = mapped_column(Text, nullable=True)

    # On-chain
    on_chain_record_hash: Mapped[str] = mapped_column(String(100), nullable=True)
    genlayer_tx_hash: Mapped[str] = mapped_column(String(100), nullable=True)
    execution_tx_hash: Mapped[str] = mapped_column(String(100), nullable=True)

    appeal_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    operator: Mapped["Operator"] = relationship("Operator", back_populates="slashing_cases")
    incident: Mapped["Incident"] = relationship("Incident", back_populates="slashing_cases")
    recommendations: Mapped[list["SlashingRecommendation"]] = relationship(
        "SlashingRecommendation", back_populates="case"
    )


class SlashingRecommendation(Base):
    __tablename__ = "slashing_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("slashing_cases.id", ondelete="CASCADE")
    )
    recommended_by: Mapped[str] = mapped_column(String(50), nullable=False)  # "ai" or user_id
    slash_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    slash_amount: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_evidence: Mapped[dict] = mapped_column(JSONB, default=dict)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=True)
    is_final: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    case: Mapped["SlashingCase"] = relationship("SlashingCase", back_populates="recommendations")
