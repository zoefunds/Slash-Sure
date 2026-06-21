import asyncio
import hashlib
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.v1.routes.auth import get_current_user
from app.db.base import get_db
from app.models.incident import Incident, IncidentEvidence, IncidentStatus
from app.models.operator import Operator
from app.models.user import User
from app.services.genlayer.client import genlayer_client, compute_merkle_root, poll_until_finalized
from app.services.genlayer.signer import get_user_private_key

router = APIRouter(prefix="/incidents", tags=["Incidents"])


class IncidentCreate(BaseModel):
    operator_address: Optional[str] = None
    incident_type: str = "protocol_violation"
    network: str
    title: str
    description: Optional[str] = None
    block_number: Optional[int] = None
    transaction_hash: Optional[str] = None
    severity: str = "medium"
    evidence_items: list[str] = []
    raw_data: dict = {}


class EvidenceAdd(BaseModel):
    evidence_type: str
    title: str
    content: str
    source_url: Optional[str] = None
    on_chain_proof: dict = {}


@router.get("/")
async def list_incidents(
    network: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    operator_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Incident)
    if network:
        query = query.where(Incident.network == network)
    if status:
        query = query.where(Incident.status == status)
    if severity:
        query = query.where(Incident.severity == severity)
    if operator_id:
        query = query.where(Incident.operator_id == uuid.UUID(operator_id))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    query = query.order_by(Incident.detected_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    incidents = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [
            {
                "id": str(i.id),
                "title": i.title,
                "incident_type": i.incident_type,
                "severity": i.severity,
                "status": i.status,
                "network": i.network,
                "ai_fault_probability": i.ai_fault_probability,
                "ai_severity_score": i.ai_severity_score,
                "ai_confidence_score": i.ai_confidence_score,
                "ai_recommended_action": i.ai_recommended_action,
                "detected_at": i.detected_at,
            }
            for i in incidents
        ],
    }


