import asyncio
import logging
import uuid
from decimal import Decimal, InvalidOperation
from typing import Optional
import hashlib
import re

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routes.auth import get_current_user
from app.db.base import get_db
from app.models.operator import Operator, OperatorStatus
from app.models.user import OrganizationMember, User
from app.services.genlayer.client import genlayer_client, poll_until_finalized
from app.services.genlayer.signer import get_user_private_key
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/operators", tags=["Operators"])


class OperatorCreate(BaseModel):
    name: str
    address: str
    network: str
    total_stake: float = 0.0
    description: str
    website: str
    commission_rate: float = 0.0


def _gen_to_wei(value: float | int | str) -> int:
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise HTTPException(status_code=400, detail="Invalid GEN amount") from exc
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Stake must be positive")
    return int(amount * Decimal("1000000000000000000"))


def _normalize_website(url: str) -> str:
    website = (url or "").strip()
    if not website:
        raise HTTPException(status_code=400, detail="Website is required")
    if not website.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Website must start with http:// or https://")
    return website


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


async def _verify_website(name: str, address: str, website: str) -> dict:
    normalized = _normalize_website(website)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(normalized, follow_redirects=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to reach operator website: {exc}") from exc
    if resp.status_code >= 400:
        raise HTTPException(status_code=400, detail="Operator website returned an error")

    content = resp.text or ""
    lowered = content.lower()
    name_match = name.lower() in lowered
    address_match = address.lower() in lowered
    meta_match = bool(
        re.search(r'<meta[^>]+name=["\']?description["\']?[^>]+content=["\'][^"\']*' + re.escape(address.lower()) + r'[^"\']*["\']', lowered)
        or re.search(r'<meta[^>]+name=["\']?author["\']?[^>]+content=["\'][^"\']*' + re.escape(name.lower()) + r'[^"\']*["\']', lowered)
    )
    if not (name_match or address_match or meta_match):
        raise HTTPException(
            status_code=400,
            detail="Website verification failed: site must reference the operator name, address, or matching metadata",
        )

    snippet = re.sub(r"\s+", " ", content)[:1000]
    proof_hash = hashlib.sha256(f"{normalized}|{name}|{address}|{snippet}".encode()).hexdigest()
    return {
        "website": normalized,
        "proof_hash": proof_hash,
        "status_code": resp.status_code,
        "matched_name": name_match,
        "matched_address": address_match,
        "matched_meta": meta_match,
        "snippet": snippet[:300],
    }


class OperatorResponse(BaseModel):
    id: str
    name: str
    address: str
    network: str
    status: str
    total_stake: float
    commission_rate: float
    uptime_percentage: float
    slash_count: int
    description: Optional[str]


@router.get("/")
async def list_operators(
    network: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = await _get_primary_org_id(db, str(current_user.id))
    query = select(Operator)
    query = query.where(Operator.organization_id == org_id)
    if network:
        query = query.where(Operator.network == network)
    if status:
        query = query.where(Operator.status == status)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    operators = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [
            {
                "id": str(op.id),
                "name": op.name,
                "address": op.address,
                "network": op.network,
                "status": op.status,
                "total_stake": op.total_stake,
                "commission_rate": op.commission_rate,
                "uptime_percentage": op.uptime_percentage,
                "slash_count": op.slash_count,
                "description": op.description,
            }
            for op in operators
        ],
    }


async def _register_on_chain(
    address: str,
    name: str,
    network: str,
    stake_wei: int,
    user_id: str,
    metadata_hash: str,
) -> dict:
    from app.db.base import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        signer_key = await get_user_private_key(user_id, db)
    try:
        already = await genlayer_client.call_view("operator_exists", [address])
        if already:
            logger.info("Operator %s already registered on-chain, skipping", address)
            return {"status": "already_registered", "tx_hash": None}
        reg = await asyncio.wait_for(
            genlayer_client.register_operator(
                address=address, name=name, network=network,
                stake=stake_wei, metadata_hash=metadata_hash,
                signer_private_key=signer_key,
            ),
            timeout=30.0,
        )
        tx_hash = reg.get("tx_hash")
        if tx_hash:
            finalized = await poll_until_finalized(tx_hash, "register_operator")
            return {"status": "finalized" if finalized else "pending", "tx_hash": tx_hash}
        return {"status": reg.get("status", "pending"), "tx_hash": tx_hash}
    except Exception as exc:
        logger.warning("GenLayer on-chain registration skipped for %s: %s", address, exc)
        return {"status": "failed", "tx_hash": None, "error": str(exc)}


@router.post("/", status_code=201)
async def create_operator(
    body: OperatorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = await _get_primary_org_id(db, str(current_user.id))
    existing = await db.execute(select(Operator).where(Operator.address == body.address))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Operator address already registered")

    website_verification = await _verify_website(body.name, body.address, body.website)
    operator = Operator(
        name=body.name,
        address=body.address,
        network=body.network,
        organization_id=org_id,
        status=OperatorStatus.ACTIVE,
        total_stake=body.total_stake,
        description=body.description,
        website=website_verification["website"],
        commission_rate=body.commission_rate,
    )
    operator.extra_metadata = {
        **(operator.extra_metadata or {}),
        "website_verification": website_verification,
    }
    db.add(operator)
    await db.commit()
    await db.refresh(operator)

    on_chain = await _register_on_chain(
        body.address, body.name, body.network,
        _gen_to_wei(body.total_stake), str(current_user.id), website_verification["proof_hash"]
    )

    return {
        "id": str(operator.id),
        "address": operator.address,
        "status": "registered",
        "total_stake_gen": body.total_stake,
        "total_stake_wei": _gen_to_wei(body.total_stake),
        "website_verification": website_verification,
        "on_chain": on_chain,
    }


@router.get("/{operator_id}")
async def get_operator(
    operator_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = await _get_primary_org_id(db, str(current_user.id))
    result = await db.execute(
        select(Operator).where(
            Operator.id == uuid.UUID(operator_id),
            Operator.organization_id == org_id,
        )
    )
    operator = result.scalar_one_or_none()
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")

    reputation = await genlayer_client.get_operator(operator.address)

    return {
        "id": str(operator.id),
        "name": operator.name,
        "address": operator.address,
        "network": operator.network,
        "status": operator.status,
        "total_stake": operator.total_stake,
        "commission_rate": operator.commission_rate,
        "uptime_percentage": operator.uptime_percentage,
        "slash_count": operator.slash_count,
        "description": operator.description,
        "website": operator.website,
        "on_chain_reputation": reputation,
        "created_at": operator.created_at,
    }
