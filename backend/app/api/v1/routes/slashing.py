import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.v1.routes.auth import get_current_user
from app.db.base import get_db
from app.models.slashing import SlashingCase, SlashingStatus
from app.models.user import User
from app.services.genlayer.client import genlayer_client
from app.services.genlayer.signer import get_user_private_key

router = APIRouter(prefix="/slashing", tags=["Slashing"])


class SlashingCaseCreate(BaseModel):
    incident_id: str
    operator_address: str
    violation_type: str
    network: str
    stake_at_risk: float


class SlashingApproval(BaseModel):
    approved: bool
    override_slash_percentage: Optional[float] = None
    reason: Optional[str] = None


@router.get("/")
async def list_cases(
    status: Optional[str] = Query(None),
    network: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(SlashingCase)
    if status:
        query = query.where(SlashingCase.status == status)
    if network:
        query = query.where(SlashingCase.network == network)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    query = query.order_by(SlashingCase.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    cases = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [
            {
                "id": str(c.id),
                "case_number": c.case_number,
                "status": c.status,
                "network": c.network,
                "violation_type": c.violation_type,
                "stake_at_risk": c.stake_at_risk,
                "recommended_slash_percentage": c.recommended_slash_percentage,
                "recommended_slash_amount": c.recommended_slash_amount,
                "ai_fault_probability": c.ai_fault_probability,
                "ai_severity_score": c.ai_severity_score,
                "ai_confidence_score": c.ai_confidence_score,
                "on_chain_record_hash": c.on_chain_record_hash,
                "genlayer_tx_hash": c.genlayer_tx_hash,
                "created_at": c.created_at,
            }
            for c in cases
        ],
    }


@router.post("/", status_code=201)
async def create_slashing_case(
    body: SlashingCaseCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import secrets
    case_number = f"SC-{secrets.token_hex(4).upper()}"
    case_id_str = str(uuid.uuid4())

    case = SlashingCase(
        id=uuid.UUID(case_id_str),
        case_number=case_number,
        operator_id=None,
        incident_id=uuid.UUID(body.incident_id),
        violation_type=body.violation_type,
        network=body.network,
        stake_at_risk=body.stake_at_risk,
        status=SlashingStatus.PENDING,
        review_type="ai",
    )
    db.add(case)
    await db.flush()

    background_tasks.add_task(
        _create_and_recommend_slashing,
        case_id_str,
        body.operator_address,
        body.incident_id,
        body.violation_type,
        body.network,
        int(body.stake_at_risk),
        str(current_user.id),
    )

    return {"id": case_id_str, "case_number": case_number, "status": "pending"}


async def _create_and_recommend_slashing(
    case_id: str,
    operator_address: str,
    incident_id: str,
    violation_type: str,
    network: str,
    stake_at_risk: int,
    user_id: str,
):
    from app.db.base import AsyncSessionLocal
    from sqlalchemy import update
    from app.models.slashing import SlashingCase

    async with AsyncSessionLocal() as db:
        signer_key = await get_user_private_key(user_id, db)
        try:
            await genlayer_client.create_slashing_case(
                case_id=case_id,
                operator_address=operator_address,
                incident_id=incident_id,
                violation_type=violation_type,
                network=network,
                stake_at_risk=stake_at_risk,
                signer_private_key=signer_key,
            )
            result = await genlayer_client.generate_slash_recommendation(
                case_id=case_id,
                evidence_summary=f"Violation type: {violation_type} on {network}",
                operator_history="Obtained from monitoring records",
                network_policy=f"{network} standard slashing policy",
                current_reputation=80,
                signer_private_key=signer_key,
            )
            await db.execute(
                update(SlashingCase)
                .where(SlashingCase.id == uuid.UUID(case_id))
                .values(
                    status=SlashingStatus.AI_ANALYSIS,
                    genlayer_tx_hash=result.get("tx_hash"),
                )
            )
            await db.commit()
        except Exception as e:
            from loguru import logger
            logger.error(f"Slashing case background processing failed: {case_id} — {e}")


@router.get("/{case_id}")
async def get_slashing_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(SlashingCase).where(SlashingCase.id == uuid.UUID(case_id)))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Slashing case not found")

    on_chain = await genlayer_client.call_view("get_slashing_case_summary", [case_id])

    return {
        "id": str(case.id),
        "case_number": case.case_number,
        "status": case.status,
        "network": case.network,
        "violation_type": case.violation_type,
        "stake_at_risk": case.stake_at_risk,
        "recommended_slash_percentage": case.recommended_slash_percentage,
        "recommended_slash_amount": case.recommended_slash_amount,
        "executed_slash_amount": case.executed_slash_amount,
        "ai_fault_probability": case.ai_fault_probability,
        "ai_severity_score": case.ai_severity_score,
        "ai_confidence_score": case.ai_confidence_score,
        "ai_rationale": case.ai_rationale,
        "on_chain_record_hash": case.on_chain_record_hash,
        "on_chain_data": on_chain,
        "genlayer_tx_hash": case.genlayer_tx_hash,
        "appeal_deadline": case.appeal_deadline,
        "created_at": case.created_at,
    }


@router.post("/{case_id}/approve")
async def approve_slashing(
    case_id: str,
    body: SlashingApproval,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(SlashingCase).where(SlashingCase.id == uuid.UUID(case_id)))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if body.approved:
        case.status = SlashingStatus.APPROVED
    else:
        case.status = SlashingStatus.REJECTED

    db.add(case)
    await db.commit()

    background_tasks.add_task(
        _approve_on_chain, case_id, body.approved, body.reason or "", str(current_user.id)
    )

    return {"case_id": case_id, "approved": body.approved, "status": case.status}


async def _approve_on_chain(case_id: str, approved: bool, reason: str, user_id: str) -> None:
    from app.db.base import AsyncSessionLocal
    from sqlalchemy import update
    async with AsyncSessionLocal() as db:
        signer_key = await get_user_private_key(user_id, db)
        fn = "approve_slashing" if approved else "reject_slashing"
        args = [case_id] if approved else [case_id, reason]
        tx = await genlayer_client.send_transaction(fn, args, signer_private_key=signer_key)
        if tx.get("tx_hash"):
            await db.execute(
                update(SlashingCase)
                .where(SlashingCase.id == uuid.UUID(case_id))
                .values(genlayer_tx_hash=tx["tx_hash"])
            )
            await db.commit()
