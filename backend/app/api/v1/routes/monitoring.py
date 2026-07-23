import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routes.auth import get_current_user
from app.core.config import settings
from app.db.base import get_db
from app.models.monitoring import MonitoringEvent, Alert
from app.models.user import User

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


def _current_contract_address() -> str:
    return settings.GENLAYER_CONTRACT_ADDRESS.strip().lower()


def _operator_contract_address(operator) -> str:
    metadata = getattr(operator, "extra_metadata", None) or {}
    return str(metadata.get("contract_address", "")).strip().lower()


def _incident_contract_address(incident) -> str:
    return str((getattr(incident, "raw_data", None) or {}).get("contract_address", "")).strip().lower()


def _claim_contract_address(claim) -> str:
    return str((getattr(claim, "claim_details", None) or {}).get("contract_address", "")).strip().lower()


@router.get("/events")
async def list_events(
    network: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(MonitoringEvent).order_by(desc(MonitoringEvent.occurred_at))
    if network:
        query = query.where(MonitoringEvent.network == network)
    if event_type:
        query = query.where(MonitoringEvent.event_type == event_type)
    if severity:
        query = query.where(MonitoringEvent.severity == severity)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    events = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "network": e.network,
                "severity": e.severity,
                "summary": e.summary,
                "block_number": e.block_number,
                "processed": e.processed,
                "occurred_at": e.occurred_at,
            }
            for e in events
        ],
    }


@router.get("/alerts")
async def list_alerts(
    severity: Optional[str] = Query(None),
    acknowledged: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Alert).order_by(desc(Alert.created_at))
    if severity:
        query = query.where(Alert.severity == severity)
    if acknowledged is not None:
        query = query.where(Alert.is_acknowledged == acknowledged)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    alerts = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [
            {
                "id": str(a.id),
                "title": a.title,
                "message": a.message,
                "severity": a.severity,
                "network": a.network,
                "is_acknowledged": a.is_acknowledged,
                "created_at": a.created_at,
            }
            for a in alerts
        ],
    }


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import datetime, timezone
    result = await db.execute(select(Alert).where(Alert.id == uuid.UUID(alert_id)))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_acknowledged = True
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.now(timezone.utc)
    return {"acknowledged": True}


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.operator import Operator
    from app.models.incident import Incident
    from app.models.slashing import SlashingCase
    from app.models.insurance import InsuranceClaim

    operators_result = await db.execute(select(Operator))
    operators = [
        op for op in operators_result.scalars().all()
        if _operator_contract_address(op) == _current_contract_address()
    ]
    incidents_result = await db.execute(select(Incident))
    incidents = [
        incident for incident in incidents_result.scalars().all()
        if _incident_contract_address(incident) == _current_contract_address()
    ]
    claims_result = await db.execute(select(InsuranceClaim))
    claims = [
        claim for claim in claims_result.scalars().all()
        if _claim_contract_address(claim) == _current_contract_address()
    ]
    slashing_result = await db.execute(select(SlashingCase).join(Incident, Incident.id == SlashingCase.incident_id))
    slashing_cases = [
        case for case in slashing_result.scalars().all()
        if _incident_contract_address(case.incident) == _current_contract_address()
    ]

    total_operators = len(operators)
    active_operators = sum(1 for op in operators if op.status == "active")
    open_incidents = sum(1 for incident in incidents if incident.status in ["open", "ai_review", "under_review"])
    pending_slashing = sum(1 for case in slashing_cases if case.status == "pending")
    active_claims = sum(1 for claim in claims if claim.status in ["submitted", "under_review", "ai_adjudication"])
    unacknowledged_alerts = (await db.execute(
        select(func.count()).select_from(Alert).where(Alert.is_acknowledged.is_(False))
    )).scalar()

    # Network distribution: count active operators per network
    network_distribution: dict[str, int] = {}
    for op in operators:
        if op.status == "active":
            network_distribution[op.network] = network_distribution.get(op.network, 0) + 1

    # Hourly incident counts for last 24 hours (simplified: return empty list if no events)
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    hourly_stats = []
    for h in range(23, -1, -1):
        bucket_start = now - timedelta(hours=h + 1)
        bucket_end = now - timedelta(hours=h)
        inc_count = sum(
            1
            for incident in incidents
            if incident.detected_at and bucket_start <= incident.detected_at < bucket_end
        )
        hourly_stats.append({
            "hour": bucket_start.strftime("%H:%M"),
            "incidents": inc_count,
            "alerts": 0,
        })

    return {
        "total_operators": total_operators,
        "active_operators": active_operators,
        "open_incidents": open_incidents,
        "pending_slashing_cases": pending_slashing,
        "active_insurance_claims": active_claims,
        "unacknowledged_alerts": unacknowledged_alerts,
        "network_distribution": network_distribution,
        "hourly_stats": hourly_stats,
    }
