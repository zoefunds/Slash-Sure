import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.v1.routes.auth import get_current_user
from app.core.config import settings
from app.db.base import get_db
from app.models.insurance import InsuranceClaim, InsurancePayout, ClaimStatus
from app.models.user import OrganizationMember, User
from app.services.genlayer.client import genlayer_client, poll_until_finalized
from app.services.genlayer.signer import get_user_private_key

router = APIRouter(prefix="/insurance", tags=["Insurance"])


def _current_contract_address() -> str:
    return settings.GENLAYER_CONTRACT_ADDRESS.strip().lower()


def _claim_contract_address(claim: InsuranceClaim) -> str:
    return str((claim.claim_details or {}).get("contract_address", "")).strip().lower()


async def _get_primary_org_id(db: AsyncSession, user_id: str) -> uuid.UUID:
    result = await db.execute(
        select(OrganizationMember.organization_id)
        .where(OrganizationMember.user_id == uuid.UUID(user_id))
        .order_by(OrganizationMember.joined_at.asc())
    )
    org_id = result.scalars().first()
    if not org_id:
        raise HTTPException(status_code=403, detail="No organization membership found for this user")
    return org_id


class ClaimCreate(BaseModel):
    incident_id: str
    claimant_address: str
    coverage_amount: float
    claimed_amount: float
    policy_id: Optional[str] = None
    claim_details: dict = {}


class PayoutRequest(BaseModel):
    amount: float
    recipient_address: str


class ClaimPoolFundRequest(BaseModel):
    amount: float


@router.get("/claims")
async def list_claims(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = await _get_primary_org_id(db, str(current_user.id))
    query = select(InsuranceClaim)
    query = query.where(InsuranceClaim.organization_id == org_id)
    if status:
        query = query.where(InsuranceClaim.status == status)

    result = await db.execute(query)
    claims = [
        claim
        for claim in result.scalars().all()
        if _claim_contract_address(claim) == _current_contract_address()
    ]
    total = len(claims)
    claims = claims[(page - 1) * per_page : (page - 1) * per_page + per_page]

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [
            {
                "id": str(c.id),
                "claim_number": c.claim_number,
                "status": c.status,
                "coverage_amount": c.coverage_amount,
                "claimed_amount": c.claimed_amount,
                "approved_amount": c.approved_amount,
                "ai_coverage_eligible": c.ai_coverage_eligible,
                "ai_confidence_score": c.ai_confidence_score,
                "submitted_at": c.submitted_at,
            }
            for c in claims
        ],
    }


