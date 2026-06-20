"""
Background monitoring worker.
Polls on-chain sources for slashing events, creates incidents,
and publishes real-time alerts to Redis.
Runs as a long-lived asyncio task started in the FastAPI lifespan.
"""

import asyncio
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from loguru import logger
from sqlalchemy import select

from app.core.config import settings
from app.db.base import AsyncSessionLocal
from app.models.incident import Incident, IncidentStatus
from app.models.monitoring import Alert, MonitoringEvent
from app.models.operator import Operator
from app.services.genlayer.client import compute_merkle_root, genlayer_client


# ── Poll intervals (seconds) ──────────────────────────────────────────────────

POLL_EIGENLAYER = 60
POLL_SYMBIOTIC  = 90
POLL_BABYLON    = 120
POLL_COSMOS     = 120


# ── HTTP client ───────────────────────────────────────────────────────────────

_http = httpx.AsyncClient(timeout=30.0, follow_redirects=True)


# ── Alert publishing ──────────────────────────────────────────────────────────

async def _publish(event_type: str, data: dict) -> None:
    try:
        from app.api.v1.ws.events import publish_event
        await publish_event(event_type, data)
    except Exception as exc:
        logger.error("Publish failed: %s", exc)


# ── Database helpers ──────────────────────────────────────────────────────────

