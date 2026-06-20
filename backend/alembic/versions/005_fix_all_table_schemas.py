"""Fix all table schemas to match current models exactly.

Migration 004 ran from a stale version of the file. This drops and
recreates every affected table with the correct columns.

Revision ID: 005
Revises: 004
Create Date: 2026-06-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None

TABLES_TO_FIX = [
    "audit_logs", "alerts", "alert_rules", "monitoring_events",
    "insurance_payouts", "insurance_claims", "slashing_recommendations",
    "slashing_cases", "incident_evidence", "incidents",
    "reputation_history", "reputation_scores",
    "wallets",
]


def upgrade() -> None:
    for table in TABLES_TO_FIX:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

    # ── wallets ──────────────────────────────────────────────────────────────
    op.create_table(
        "wallets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("address", sa.String(42), unique=True, nullable=False),
        sa.Column("encrypted_private_key", sa.Text, nullable=False),
        sa.Column("encryption_salt", sa.String(64), nullable=False),
        sa.Column("encryption_nonce", sa.String(64), nullable=False),
        sa.Column("chain_id", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_wallets_address", "wallets", ["address"])

    # ── reputation_scores ────────────────────────────────────────────────────
    op.create_table(
        "reputation_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("operators.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("reliability_score", sa.Float, nullable=False, server_default="100"),
        sa.Column("security_score", sa.Float, nullable=False, server_default="100"),
        sa.Column("slashing_risk_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("insurance_premium_score", sa.Float, nullable=False, server_default="1"),
        sa.Column("overall_score", sa.Float, nullable=False, server_default="100"),
        sa.Column("on_chain_score_hash", sa.String(100), nullable=True),
        sa.Column("genlayer_tx_hash", sa.String(100), nullable=True),
        sa.Column("predicted_failure_probability", sa.Float, nullable=False, server_default="0"),
        sa.Column("predicted_slash_probability", sa.Float, nullable=False, server_default="0"),
        sa.Column("risk_trend", sa.String(20), nullable=False, server_default="stable"),
        sa.Column("score_breakdown", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("last_calculated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── reputation_history ───────────────────────────────────────────────────
    op.create_table(
        "reputation_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("reputation_score_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reputation_scores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("overall_score", sa.Float, nullable=False),
        sa.Column("reliability_score", sa.Float, nullable=False),
        sa.Column("security_score", sa.Float, nullable=False),
        sa.Column("slashing_risk_score", sa.Float, nullable=False),
        sa.Column("change_reason", sa.Text, nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── incidents ────────────────────────────────────────────────────────────
    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("operators.id", ondelete="SET NULL"), nullable=True),
        sa.Column("incident_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(50), nullable=False, server_default="open"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("network", sa.String(50), nullable=False),
        sa.Column("block_number", sa.Integer, nullable=True),
        sa.Column("transaction_hash", sa.String(100), nullable=True),
        sa.Column("ai_fault_probability", sa.Float, nullable=True),
        sa.Column("ai_severity_score", sa.Float, nullable=True),
        sa.Column("ai_confidence_score", sa.Float, nullable=True),
        sa.Column("ai_recommended_action", sa.String(100), nullable=True),
        sa.Column("ai_analysis_summary", sa.Text, nullable=True),
        sa.Column("ai_verdict_hash", sa.String(100), nullable=True),
        sa.Column("genlayer_tx_hash", sa.String(100), nullable=True),
        sa.Column("raw_data", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_incidents_incident_type", "incidents", ["incident_type"])
    op.create_index("ix_incidents_status", "incidents", ["status"])
    op.create_index("ix_incidents_network", "incidents", ["network"])

    # ── incident_evidence ────────────────────────────────────────────────────
    op.create_table(
        "incident_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("source_url", sa.String(1000), nullable=True),
        sa.Column("on_chain_proof", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("merkle_hash", sa.String(100), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── slashing_cases ───────────────────────────────────────────────────────
    op.create_table(
        "slashing_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("operators.id", ondelete="SET NULL"), nullable=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("case_number", sa.String(50), unique=True, nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("review_type", sa.String(50), nullable=False, server_default="ai"),
        sa.Column("network", sa.String(50), nullable=False),
        sa.Column("violation_type", sa.String(100), nullable=False),
        sa.Column("stake_at_risk", sa.Float, nullable=False, server_default="0"),
        sa.Column("recommended_slash_percentage", sa.Float, nullable=True),
        sa.Column("recommended_slash_amount", sa.Float, nullable=True),
        sa.Column("executed_slash_amount", sa.Float, nullable=True),
        sa.Column("ai_fault_probability", sa.Float, nullable=True),
        sa.Column("ai_severity_score", sa.Float, nullable=True),
        sa.Column("ai_confidence_score", sa.Float, nullable=True),
        sa.Column("ai_rationale", sa.Text, nullable=True),
        sa.Column("on_chain_record_hash", sa.String(100), nullable=True),
        sa.Column("genlayer_tx_hash", sa.String(100), nullable=True),
        sa.Column("execution_tx_hash", sa.String(100), nullable=True),
        sa.Column("appeal_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_slashing_cases_case_number", "slashing_cases", ["case_number"])
    op.create_index("ix_slashing_cases_status", "slashing_cases", ["status"])

    # ── slashing_recommendations ─────────────────────────────────────────────
    op.create_table(
        "slashing_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("slashing_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recommended_by", sa.String(50), nullable=False),
        sa.Column("slash_percentage", sa.Float, nullable=False),
        sa.Column("slash_amount", sa.Float, nullable=False),
        sa.Column("rationale", sa.Text, nullable=False),
        sa.Column("supporting_evidence", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("is_final", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── insurance_claims ─────────────────────────────────────────────────────
    op.create_table(
        "insurance_claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("slashing_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("slashing_cases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("claim_number", sa.String(50), unique=True, nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="submitted"),
        sa.Column("claimant_address", sa.String(100), nullable=False),
        sa.Column("policy_id", sa.String(100), nullable=True),
        sa.Column("coverage_amount", sa.Float, nullable=False, server_default="0"),
        sa.Column("claimed_amount", sa.Float, nullable=False, server_default="0"),
        sa.Column("assessed_damage", sa.Float, nullable=True),
        sa.Column("approved_amount", sa.Float, nullable=True),
        sa.Column("ai_coverage_eligible", sa.Boolean(), nullable=True),
        sa.Column("ai_damage_assessment", sa.Float, nullable=True),
        sa.Column("ai_payout_recommendation", sa.Float, nullable=True),
        sa.Column("ai_confidence_score", sa.Float, nullable=True),
        sa.Column("ai_adjudication_rationale", sa.Text, nullable=True),
        sa.Column("ai_adjudication_hash", sa.String(100), nullable=True),
        sa.Column("on_chain_status_hash", sa.String(100), nullable=True),
        sa.Column("genlayer_tx_hash", sa.String(100), nullable=True),
        sa.Column("claim_details", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("adjudicated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_insurance_claims_claim_number", "insurance_claims", ["claim_number"])
    op.create_index("ix_insurance_claims_status", "insurance_claims", ["status"])

    # ── insurance_payouts ────────────────────────────────────────────────────
    op.create_table(
        "insurance_payouts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("insurance_claims.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Float, nullable=False),
        sa.Column("recipient_address", sa.String(100), nullable=False),
        sa.Column("token", sa.String(20), nullable=False, server_default="GEN"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("transaction_hash", sa.String(100), nullable=True),
        sa.Column("genlayer_approval_hash", sa.String(100), nullable=True),
        sa.Column("initiated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── monitoring_events ────────────────────────────────────────────────────
    op.create_table(
        "monitoring_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("operators.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("network", sa.String(50), nullable=False),
        sa.Column("block_number", sa.Integer, nullable=True),
        sa.Column("transaction_hash", sa.String(100), nullable=True),
        sa.Column("severity", sa.String(50), nullable=False, server_default="low"),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("raw_payload", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("incident_created", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_monitoring_events_event_type", "monitoring_events", ["event_type"])
    op.create_index("ix_monitoring_events_network", "monitoring_events", ["network"])
    op.create_index("ix_monitoring_events_occurred_at", "monitoring_events", ["occurred_at"])

    # ── alert_rules ──────────────────────────────────────────────────────────
    op.create_table(
        "alert_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("event_type", sa.String(100), nullable=True),
        sa.Column("network", sa.String(50), nullable=True),
        sa.Column("severity_threshold", sa.String(50), nullable=False, server_default="medium"),
        sa.Column("conditions", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("notification_channels", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("cooldown_minutes", sa.Integer, nullable=False, server_default="15"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── alerts ───────────────────────────────────────────────────────────────
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("alert_rules.id", ondelete="SET NULL"), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("operators.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("network", sa.String(50), nullable=True),
        sa.Column("is_acknowledged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("acknowledged_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notification_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("extra_data", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── audit_logs ───────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("request_data", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("response_status", sa.Integer, nullable=True),
        sa.Column("details", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    for table in TABLES_TO_FIX:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