@router.post("/claims", status_code=201)
async def submit_claim(
    body: ClaimCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = await _get_primary_org_id(db, str(current_user.id))
    import secrets
    claim_number = f"CLM-{secrets.token_hex(4).upper()}"
    claim_id = str(uuid.uuid4())

    claim = InsuranceClaim(
        organization_id=org_id,
        id=uuid.UUID(claim_id),
        claim_number=claim_number,
        incident_id=uuid.UUID(body.incident_id),
        claimant_address=body.claimant_address,
        coverage_amount=body.coverage_amount,
        claimed_amount=body.claimed_amount,
        policy_id=body.policy_id,
        claim_details={
            **(body.claim_details or {}),
            "contract_address": settings.GENLAYER_CONTRACT_ADDRESS,
        },
        status=ClaimStatus.SUBMITTED,
    )
    db.add(claim)
    await db.flush()

    background_tasks.add_task(
        _submit_and_adjudicate_claim,
        claim_id,
        body.incident_id,
        body.claimant_address,
        int(body.coverage_amount),
        int(body.claimed_amount),
        str(current_user.id),
    )

    return {"id": claim_id, "claim_number": claim_number, "status": "submitted"}



async def _submit_and_adjudicate_claim(
    claim_id: str,
    incident_id: str,
    claimant_address: str,
    coverage_amount: int,
    claimed_amount: int,
    user_id: str,
):
    from app.db.base import AsyncSessionLocal
    from sqlalchemy import update
    from app.models.insurance import InsuranceClaim
    from loguru import logger

    # Fetch signer key then immediately release the DB connection
    async with AsyncSessionLocal() as db:
        signer_key = await get_user_private_key(user_id, db)

    # ── Step 1: submit_claim ──────────────────────────────────────────────
    for attempt in range(3):
        sr = await genlayer_client.send_and_wait(
            "submit_claim",
            [claim_id, claimant_address, incident_id, claimant_address,
             coverage_amount, claimed_amount],
            signer_private_key=signer_key,
        )
        if not sr.get("tx_hash"):
            logger.error(f"submit_claim send failed ({claim_id}): {sr}")
            return
        confirmed = await poll_until_finalized(sr["tx_hash"], "submit_claim")
        if confirmed:
            break
        if attempt == 2:
            logger.error("submit_claim never confirmed — NOT starting adjudicate_claim")
            return
        logger.warning(f"submit_claim attempt {attempt+1} undetermined — retrying")

    # ── Step 2: adjudicate_claim — only reaches here after submit_claim FINALIZED ─
    logger.info(f"submit_claim confirmed — now sending adjudicate_claim for {claim_id}")
    for attempt in range(3):
        tx = await genlayer_client.send_and_wait(
            "adjudicate_claim",
            [claim_id,
             f"Incident {incident_id} — coverage claim",
             "Standard SlashSure coverage policy v1.0",
             f"Claimed: {claimed_amount} GEN, Coverage: {coverage_amount} GEN",
             60,
             "No prior fraudulent claims"],
            signer_private_key=signer_key,
        )
        if not tx.get("tx_hash"):
            logger.error(f"adjudicate_claim send failed ({claim_id}): {tx}")
            return
        confirmed = await poll_until_finalized(tx["tx_hash"], "adjudicate_claim")
        if confirmed:
            break
        if attempt == 2:
            logger.error("adjudicate_claim never confirmed after 3 attempts")
            return
        logger.warning(f"adjudicate_claim attempt {attempt+1} undetermined — retrying")

    # ── Sync on-chain verdict back to DB (fresh connection) ───────────────
    try:
        on_chain = await genlayer_client.call_view("get_claim", [claim_id])
        update_vals: dict = {
            "status": ClaimStatus.AI_ADJUDICATION,
            "genlayer_tx_hash": tx.get("tx_hash"),
        }
        if isinstance(on_chain, dict):
            update_vals["approved_amount"] = on_chain.get("approved_amount") or on_chain.get("payout_amount")
            # contract uses ai_eligible and ai_confidence
            update_vals["ai_coverage_eligible"] = on_chain.get("ai_eligible") or on_chain.get("coverage_eligible") or on_chain.get("eligible")
            update_vals["ai_confidence_score"] = on_chain.get("ai_confidence") or on_chain.get("confidence_score") or on_chain.get("confidence")
            if on_chain.get("status"):
                s = str(on_chain.get("status")).lower()
                if s in ("approved", "partial", "rejected", "paid"):
                    update_vals["status"] = s
        async with AsyncSessionLocal() as db:
            await db.execute(
                update(InsuranceClaim)
                .where(InsuranceClaim.id == uuid.UUID(claim_id))
                .values(**update_vals)
            )
            await db.commit()
    except Exception as e:
        logger.error(f"DB sync failed for claim {claim_id}: {e}")


@router.get("/claims/{claim_id}")
async def get_claim(
    claim_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = await _get_primary_org_id(db, str(current_user.id))
    result = await db.execute(select(InsuranceClaim).where(InsuranceClaim.id == uuid.UUID(claim_id)))
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Claim not found")
    if _claim_contract_address(claim) != _current_contract_address():
        raise HTTPException(status_code=404, detail="Claim not found")

    on_chain = await genlayer_client.call_view("get_claim", [claim_id])

    return {
        "id": str(claim.id),
        "claim_number": claim.claim_number,
        "status": claim.status,
        "coverage_amount": claim.coverage_amount,
        "claimed_amount": claim.claimed_amount,
        "assessed_damage": claim.assessed_damage,
        "approved_amount": claim.approved_amount,
        "ai_coverage_eligible": claim.ai_coverage_eligible,
        "ai_confidence_score": claim.ai_confidence_score,
        "ai_adjudication_rationale": claim.ai_adjudication_rationale,
        "ai_adjudication_hash": claim.ai_adjudication_hash,
        "on_chain_data": on_chain,
        "genlayer_tx_hash": claim.genlayer_tx_hash,
        "submitted_at": claim.submitted_at,
        "adjudicated_at": claim.adjudicated_at,
    }


@router.post("/claims/{claim_id}/payout")
async def authorize_payout(
    claim_id: str,
    body: PayoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = await _get_primary_org_id(db, str(current_user.id))
    result = await db.execute(select(InsuranceClaim).where(InsuranceClaim.id == uuid.UUID(claim_id)))
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Claim not found")
    if _claim_contract_address(claim) != _current_contract_address():
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.status not in [ClaimStatus.APPROVED, ClaimStatus.PARTIAL]:
        raise HTTPException(status_code=400, detail="Claim not in approved state")

    payout_id = str(uuid.uuid4())
    payout = InsurancePayout(
        id=uuid.UUID(payout_id),
        claim_id=claim.id,
        amount=body.amount,
        recipient_address=body.recipient_address,
        token="GEN",
        status="pending",
    )
    db.add(payout)

    signer_key = await get_user_private_key(str(current_user.id), db)
    tx = await genlayer_client.authorize_payout(
        claim_id=claim_id,
        payout_id=payout_id,
        amount=int(body.amount),
        recipient=body.recipient_address,
        signer_private_key=signer_key,
    )
    payout.genlayer_approval_hash = tx.get("tx_hash")

    return {
        "payout_id": payout_id,
        "amount": body.amount,
        "recipient": body.recipient_address,
        "approval_tx": tx.get("tx_hash"),
    }


@router.post("/claim-pool/fund")
async def fund_claim_pool(
    body: ClaimPoolFundRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="Funding amount must be positive")
    await _get_primary_org_id(db, str(current_user.id))
    signer_key = await get_user_private_key(str(current_user.id), db)
    tx = await genlayer_client.send_and_wait(
        "fund_claim_pool",
        [],
        signer_private_key=signer_key,
        value=int(body.amount * 10**18),
    )
    if tx.get("tx_hash"):
        await poll_until_finalized(tx["tx_hash"], "fund_claim_pool")
    return {
        "amount": body.amount,
        "tx_hash": tx.get("tx_hash"),
        "status": tx.get("status", "pending"),
    }
