"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-20 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── organizations ────────────────────────────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("plan", sa.String(50), nullable=False, server_default="free"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("settings", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"])

    # ── users ────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("role", sa.String(50), nullable=False, server_default="viewer"),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("email_verification_token", sa.String(128), nullable=True),
        sa.Column("email_verification_expires", sa.DateTime(timezone=True), nullable=True),
        sa.Column("password_reset_token", sa.String(128), nullable=True),
        sa.Column("password_reset_expires", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_email_verification_token", "users", ["email_verification_token"])
    op.create_index("ix_users_password_reset_token", "users", ["password_reset_token"])

    # ── organization_members ─────────────────────────────────────────────────
    op.create_table(
        "organization_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="member"),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
    )

    # ── api_keys ─────────────────────────────────────────────────────────────
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("key_hash", sa.String(255), unique=True, nullable=False),
        sa.Column("key_prefix", sa.String(16), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("scopes", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"])

    # ── wallets ──────────────────────────────────────────────────────────────
    op.create_table(
        "wallets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("address", sa.String(100), unique=True, nullable=False),
        sa.Column("encrypted_private_key", sa.Text(), nullable=False),
        sa.Column("key_salt", sa.String(100), nullable=False),
        sa.Column("key_iv", sa.String(100), nullable=False),
        sa.Column("key_tag", sa.String(100), nullable=False),
        sa.Column("network", sa.String(50), nullable=False, server_default="ethereum"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_wallets_address", "wallets", ["address"])

    # ── operators ────────────────────────────────────────────────────────────
    op.create_table(
        "operators",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.String(100), unique=True, nullable=False),
        sa.Column("network", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("total_stake", sa.Float(), nullable=False, server_default="0"),
        sa.Column("commission_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("uptime_percentage", sa.Float(), nullable=False, server_default="100"),
        sa.Column("slash_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reputation_score", sa.Float(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("on_chain_registered", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("genlayer_tx_hash", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_operators_address", "operators", ["address"])
    op.create_index("ix_operators_network", "operators", ["network"])
    op.create_index("ix_operators_status", "operators", ["status"])

    # ── operator_networks ────────────────────────────────────────────────────
    op.create_table(
        "operator_networks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("operators.id", ondelete="CASCADE"), nullable=False),
        sa.Column("network", sa.String(50), nullable=False),
        sa.Column("stake", sa.Float(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("operator_id", "network", name="uq_operator_network"),
    )

    # ── reputation_scores ────────────────────────────────────────────────────
    op.create_table(
        "reputation_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("operators.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("uptime_score", sa.Float(), nullable=True),
        sa.Column("slash_penalty", sa.Float(), nullable=True),
        sa.Column("reliability_score", sa.Float(), nullable=True),
        sa.Column("network", sa.String(50), nullable=False),
        sa.Column("genlayer_tx_hash", sa.String(100), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_reputation_scores_operator_id", "reputation_scores", ["operator_id"])

    # ── reputation_history ───────────────────────────────────────────────────
    op.create_table(
        "reputation_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("operators.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("network", sa.String(50), nullable=False),
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
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("network", sa.String(50), nullable=False),
        sa.Column("block_number", sa.Integer(), nullable=True),
        sa.Column("transaction_hash", sa.String(100), nullable=True),
        sa.Column("ai_fault_probability", sa.Float(), nullable=True),
        sa.Column("ai_severity_score", sa.Float(), nullable=True),
        sa.Column("ai_confidence_score", sa.Float(), nullable=True),
        sa.Column("ai_recommended_action", sa.String(100), nullable=True),
        sa.Column("ai_analysis_summary", sa.Text(), nullable=True),
        sa.Column("ai_verdict_hash", sa.String(100), nullable=True),
        sa.Column("genlayer_tx_hash", sa.String(100), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_incidents_operator_id", "incidents", ["operator_id"])
    op.create_index("ix_incidents_status", "incidents", ["status"])
    op.create_index("ix_incidents_network", "incidents", ["network"])
    op.create_index("ix_incidents_severity", "incidents", ["severity"])

    # ── incident_evidence ────────────────────────────────────────────────────
    op.create_table(
        "incident_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(1000), nullable=True),
        sa.Column("on_chain_proof", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("merkle_hash", sa.String(100), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_incident_evidence_incident_id", "incident_evidence", ["incident_id"])

    # ── slashing_cases ───────────────────────────────────────────────────────
    op.create_table(
        "slashing_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_number", sa.String(50), unique=True, nullable=False),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("operators.id", ondelete="SET NULL"), nullable=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("review_type", sa.String(50), nullable=False, server_default="ai"),
        sa.Column("violation_type", sa.String(100), nullable=False),
        sa.Column("network", sa.String(50), nullable=False),
        sa.Column("stake_at_risk", sa.Float(), nullable=False, server_default="0"),
        sa.Column("recommended_slash_percentage", sa.Float(), nullable=True),
        sa.Column("recommended_slash_amount", sa.Float(), nullable=True),
        sa.Column("executed_slash_amount", sa.Float(), nullable=True),
        sa.Column("ai_fault_probability", sa.Float(), nullable=True),
        sa.Column("ai_severity_score", sa.Float(), nullable=True),
        sa.Column("ai_confidence_score", sa.Float(), nullable=True),
        sa.Column("ai_rationale", sa.Text(), nullable=True),
        sa.Column("on_chain_record_hash", sa.String(100), nullable=True),
        sa.Column("genlayer_tx_hash", sa.String(100), nullable=True),
        sa.Column("appeal_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_slashing_cases_case_number", "slashing_cases", ["case_number"])
    op.create_index("ix_slashing_cases_status", "slashing_cases", ["status"])
    op.create_index("ix_slashing_cases_network", "slashing_cases", ["network"])

    # ── slashing_recommendations ─────────────────────────────────────────────
    op.create_table(
        "slashing_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("slashing_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("slash_percentage", sa.Float(), nullable=False),
        sa.Column("slash_amount", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("genlayer_tx_hash", sa.String(100), nullable=True),
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
        sa.Column("coverage_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("claimed_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("assessed_damage", sa.Float(), nullable=True),
        sa.Column("approved_amount", sa.Float(), nullable=True),
        sa.Column("ai_coverage_eligible", sa.Boolean(), nullable=True),
        sa.Column("ai_damage_assessment", sa.Float(), nullable=True),
        sa.Column("ai_payout_recommendation", sa.Float(), nullable=True),
        sa.Column("ai_confidence_score", sa.Float(), nullable=True),
        sa.Column("ai_adjudication_rationale", sa.Text(), nullable=True),
        sa.Column("ai_adjudication_hash", sa.String(100), nullable=True),
        sa.Column("claim_details", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("genlayer_tx_hash", sa.String(100), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("adjudicated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_insurance_claims_claim_number", "insurance_claims", ["claim_number"])
    op.create_index("ix_insurance_claims_status", "insurance_claims", ["status"])

    # ── insurance_payouts ────────────────────────────────────────────────────
    op.create_table(
        "insurance_payouts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("insurance_claims.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("recipient_address", sa.String(100), nullable=False),
        sa.Column("token", sa.String(50), nullable=False, server_default="GEN"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("genlayer_approval_hash", sa.String(100), nullable=True),
        sa.Column("on_chain_tx_hash", sa.String(100), nullable=True),
        sa.Column("authorized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── monitoring_events ────────────────────────────────────────────────────
    op.create_table(
        "monitoring_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("operators.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False, server_default="low"),
        sa.Column("network", sa.String(50), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_monitoring_events_source", "monitoring_events", ["source"])
    op.create_index("ix_monitoring_events_event_type", "monitoring_events", ["event_type"])
    op.create_index("ix_monitoring_events_network", "monitoring_events", ["network"])

    # ── alert_rules ──────────────────────────────────────────────────────────
    op.create_table(
        "alert_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("rule_type", sa.String(100), nullable=False),
        sa.Column("network", sa.String(50), nullable=True),
        sa.Column("conditions", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("actions", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("severity", sa.String(50), nullable=False, server_default="medium"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ── alerts ───────────────────────────────────────────────────────────────
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("alert_rules.id", ondelete="SET NULL"), nullable=True),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("operators.id", ondelete="SET NULL"), nullable=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(50), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("network", sa.String(50), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_alerts_status", "alerts", ["status"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])

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
        sa.Column("request_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("alerts")
    op.drop_table("alert_rules")
    op.drop_table("monitoring_events")
    op.drop_table("insurance_payouts")
    op.drop_table("insurance_claims")
    op.drop_table("slashing_recommendations")
    op.drop_table("slashing_cases")
    op.drop_table("incident_evidence")
    op.drop_table("incidents")
    op.drop_table("reputation_history")
    op.drop_table("reputation_scores")
    op.drop_table("operator_networks")
    op.drop_table("operators")
    op.drop_table("wallets")
    op.drop_table("api_keys")
    op.drop_table("organization_members")
    op.drop_table("users")
    op.drop_table("organizations")
