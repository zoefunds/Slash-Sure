import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ClaimStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    AI_ADJUDICATION = "ai_adjudication"
    APPROVED = "approved"
    REJECTED = "rejected"
    PARTIAL = "partial"
    PAID = "paid"
    APPEALED = "appealed"


class InsuranceClaim(Base):
    __tablename__ = "insurance_claims"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True
    )
    slashing_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("slashing_cases.id", ondelete="SET NULL"), nullable=True
    )
    claim_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default=ClaimStatus.SUBMITTED, index=True)
    claimant_address: Mapped[str] = mapped_column(String(100), nullable=False)
    policy_id: Mapped[str] = mapped_column(String(100), nullable=True)
    coverage_amount: Mapped[float] = mapped_column(Float, default=0.0)
    claimed_amount: Mapped[float] = mapped_column(Float, default=0.0)
    assessed_damage: Mapped[float] = mapped_column(Float, nullable=True)
    approved_amount: Mapped[float] = mapped_column(Float, nullable=True)

    # AI Adjudication
    ai_coverage_eligible: Mapped[bool] = mapped_column(nullable=True)
    ai_damage_assessment: Mapped[float] = mapped_column(Float, nullable=True)
    ai_payout_recommendation: Mapped[float] = mapped_column(Float, nullable=True)
    ai_confidence_score: Mapped[float] = mapped_column(Float, nullable=True)
    ai_adjudication_rationale: Mapped[str] = mapped_column(Text, nullable=True)
    ai_adjudication_hash: Mapped[str] = mapped_column(String(100), nullable=True)

    # On-chain
    on_chain_status_hash: Mapped[str] = mapped_column(String(100), nullable=True)
    genlayer_tx_hash: Mapped[str] = mapped_column(String(100), nullable=True)

    claim_details: Mapped[dict] = mapped_column(JSONB, default=dict)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    adjudicated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="insurance_claims"
    )
    incident: Mapped["Incident"] = relationship("Incident", back_populates="insurance_claims")
    payouts: Mapped[list["InsurancePayout"]] = relationship(
        "InsurancePayout", back_populates="claim"
    )


class InsurancePayout(Base):
    __tablename__ = "insurance_payouts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insurance_claims.id", ondelete="CASCADE")
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    recipient_address: Mapped[str] = mapped_column(String(100), nullable=False)
    token: Mapped[str] = mapped_column(String(20), default="GEN")
    status: Mapped[str] = mapped_column(String(50), default="pending")
    transaction_hash: Mapped[str] = mapped_column(String(100), nullable=True)
    genlayer_approval_hash: Mapped[str] = mapped_column(String(100), nullable=True)
    initiated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    claim: Mapped["InsuranceClaim"] = relationship("InsuranceClaim", back_populates="payouts")