async def _save_event(
    db,
    event_type: str,
    network: str,
    severity: str,
    summary: str,
    raw_data: dict,
    block_number: Optional[int] = None,
    operator_address: Optional[str] = None,
) -> MonitoringEvent:
    ev = MonitoringEvent(
        event_type=event_type,
        network=network,
        severity=severity,
        summary=summary,
        block_number=block_number,
        raw_payload={**(raw_data or {}), "operator_address": operator_address},
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(ev)
    await db.flush()
    return ev


async def _save_alert(db, title: str, message: str, severity: str, network: str) -> Alert:
    alert = Alert(
        title=title,
        message=message,
        severity=severity,
        network=network,
        is_acknowledged=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(alert)
    await db.flush()
    return alert


async def _create_incident(
    db,
    operator_address: str,
    incident_type: str,
    network: str,
    title: str,
    description: str,
    severity: str,
    block_number: Optional[int],
    evidence_items: list[str],
) -> Optional[Incident]:
    # Deduplicate: skip if identical incident already exists in last hour
    recent = await db.execute(
        select(Incident).where(
            Incident.incident_type == incident_type,
            Incident.network == network,
            Incident.status != IncidentStatus.RESOLVED,
        ).limit(1)
    )
    if recent.scalar_one_or_none():
        return None

    op_result = await db.execute(select(Operator).where(Operator.address == operator_address))
    operator = op_result.scalar_one_or_none()

    merkle_root = compute_merkle_root(evidence_items)
    incident_id = uuid.uuid4()

    incident = Incident(
        id=incident_id,
        operator_id=operator.id if operator else None,
        incident_type=incident_type,
        severity=severity,
        status=IncidentStatus.OPEN,
        title=title,
        description=description,
        network=network,
        block_number=block_number,
        raw_data={"evidence": evidence_items, "merkle_root": merkle_root},
    )
    db.add(incident)
    await db.flush()
    return incident


# ── EigenLayer Adapter ────────────────────────────────────────────────────────

async def poll_eigenlayer() -> None:
    logger.info("Polling EigenLayer...")
    try:
        # EigenLayer public GraphQL subgraph
        url = "https://api.thegraph.com/subgraphs/name/eigenlabs/eigenlayer-mainnet"
        query = """
        {
          operatorSlashings(first: 10, orderBy: blockNumber, orderDirection: desc) {
            id
            operator { id }
            slashedAmount
            blockNumber
            blockTimestamp
          }
          registeredOperators(first: 5, orderBy: registeredAt, orderDirection: desc) {
            id
            metadataURI
          }
        }
        """
        resp = await _http.post(url, json={"query": query}, timeout=20.0)
        if resp.status_code != 200:
            return

        data = resp.json().get("data", {})
        slashings = data.get("operatorSlashings", [])

        async with AsyncSessionLocal() as db:
            for s in slashings:
                op_addr  = s.get("operator", {}).get("id", "unknown")
                amount   = int(s.get("slashedAmount", 0))
                block    = int(s.get("blockNumber", 0))
                event_id = s.get("id", "")

                evidence = [
                    f"operator:{op_addr}",
                    f"slashed_amount:{amount}",
                    f"block:{block}",
                    f"event_id:{event_id}",
                ]

                incident = await _create_incident(
                    db,
                    operator_address=op_addr,
                    incident_type="slashing_detected",
                    network="eigenlayer",
                    title=f"EigenLayer Slash Detected — {op_addr[:12]}…",
                    description=f"Operator {op_addr} slashed {amount} on EigenLayer at block {block}",
                    severity="critical" if amount > 1_000_000 else "high",
                    block_number=block,
                    evidence_items=evidence,
                )
                if incident:
                    await _save_alert(
                        db,
                        title=f"EigenLayer Slash: {op_addr[:10]}…",
                        message=f"Operator slashed {amount} ETH-equivalent at block {block}",
                        severity="critical",
                        network="eigenlayer",
                    )
                    await _save_event(
                        db,
                        event_type="eigenlayer_slash",
                        network="eigenlayer",
                        severity="critical",
                        summary=f"Slash detected: {op_addr[:12]} — {amount}",
                        raw_data=s,
                        block_number=block,
                        operator_address=op_addr,
                    )
                    await db.commit()
                    await _publish("slash_alert", {
                        "network": "eigenlayer",
                        "operator": op_addr,
                        "amount": amount,
                        "block": block,
                        "incident_id": str(incident.id),
                    })

    except Exception as exc:
        logger.warning("EigenLayer poll error: %s", exc)


# ── Symbiotic Adapter ─────────────────────────────────────────────────────────

async def poll_symbiotic() -> None:
    logger.info("Polling Symbiotic...")
    try:
        # Symbiotic public API / subgraph — adapt URL as it becomes available
        url = "https://api.symbiotic.fi/v1/slashing-events?limit=10"
        resp = await _http.get(url, timeout=15.0)
        if resp.status_code != 200:
            return
        events = resp.json().get("events", [])

        async with AsyncSessionLocal() as db:
            for ev in events:
                op_addr  = ev.get("operatorAddress", "unknown")
                amount   = float(ev.get("slashedAmount", 0))
                block    = ev.get("blockNumber")
                vault    = ev.get("vault", "unknown")

                evidence = [
                    f"operator:{op_addr}",
                    f"vault:{vault}",
                    f"slashed:{amount}",
                ]

                incident = await _create_incident(
                    db,
                    operator_address=op_addr,
                    incident_type="slashing_detected",
                    network="symbiotic",
                    title=f"Symbiotic Slash — vault {vault[:10]}",
                    description=f"Operator {op_addr} slashed {amount} from vault {vault}",
                    severity="high",
                    block_number=block,
                    evidence_items=evidence,
                )
                if incident:
                    await _save_alert(db, f"Symbiotic Slash: {op_addr[:10]}",
                                      f"Amount: {amount}", "high", "symbiotic")
                    await db.commit()
                    await _publish("slash_alert", {
                        "network": "symbiotic",
                        "operator": op_addr,
                        "amount": amount,
                        "incident_id": str(incident.id),
                    })

    except Exception as exc:
        logger.debug("Symbiotic poll: %s (API may not be live yet)", exc)


# ── Babylon Adapter ───────────────────────────────────────────────────────────

async def poll_babylon() -> None:
    logger.info("Polling Babylon...")
    try:
        rpc = settings.BABYLON_RPC_URL
        resp = await _http.get(f"{rpc}/babylon/btcstaking/v1/finality_providers", timeout=15.0)
        if resp.status_code != 200:
            return

        fps = resp.json().get("finality_providers", [])

        async with AsyncSessionLocal() as db:
            for fp in fps:
                jailed = fp.get("jailed", False)
                if not jailed:
                    continue

                btc_pk    = fp.get("btc_pk", "unknown")
                commission = fp.get("commission", "0")
                slashed   = fp.get("slashed_babylon_addr") or fp.get("slashed_sat", 0)

                evidence = [f"btc_pk:{btc_pk}", f"jailed:true", f"commission:{commission}"]
                incident = await _create_incident(
                    db,
                    operator_address=btc_pk,
                    incident_type="jailed_validator",
                    network="babylon",
                    title=f"Babylon Finality Provider Jailed — {btc_pk[:12]}",
                    description=f"Finality provider {btc_pk} is jailed on Babylon.",
                    severity="high",
                    block_number=None,
                    evidence_items=evidence,
                )
                if incident:
                    await _save_alert(db, f"Babylon FP Jailed: {btc_pk[:10]}",
                                      "Finality provider jailed", "high", "babylon")
                    await db.commit()
                    await _publish("validator_jailed", {
                        "network": "babylon",
                        "operator": btc_pk,
                        "incident_id": str(incident.id),
                    })

    except Exception as exc:
        logger.debug("Babylon poll error: %s", exc)


# ── Cosmos / IBC Adapter ──────────────────────────────────────────────────────

async def poll_cosmos() -> None:
    logger.info("Polling Cosmos...")
    try:
        rpc = settings.COSMOS_RPC_URL
        # Fetch validators in jail state
        resp = await _http.get(f"{rpc}/cosmos/staking/v1beta1/validators?status=BOND_STATUS_UNBONDED",
                               timeout=15.0)
        if resp.status_code != 200:
            return

        validators = resp.json().get("validators", [])

        async with AsyncSessionLocal() as db:
            for val in validators:
                jailed = val.get("jailed", False)
                if not jailed:
                    continue

                op_addr  = val.get("operator_address", "unknown")
                moniker  = val.get("description", {}).get("moniker", "unknown")
                tokens   = int(val.get("tokens", 0))

                evidence = [f"operator:{op_addr}", f"moniker:{moniker}", f"jailed:true"]
                incident = await _create_incident(
                    db,
                    operator_address=op_addr,
                    incident_type="jailed_validator",
                    network="cosmos",
                    title=f"Cosmos Validator Jailed — {moniker}",
                    description=f"Validator {moniker} ({op_addr}) jailed with {tokens} tokens.",
                    severity="medium",
                    block_number=None,
                    evidence_items=evidence,
                )
                if incident:
                    await _save_alert(db, f"Cosmos Jailed: {moniker}",
                                      f"Operator: {op_addr}", "medium", "cosmos")
                    await db.commit()
                    await _publish("validator_jailed", {
                        "network": "cosmos",
                        "operator": op_addr,
                        "moniker": moniker,
                        "incident_id": str(incident.id),
                    })

    except Exception as exc:
        logger.debug("Cosmos poll error: %s", exc)


# ── Main worker loop ──────────────────────────────────────────────────────────

async def run_monitoring_worker() -> None:
    logger.info("Monitoring worker started")
    last_eigen   = 0.0
    last_symb    = 0.0
    last_babylon = 0.0
    last_cosmos  = 0.0

    while True:
        now = asyncio.get_event_loop().time()
        tasks = []

        if now - last_eigen >= POLL_EIGENLAYER:
            last_eigen = now
            tasks.append(poll_eigenlayer())

        if now - last_symb >= POLL_SYMBIOTIC:
            last_symb = now
            tasks.append(poll_symbiotic())

        if now - last_babylon >= POLL_BABYLON:
            last_babylon = now
            tasks.append(poll_babylon())

        if now - last_cosmos >= POLL_COSMOS:
            last_cosmos = now
            tasks.append(poll_cosmos())

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    logger.error("Worker task error: %s", r)

        await asyncio.sleep(15)