@router.post("/", status_code=201)
async def create_incident(
    body: IncidentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Look up operator
    op_result = await db.execute(
        select(Operator).where(Operator.address == body.operator_address)
    )
    operator = op_result.scalar_one_or_none()

    incident = Incident(
        operator_id=operator.id if operator else None,
        incident_type=body.incident_type,
        severity=body.severity,
        status=IncidentStatus.OPEN,
        title=body.title,
        description=body.description,
        network=body.network,
        block_number=body.block_number,
        transaction_hash=body.transaction_hash,
        raw_data=body.raw_data,
    )
    db.add(incident)
    await db.flush()

    # Create evidence records and build merkle root
    incident_id_str = str(incident.id)
    evidence_strings = []
    for idx, item_str in enumerate(body.evidence_items):
        ev = IncidentEvidence(
            incident_id=incident.id,
            evidence_type="raw",
            title=f"Evidence {idx + 1}",
            content=item_str,
            merkle_hash=hashlib.sha256(item_str.encode()).hexdigest(),
        )
        db.add(ev)
        evidence_strings.append(item_str)

    # Always include incident_id as a base evidence item so merkle_root is never empty
    evidence_strings_for_merkle = evidence_strings if evidence_strings else [incident_id_str]
    merkle_root = compute_merkle_root(evidence_strings_for_merkle)
    evidence_summary_hash = hashlib.sha256(
        "\n".join(evidence_strings).encode()
    ).hexdigest()

    # Submit evidence to GenLayer asynchronously
    background_tasks.add_task(
        _submit_evidence_and_analyze,
        incident_id_str,
        body.operator_address,
        body.incident_type,
        body.network,
        body.block_number or 0,
        merkle_root,
        max(1, len(evidence_strings)),
        evidence_summary_hash,
        "\n".join(evidence_strings),
        operator.uptime_percentage if operator else 100,
        operator.slash_count if operator else 0,
        int(operator.total_stake) if operator else 0,
        str(current_user.id),
    )

    return {
        "id": str(incident.id),
        "status": "created",
        "merkle_root": merkle_root,
        "analysis": "queued",
    }



async def _submit_evidence_and_analyze(
    incident_id: str,
    operator_address: str,
    violation_type: str,
    network: str,
    block_number: int,
    merkle_root: str,
    evidence_count: int,
    evidence_summary_hash: str,
    evidence_summary: str,
    uptime_pct: float,
    slash_count: int,
    stake_amount: int,
    user_id: str,
):
    from app.db.base import AsyncSessionLocal
    from loguru import logger

    # Fetch signer key then immediately release the DB connection
    async with AsyncSessionLocal() as db:
        signer_key = await get_user_private_key(user_id, db)

    # ── Step 0: ensure operator is registered on-chain before any contract calls ──
    if operator_address:
        try:
            already = await genlayer_client.call_view("operator_exists", [operator_address])
            if not already:
                reg = await genlayer_client.send_transaction(
                    "register_operator",
                    [operator_address, operator_address, network,
                     stake_amount, ""],
                    signer_private_key=signer_key,
                )
                if reg.get("tx_hash"):
                    await poll_until_finalized(reg["tx_hash"], "register_operator")
        except Exception as exc:
            from loguru import logger as _l
            _l.warning(f"Operator on-chain check/register skipped: {exc}")

    # ── Step 1: submit_evidence ───────────────────────────────────────────
    for attempt in range(3):
        ev = await genlayer_client.send_transaction(
            "submit_evidence",
            [incident_id, operator_address, violation_type, network,
             block_number, merkle_root, evidence_count, evidence_summary_hash],
            signer_private_key=signer_key,
        )
        if not ev.get("tx_hash"):
            logger.error(f"submit_evidence send failed ({incident_id}): {ev}")
            return
        confirmed = await poll_until_finalized(ev["tx_hash"], "submit_evidence")
        if confirmed:
            break
        if attempt == 2:
            logger.error(f"submit_evidence never confirmed after 3 attempts — NOT starting analyze_fault")
            return
        logger.warning(f"submit_evidence attempt {attempt+1} undetermined — retrying")

    # ── Step 2: analyze_fault — only reaches here after submit_evidence FINALIZED ──
    logger.info(f"submit_evidence confirmed — now sending analyze_fault for {incident_id}")
    for attempt in range(3):
        verdict = await genlayer_client.send_transaction(
            "analyze_fault",
            [incident_id, operator_address, violation_type, network,
             evidence_summary[:2000],
             f"Slash count: {slash_count}, Uptime: {uptime_pct}%",
             stake_amount, int(uptime_pct), slash_count, 80],
            signer_private_key=signer_key,
        )
        if not verdict.get("tx_hash"):
            logger.error(f"analyze_fault send failed ({incident_id}): {verdict}")
            return
        confirmed = await poll_until_finalized(verdict["tx_hash"], "analyze_fault")
        if confirmed:
            break
        if attempt == 2:
            logger.error(f"analyze_fault never confirmed after 3 attempts")
            return
        logger.warning(f"analyze_fault attempt {attempt+1} undetermined — retrying")

    # ── Sync on-chain verdict back to DB (fresh connection) ───────────────
    try:
        from sqlalchemy import update
        from app.models.incident import Incident
        on_chain = await genlayer_client.call_view("get_ai_verdict", [incident_id])
        update_vals: dict = {
            "status": IncidentStatus.AI_REVIEW,
            "genlayer_tx_hash": verdict.get("tx_hash"),
        }
        if isinstance(on_chain, dict):
            update_vals["ai_fault_probability"] = on_chain.get("fault_probability")
            update_vals["ai_severity_score"] = on_chain.get("severity_score")
            update_vals["ai_confidence_score"] = on_chain.get("confidence_score") or on_chain.get("confidence")
            update_vals["ai_recommended_action"] = on_chain.get("recommended_action")
            update_vals["ai_analysis_summary"] = on_chain.get("analysis_summary") or on_chain.get("reasoning")
        async with AsyncSessionLocal() as db:
            await db.execute(
                update(Incident)
                .where(Incident.id == uuid.UUID(incident_id))
                .values(**update_vals)
            )
            await db.commit()
    except Exception as e:
        logger.error(f"DB sync failed for incident {incident_id}: {e}")


@router.get("/{incident_id}")
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Incident).where(Incident.id == uuid.UUID(incident_id)))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Fetch on-chain verdict
    verdict = await genlayer_client.call_view("get_ai_verdict", [incident_id])

    return {
        "id": str(incident.id),
        "title": incident.title,
        "incident_type": incident.incident_type,
        "severity": incident.severity,
        "status": incident.status,
        "network": incident.network,
        "description": incident.description,
        "block_number": incident.block_number,
        "transaction_hash": incident.transaction_hash,
        "ai_fault_probability": incident.ai_fault_probability,
        "ai_severity_score": incident.ai_severity_score,
        "ai_confidence_score": incident.ai_confidence_score,
        "ai_recommended_action": incident.ai_recommended_action,
        "ai_analysis_summary": incident.ai_analysis_summary,
        "on_chain_verdict": verdict,
        "genlayer_tx_hash": incident.genlayer_tx_hash,
        "detected_at": incident.detected_at,
        "raw_data": incident.raw_data,
    }


@router.post("/{incident_id}/evidence")
async def add_evidence(
    incident_id: str,
    body: EvidenceAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Incident).where(Incident.id == uuid.UUID(incident_id)))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    ev = IncidentEvidence(
        incident_id=incident.id,
        evidence_type=body.evidence_type,
        title=body.title,
        content=body.content,
        source_url=body.source_url,
        on_chain_proof=body.on_chain_proof,
        merkle_hash=hashlib.sha256(body.content.encode()).hexdigest(),
    )
    db.add(ev)
    return {"id": str(ev.id), "status": "added"}
