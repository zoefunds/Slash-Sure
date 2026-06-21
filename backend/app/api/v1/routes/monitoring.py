import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.v1.routes.auth import get_current_user
from app.db.base import get_db
from app.models.monitoring import MonitoringEvent, Alert, AlertRule
from app.models.user import User

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


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

    total_operators = (await db.execute(select(func.count()).select_from(Operator))).scalar()
    active_operators = (await db.execute(
        select(func.count()).select_from(Operator).where(Operator.status == "active")
    )).scalar()
    open_incidents = (await db.execute(
        select(func.count()).select_from(Incident).where(
            Incident.status.in_(["open", "ai_review", "under_review"])
        )
    )).scalar()
    pending_slashing = (await db.execute(
        select(func.count()).select_from(SlashingCase).where(SlashingCase.status == "pending")
    )).scalar()
    active_claims = (await db.execute(
        select(func.count()).select_from(InsuranceClaim).where(
            InsuranceClaim.status.in_(["submitted", "under_review", "ai_adjudication"])
        )
    )).scalar()
    unacknowledged_alerts = (await db.execute(
        select(func.count()).select_from(Alert).where(Alert.is_acknowledged == False)
    )).scalar()

    # Network distribution: count active operators per network
    from sqlalchemy import text as sa_text
    net_rows = (await db.execute(
        select(Operator.network, func.count().label("cnt"))
        .where(Operator.status == "active")
        .group_by(Operator.network)
    )).all()
    network_distribution = {row.network: row.cnt for row in net_rows}

    # Hourly incident counts for last 24 hours (simplified: return empty list if no events)
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    hourly_stats = []
    for h in range(23, -1, -1):
        bucket_start = now - timedelta(hours=h + 1)
        bucket_end = now - timedelta(hours=h)
        inc_count = (await db.execute(
            select(func.count()).select_from(Incident).where(
                Incident.detected_at >= bucket_start,
                Incident.detected_at < bucket_end,
            )
        )).scalar()
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
