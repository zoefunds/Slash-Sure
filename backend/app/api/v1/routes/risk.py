import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.v1.routes.auth import get_current_user
from app.db.base import get_db
from app.models.operator import Operator
from app.models.reputation import ReputationScore, ReputationHistory
from app.models.user import User
from app.services.genlayer.client import genlayer_client, poll_until_finalized

router = APIRouter(prefix="/risk", tags=["Risk Intelligence"])


class ReputationComputeRequest(BaseModel):
    operator_address: str
    uptime_30d: int = 99
    uptime_90d: int = 98
    slash_count_total: int = 0
    slash_count_90d: int = 0
    incident_count_90d: int = 0
    missed_blocks_30d: int = 0
    total_blocks_30d: int = 10000
    oracle_accuracy_score: int = 95
    peer_review_score: int = 85
    stake_stability_score: int = 90


class RiskPredictRequest(BaseModel):
    operator_address: str
    recent_performance_trend: str = "stable"
    infrastructure_alerts: str = "none"
    peer_comparison: str = "average"
    market_conditions: str = "normal"
    historical_patterns: str = "no notable patterns"
    days_since_last_incident: int = 365
    stake_growth_rate: int = 0
    delegator_change_rate: int = 0


@router.post("/reputation/compute")
async def compute_reputation(
    body: ReputationComputeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    op_result = await db.execute(
        select(Operator).where(Operator.address == body.operator_address)
    )
    operator = op_result.scalar_one_or_none()
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")

    background_tasks.add_task(
        _compute_and_store_reputation,
        str(operator.id),
        body.operator_address,
        body.uptime_30d, body.uptime_90d, body.slash_count_total, body.slash_count_90d,
        body.incident_count_90d, body.missed_blocks_30d, body.total_blocks_30d,
        body.oracle_accuracy_score, body.peer_review_score, body.stake_stability_score,
        operator.network,
        str(current_user.id),
    )

    return {"status": "queued", "operator": body.operator_address, "message": "Reputation computation started"}


async def _compute_and_store_reputation(
    operator_db_id: str,
    operator_address: str,
    uptime_30d: int, uptime_90d: int, slash_total: int, slash_90d: int,
    incident_90d: int, missed_30d: int, total_30d: int,
    oracle_score: int, peer_score: int, stake_stability: int, network: str,
    user_id: str = "",
):
    from app.db.base import AsyncSessionLocal
    from sqlalchemy import update
    from app.services.genlayer.signer import get_user_private_key

    from loguru import logger

    # Fetch signer key then immediately release the DB connection
    async with AsyncSessionLocal() as db:
        signer_key = await get_user_private_key(user_id, db) if user_id else None

    try:
        from app.models.reputation import ReputationScore
        # Ensure operator is registered on-chain before compute_reputation
        try:
            already = await genlayer_client.call_view("operator_exists", [operator_address])
            if not already:
                reg = await genlayer_client.send_transaction(
                    "register_operator",
                    [operator_address, operator_address, network, 0, ""],
                    signer_private_key=signer_key,
                    value=0,
                )
                if reg.get("tx_hash"):
                    await poll_until_finalized(reg["tx_hash"], "register_operator")
        except Exception as exc:
            logger.warning(f"Operator on-chain check/register skipped for reputation: {exc}")

        # Send compute_reputation and wait for FINALIZED before reading state
        for attempt in range(3):
            cr = await genlayer_client.send_transaction(
                "compute_reputation",
                [operator_address, uptime_30d, uptime_90d, slash_total, slash_90d,
                 incident_90d, missed_30d, total_30d, oracle_score, peer_score,
                 stake_stability, network],
                signer_private_key=signer_key,
            )
            if not cr.get("tx_hash"):
                logger.error(f"compute_reputation send failed: {cr}")
                return
            confirmed = await poll_until_finalized(cr["tx_hash"], "compute_reputation")
            if confirmed:
                break
            if attempt == 2:
                logger.error("compute_reputation never confirmed after 3 attempts")
                return
            logger.warning(f"compute_reputation attempt {attempt+1} undetermined — retrying")

        # Read back on-chain reputation scores
        on_chain = await genlayer_client.get_operator_reputation(operator_address)

        # Write results with a fresh DB connection
        op_uuid = uuid.UUID(operator_db_id)
        async with AsyncSessionLocal() as db:
            await db.execute(
                update(Operator)
                .where(Operator.id == op_uuid)
                .values(uptime_percentage=float(uptime_30d))
            )
            rep_result = await db.execute(
                select(ReputationScore).where(ReputationScore.operator_id == op_uuid)
            )
            rep = rep_result.scalar_one_or_none()
            if rep is None:
                rep = ReputationScore(operator_id=op_uuid)
                db.add(rep)
            if on_chain:
                rep.reliability_score = float(on_chain.get("reliability_score") or rep.reliability_score or 0)
                rep.security_score = float(on_chain.get("security_score") or rep.security_score or 0)
                rep.slashing_risk_score = float(on_chain.get("slashing_risk_score") or rep.slashing_risk_score or 0)
                rep.overall_score = float(on_chain.get("reputation_score") or rep.overall_score or 0)
            await db.commit()
    except Exception as e:
        logger.error(f"Reputation compute failed: {operator_address} — {e}")


@router.post("/predict")
async def predict_risk(
    body: RiskPredictRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    op_result = await db.execute(
        select(Operator).where(Operator.address == body.operator_address)
    )
    if not op_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Operator not found")

    background_tasks.add_task(
        _predict_and_store_risk,
        body.operator_address,
        body.recent_performance_trend,
        body.infrastructure_alerts,
        body.peer_comparison,
        body.market_conditions,
        body.historical_patterns,
        body.days_since_last_incident,
        body.stake_growth_rate,
        body.delegator_change_rate,
        str(current_user.id),
    )

    return {"status": "queued", "operator": body.operator_address, "message": "Risk prediction started"}


async def _predict_and_store_risk(
    operator_address: str,
    perf_trend: str, infra_alerts: str, peer_comparison: str,
    market_conditions: str, historical_patterns: str,
    days_since: int, stake_growth: int, delegator_change: int,
    user_id: str = "",
):
    from app.db.base import AsyncSessionLocal
    from app.services.genlayer.signer import get_user_private_key
    async with AsyncSessionLocal() as db:
        signer_key = await get_user_private_key(user_id, db) if user_id else None
        try:
            await genlayer_client.predict_risk(
                operator_address=operator_address,
                perf_trend=perf_trend, infra_alerts=infra_alerts,
                peer_comparison=peer_comparison, market_conditions=market_conditions,
                historical_patterns=historical_patterns,
                days_since_incident=days_since, stake_growth_rate=stake_growth,
                delegator_change_rate=delegator_change,
                signer_private_key=signer_key,
            )
        except Exception as e:
            from loguru import logger
            logger.error(f"Risk prediction failed: {operator_address} — {e}")


@router.get("/operator/{operator_address}")
async def get_operator_risk_profile(
    operator_address: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.reputation import ReputationScore
    op_result = await db.execute(select(Operator).where(Operator.address == operator_address))
    operator = op_result.scalar_one_or_none()
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")

    # Load DB reputation scores
    rep_result = await db.execute(
        select(ReputationScore).where(ReputationScore.operator_id == operator.id)
    )
    rep = rep_result.scalar_one_or_none()

    # Also try on-chain (may have fresher data)
    on_chain_reputation = await genlayer_client.get_operator_reputation(operator_address)
    on_chain_prediction = await genlayer_client.call_view("get_risk_prediction", [operator_address])

    # Flatten scores: on-chain takes precedence over DB
    reliability_score = (
        (on_chain_reputation or {}).get("reliability_score")
        or (rep.reliability_score if rep else None)
    )
    security_score = (
        (on_chain_reputation or {}).get("security_score")
        or (rep.security_score if rep else None)
    )
    slashing_risk_score = (
        (on_chain_reputation or {}).get("slashing_risk_score")
        or (rep.slashing_risk_score if rep else None)
    )
    reputation_score = (
        (on_chain_reputation or {}).get("reputation_score")
        or (rep.overall_score if rep else None)
    )
    risk_trend = (rep.risk_trend if rep else "stable") if reputation_score else "stable"

    return {
        "operator_address": operator_address,
        "network": operator.network,
        "status": operator.status,
        # Flat fields the frontend reads directly
        "reliability_score": reliability_score,
        "security_score": security_score,
        "slashing_risk_score": slashing_risk_score,
        "overall_score": reputation_score,
        "risk_trend": risk_trend,
        # Raw on-chain data
        "on_chain_reputation": on_chain_reputation,
        "on_chain_prediction": on_chain_prediction,
    }
