import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class IncidentType(str, Enum):
    DOWNTIME = "downtime"
    DOUBLE_SIGNING = "double_signing"
    ORACLE_MANIPULATION = "oracle_manipulation"
    CONSENSUS_FAILURE = "consensus_failure"
    CENSORSHIP = "censorship"
    INCORRECT_AI_OUTPUT = "incorrect_ai_output"
    SLA_VIOLATION = "sla_violation"
    DATA_WITHHOLDING = "data_withholding"
    COORDINATED_ATTACK = "coordinated_attack"
    OTHER = "other"


class IncidentSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    AI_REVIEW = "ai_review"
    HUMAN_REVIEW = "human_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("operators.id", ondelete="SET NULL"), nullable=True
    )
    incident_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(50), default=IncidentSeverity.MEDIUM)
    status: Mapped[str] = mapped_column(String(50), default=IncidentStatus.OPEN, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    network: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    block_number: Mapped[int] = mapped_column(Integer, nullable=True)
    transaction_hash: Mapped[str] = mapped_column(String(100), nullable=True)

    # AI Analysis fields
    ai_fault_probability: Mapped[float] = mapped_column(Float, nullable=True)
    ai_severity_score: Mapped[float] = mapped_column(Float, nullable=True)
    ai_confidence_score: Mapped[float] = mapped_column(Float, nullable=True)
    ai_recommended_action: Mapped[str] = mapped_column(String(100), nullable=True)
    ai_analysis_summary: Mapped[str] = mapped_column(Text, nullable=True)
    ai_verdict_hash: Mapped[str] = mapped_column(String(100), nullable=True)

    # GenLayer on-chain references
    genlayer_tx_hash: Mapped[str] = mapped_column(String(100), nullable=True)

    raw_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    operator: Mapped["Operator"] = relationship("Operator", back_populates="incidents")
    evidence: Mapped[list["IncidentEvidence"]] = relationship(
        "IncidentEvidence", back_populates="incident"
    )
    slashing_cases: Mapped[list["SlashingCase"]] = relationship(
        "SlashingCase", back_populates="incident"
    )
    insurance_claims: Mapped[list["InsuranceClaim"]] = relationship(
        "InsuranceClaim", back_populates="incident"
    )


class IncidentEvidence(Base):
    __tablename__ = "incident_evidence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE")
    )
    evidence_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=True)
    on_chain_proof: Mapped[dict] = mapped_column(JSONB, default=dict)
    merkle_hash: Mapped[str] = mapped_column(String(100), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    incident: Mapped["Incident"] = relationship("Incident", back_populates="evidence")
