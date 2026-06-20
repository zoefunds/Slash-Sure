import asyncio
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routes.auth import get_current_user
from app.db.base import get_db
from app.models.operator import Operator, OperatorStatus
from app.models.user import User
from app.services.genlayer.client import genlayer_client
from app.services.genlayer.signer import get_user_private_key
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/operators", tags=["Operators"])


class OperatorCreate(BaseModel):
    name: str
    address: str
    network: str
    total_stake: float = 0.0
    description: Optional[str] = None
    website: Optional[str] = None
    commission_rate: float = 0.0


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
    query = select(Operator)
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


async def _register_on_chain(address: str, name: str, network: str, stake: int, user_id: str) -> None:
    from app.db.base import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        signer_key = await get_user_private_key(user_id, db)
    try:
        await asyncio.wait_for(
            genlayer_client.register_operator(
                address=address, name=name, network=network,
                stake=stake, metadata_hash="",
                signer_private_key=signer_key,
            ),
            timeout=30.0,
        )
    except Exception as exc:
        logger.warning("GenLayer on-chain registration skipped for %s: %s", address, exc)


@router.post("/", status_code=201)
async def create_operator(
    body: OperatorCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await db.execute(select(Operator).where(Operator.address == body.address))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Operator address already registered")

    operator = Operator(
        name=body.name,
        address=body.address,
        network=body.network,
        status=OperatorStatus.ACTIVE,
        total_stake=body.total_stake,
        description=body.description,
        website=body.website,
        commission_rate=body.commission_rate,
    )
    db.add(operator)
    await db.commit()
    await db.refresh(operator)

    # Fire-and-forget on-chain registration — don't block the response
    background_tasks.add_task(
        _register_on_chain, body.address, body.name, body.network,
        int(body.total_stake), str(current_user.id)
    )

    return {"id": str(operator.id), "address": operator.address, "status": "registered"}


@router.get("/{operator_id}")
async def get_operator(
    operator_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Operator).where(Operator.id == uuid.UUID(operator_id)))
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
