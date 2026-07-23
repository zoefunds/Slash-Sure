"""
GenLayer on-chain read/write routes.
Exposes contract state to the frontend without going through GenLayer RPC directly.
"""

import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.api.v1.routes.auth import get_current_user
from app.models.user import User
from app.services.genlayer.client import genlayer_client
from app.services.genlayer.signer import get_user_private_key

router = APIRouter(prefix="/genlayer", tags=["GenLayer"])


# ── Global Stats ──────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_contract_stats(current_user: User = Depends(get_current_user)):
    try:
        stats = await asyncio.wait_for(genlayer_client.get_stats(), timeout=15.0)
    except asyncio.TimeoutError:
        stats = None
    return {
        "contract_address": genlayer_client.contract_address,
        "network": "StudioNet",
        "reachable": stats is not None,
        **(stats or {}),
    }


# ── Operators ─────────────────────────────────────────────────────────────────

@router.get("/operators/{address}")
async def get_on_chain_operator(
    address: str,
    current_user: User = Depends(get_current_user),
):
    result = await genlayer_client.get_operator(address)
    if not result:
        raise HTTPException(status_code=404, detail="Operator not found on-chain")
    return result


@router.get("/operators/{address}/exists")
async def operator_exists(address: str, current_user: User = Depends(get_current_user)):
    return {"address": address, "exists": await genlayer_client.operator_exists(address)}


@router.get("/operators/{address}/incidents")
async def get_operator_incidents(address: str, current_user: User = Depends(get_current_user)):
    ids = await genlayer_client.get_operator_incidents(address)
    return {"operator_address": address, "incident_ids": ids}


@router.get("/operators/{address}/cases")
async def get_operator_cases(address: str, current_user: User = Depends(get_current_user)):
    ids = await genlayer_client.get_operator_cases(address)
    return {"operator_address": address, "case_ids": ids}


@router.get("/operators/{address}/risk")
async def get_operator_risk(address: str, current_user: User = Depends(get_current_user)):
    result = await genlayer_client.get_risk_prediction(address)
    if not result:
        raise HTTPException(status_code=404, detail="No risk prediction found")
    return result


@router.get("/operators/{address}/jailed")
async def is_operator_jailed(address: str, current_user: User = Depends(get_current_user)):
    return {"address": address, "jailed": await genlayer_client.is_operator_jailed(address)}


# ── Verdicts ──────────────────────────────────────────────────────────────────

@router.get("/verdicts/{incident_id}")
async def get_verdict(incident_id: str, current_user: User = Depends(get_current_user)):
    result = await genlayer_client.get_verdict(incident_id)
    if not result:
        raise HTTPException(status_code=404, detail="No verdict found")
    return result


@router.get("/evidence/{incident_id}")
async def get_evidence(incident_id: str, current_user: User = Depends(get_current_user)):
    result = await genlayer_client.get_evidence(incident_id)
    if not result:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return result


@router.get("/evidence/{incident_id}/verify/{merkle_root}")
async def verify_evidence(
    incident_id: str,
    merkle_root: str,
    current_user: User = Depends(get_current_user),
):
    valid = await genlayer_client.verify_merkle_root(incident_id, merkle_root)
    return {"incident_id": incident_id, "merkle_root": merkle_root, "valid": valid}


# ── Slashing Cases ────────────────────────────────────────────────────────────

@router.get("/cases/{case_id}")
async def get_case(case_id: str, current_user: User = Depends(get_current_user)):
    result = await genlayer_client.get_slashing_case(case_id)
    if not result:
        raise HTTPException(status_code=404, detail="Case not found on-chain")
    return result


# ── Insurance Claims ──────────────────────────────────────────────────────────

@router.get("/claims/{claim_id}")
async def get_claim(claim_id: str, current_user: User = Depends(get_current_user)):
    result = await genlayer_client.get_claim(claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="Claim not found on-chain")
    return result


@router.get("/payouts/{payout_id}")
async def get_payout(payout_id: str, current_user: User = Depends(get_current_user)):
    result = await genlayer_client.get_payout(payout_id)
    if not result:
        raise HTTPException(status_code=404, detail="Payout not found")
    return result


# ── Governance ────────────────────────────────────────────────────────────────

@router.get("/proposals/{proposal_id}")
async def get_proposal(proposal_id: str, current_user: User = Depends(get_current_user)):
    result = await genlayer_client.get_proposal(proposal_id)
    if not result:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return result


class ProposalCreate(BaseModel):
    target_id: str
    proposal_type: str
    description_hash: str
    voting_period_blocks: int = 7200


@router.post("/proposals")
async def create_proposal(body: ProposalCreate, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    from app.db.base import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        signer_key = await get_user_private_key(str(current_user.id), db)
    background_tasks.add_task(
        genlayer_client.create_proposal,
        target_id=body.target_id,
        proposal_type=body.proposal_type,
        description_hash=body.description_hash,
        voting_period_blocks=body.voting_period_blocks,
        signer_private_key=signer_key,
    )
    return {"status": "queued", "target_id": body.target_id, "proposal_type": body.proposal_type}


class VoteBody(BaseModel):
    vote_for: bool


@router.post("/proposals/{proposal_id}/vote")
async def vote(
    proposal_id: str,
    body: VoteBody,
    current_user: User = Depends(get_current_user),
):
    from app.db.base import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        signer_key = await get_user_private_key(str(current_user.id), db)
    return await genlayer_client.vote(proposal_id, body.vote_for, signer_private_key=signer_key)


@router.post("/proposals/{proposal_id}/finalize")
async def finalize_proposal(proposal_id: str, current_user: User = Depends(get_current_user)):
    from app.db.base import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        signer_key = await get_user_private_key(str(current_user.id), db)
    return await genlayer_client.finalize_proposal(proposal_id, signer_private_key=signer_key)


# ── Audit ─────────────────────────────────────────────────────────────────────

@router.get("/audit/{index}")
async def get_audit_entry(index: int, current_user: User = Depends(get_current_user)):
    result = await genlayer_client.get_audit_entry(index)
    if not result:
        raise HTTPException(status_code=404, detail="Audit entry not found")
    return {"index": index, "hash": result}
