"""
GenLayer client — all on-chain calls for SlashSure contract
0x80DD0F48bC6cB64bbc6e2923A76cEb94F69Ce24d (StudioNet)

Uses genlayer-py SDK (>=0.8.1) with the proper write_contract/read_contract
flow through the Consensus Main Contract.
"""

import asyncio
import functools
import hashlib
import json
from typing import Any, Optional

from loguru import logger

from app.core.config import settings

CONTRACT_ADDRESS = "0x80DD0F48bC6cB64bbc6e2923A76cEb94F69Ce24d"

# Lazy-initialise the SDK client once on first use
_sdk_client = None


def _get_sdk_client():
    global _sdk_client
    if _sdk_client is None:
        from genlayer_py.chains.studionet import studionet
        from genlayer_py.client.genlayer_client import GenLayerClient as SDKClient
        _sdk_client = SDKClient(chain_config=studionet)
    return _sdk_client


def _account_from_key(private_key: str):
    from eth_account import Account
    return Account.from_key(private_key)


def _fallback_account():
    """Return a read-only account from the deployer key, or a deterministic dummy."""
    pk = settings.GENLAYER_DEPLOYER_PRIVATE_KEY
    if pk:
        return _account_from_key(pk)
    # deterministic throwaway — address 0x7E5F4…  (only used as sender in gen_call)
    from eth_account import Account
    return Account.from_key("0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef")


async def _run_sync(fn, *args, **kwargs):
    """Run a synchronous SDK call in the default thread-pool executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(fn, *args, **kwargs))


class GenLayerClient:

    def __init__(self):
        self.contract_address = settings.GENLAYER_CONTRACT_ADDRESS or CONTRACT_ADDRESS

    # ── Core helpers ──────────────────────────────────────────────────────────

    async def send_transaction(
        self,
        function_name: str,
        args: list,
        wait_for_receipt: bool = True,
        signer_private_key: Optional[str] = None,
    ) -> dict:
        if not self.contract_address:
            logger.warning("Contract address not set — skipping: %s", function_name)
            return {"tx_hash": None, "status": "skipped", "function": function_name}

        if not signer_private_key:
            pk = settings.GENLAYER_DEPLOYER_PRIVATE_KEY
            if not pk:
                logger.warning("No signer available — skipping: %s", function_name)
                return {"tx_hash": None, "status": "skipped", "reason": "no_signer"}
            signer_private_key = pk

        try:
            sdk = _get_sdk_client()
            account = _account_from_key(signer_private_key)
            tx_hash = await _run_sync(
                sdk.write_contract,
                self.contract_address,
                function_name,
                account,
                None,   # consensus_max_rotations — use chain default
                0,      # value
                False,  # leader_only
                args,   # positional args
                None,   # kwargs
            )
            tx_hash_str = tx_hash.hex() if hasattr(tx_hash, "hex") else str(tx_hash)
            logger.info("GenLayer tx sent: %s → %s", function_name, tx_hash_str)
            return {"tx_hash": tx_hash_str, "status": "pending"}
        except Exception as exc:
            logger.error("GenLayer tx failed: %s — %s", function_name, exc)
            return {"tx_hash": None, "status": "failed", "error": str(exc)}

    async def call_view(self, function_name: str, args: list) -> Any:
        if not self.contract_address:
            return None
        try:
            sdk = _get_sdk_client()
            account = _fallback_account()
            result = await _run_sync(
                sdk.read_contract,
                self.contract_address,
                function_name,
                args,
                None,    # kwargs
                account,
            )
            if isinstance(result, (bytes, bytearray)):
                try:
                    return json.loads(result.decode())
                except Exception:
                    return result.hex()
            if isinstance(result, str):
                try:
                    return json.loads(result)
                except Exception:
                    return result
            return result
        except Exception as exc:
            logger.error("GenLayer view failed: %s — %s", function_name, exc)
            return None

    # ── Operator Management ───────────────────────────────────────────────────

    async def register_operator(
        self, address: str, name: str, network: str, stake: int, metadata_hash: str,
        signer_private_key: Optional[str] = None,
    ) -> dict:
        return await self.send_transaction(
            "register_operator", [address, name, network, stake, metadata_hash],
            signer_private_key=signer_private_key,
        )

    async def update_operator_stake(self, address: str, new_stake: int, signer_private_key: Optional[str] = None) -> dict:
        return await self.send_transaction("update_operator_stake", [address, new_stake], signer_private_key=signer_private_key)

    async def update_operator_status(self, address: str, status: str, signer_private_key: Optional[str] = None) -> dict:
        return await self.send_transaction("update_operator_status", [address, status], signer_private_key=signer_private_key)

    async def whitelist_operator(self, address: str, signer_private_key: Optional[str] = None) -> dict:
        return await self.send_transaction("whitelist_operator", [address], signer_private_key=signer_private_key)

    async def get_operator(self, address: str) -> Optional[dict]:
        return await self.call_view("get_operator", [address])

    async def operator_exists(self, address: str) -> bool:
        result = await self.call_view("operator_exists", [address])
        return bool(result)

    async def get_operator_incidents(self, address: str) -> list[str]:
        raw = await self.call_view("get_operator_incidents", [address])
        if not raw:
            return []
        return [x for x in str(raw).split(",") if x]

    async def get_operator_cases(self, address: str) -> list[str]:
        raw = await self.call_view("get_operator_cases", [address])
        if not raw:
            return []
        return [x for x in str(raw).split(",") if x]

    async def get_operator_claims(self, address: str) -> list[str]:
        raw = await self.call_view("get_operator_claims", [address])
        if not raw:
            return []
        return [x for x in str(raw).split(",") if x]

    # ── Evidence ──────────────────────────────────────────────────────────────

    async def submit_evidence(
        self,
        incident_id: str,
        operator_address: str,
        violation_type: str,
        network: str,
        block_number: int,
        merkle_root: str,
        evidence_count: int,
        evidence_summary_hash: str,
        signer_private_key: Optional[str] = None,
    ) -> dict:
        return await self.send_transaction(
            "submit_evidence",
            [incident_id, operator_address, violation_type, network,
             block_number, merkle_root, evidence_count, evidence_summary_hash],
            signer_private_key=signer_private_key,
        )

    async def get_evidence(self, incident_id: str) -> Optional[dict]:
        return await self.call_view("get_evidence", [incident_id])

    async def verify_merkle_root(self, incident_id: str, expected_root: str) -> bool:
        result = await self.call_view("verify_merkle_root", [incident_id, expected_root])
        return bool(result)

    # ── AI Fault Analysis ─────────────────────────────────────────────────────

    async def analyze_fault(
        self,
        incident_id: str,
        operator_address: str,
        violation_type: str,
        network: str,
        evidence_summary: str,
        operator_history: str,
        stake_amount: int,
        uptime_pct: int,
        prior_slash_count: int,
        reputation: int,
        signer_private_key: Optional[str] = None,
    ) -> dict:
        return await self.send_transaction(
            "analyze_fault",
            [incident_id, operator_address, violation_type, network,
             evidence_summary, operator_history, stake_amount,
             uptime_pct, prior_slash_count, reputation],
            signer_private_key=signer_private_key,
        )

    async def get_verdict(self, incident_id: str) -> Optional[dict]:
        return await self.call_view("get_verdict", [incident_id])

    # ── Slashing Cases ────────────────────────────────────────────────────────

    async def create_slashing_case(
        self,
        case_id: str,
        operator_address: str,
        incident_id: str,
        violation_type: str,
        network: str,
        stake_at_risk: int,
        signer_private_key: Optional[str] = None,
    ) -> dict:
        return await self.send_transaction(
            "create_slashing_case",
            [case_id, operator_address, incident_id, violation_type, network, stake_at_risk],
            signer_private_key=signer_private_key,
        )

    async def generate_slash_recommendation(
        self,
        case_id: str,
        evidence_summary: str,
        operator_history: str,
        network_policy: str,
        current_reputation: int,
        signer_private_key: Optional[str] = None,
    ) -> dict:
        return await self.send_transaction(
            "generate_slash_recommendation",
            [case_id, evidence_summary, operator_history, network_policy, current_reputation],
            signer_private_key=signer_private_key,
        )

    async def approve_slashing(self, case_id: str, signer_private_key: Optional[str] = None) -> dict:
        return await self.send_transaction("approve_slashing", [case_id], signer_private_key=signer_private_key)

    async def reject_slashing(self, case_id: str, reason: str, signer_private_key: Optional[str] = None) -> dict:
        return await self.send_transaction("reject_slashing", [case_id, reason], signer_private_key=signer_private_key)

    async def execute_slashing(self, case_id: str, actual_slash_amount: int, signer_private_key: Optional[str] = None) -> dict:
        return await self.send_transaction("execute_slashing", [case_id, actual_slash_amount], signer_private_key=signer_private_key)

    async def appeal_slashing(self, case_id: str, rationale_hash: str, signer_private_key: Optional[str] = None) -> dict:
        return await self.send_transaction("appeal_slashing", [case_id, rationale_hash], signer_private_key=signer_private_key)

    async def ai_review_appeal(
        self,
        case_id: str,
        original_summary: str,
        appeal_arguments: str,
        new_evidence: str,
        signer_private_key: Optional[str] = None,
    ) -> dict:
        return await self.send_transaction(
            "ai_review_appeal",
            [case_id, original_summary, appeal_arguments, new_evidence],
            signer_private_key=signer_private_key,
        )

    async def get_slashing_case(self, case_id: str) -> Optional[dict]:
        return await self.call_view("get_slashing_case", [case_id])

    # ── Insurance Claims ──────────────────────────────────────────────────────

    async def submit_claim(
        self,
        claim_id: str,
        organization: str,
        incident_id: str,
        claimant_address: str,
        coverage_amount: int,
        claimed_amount: int,
        signer_private_key: Optional[str] = None,
    ) -> dict:
        return await self.send_transaction(
            "submit_claim",
            [claim_id, organization, incident_id, claimant_address, coverage_amount, claimed_amount],
            signer_private_key=signer_private_key,
        )

    async def adjudicate_claim(
        self,
        claim_id: str,
        incident_summary: str,
        policy_terms: str,
        damage_evidence: str,
        negligence_score: int,
        claimant_history: str,
        signer_private_key: Optional[str] = None,
    ) -> dict:
        return await self.send_transaction(
            "adjudicate_claim",
            [claim_id, incident_summary, policy_terms, damage_evidence,
             negligence_score, claimant_history],
            signer_private_key=signer_private_key,
        )

    async def authorize_payout(
        self, claim_id: str, payout_id: str, amount: int, recipient: str,
        signer_private_key: Optional[str] = None,
    ) -> dict:
        return await self.send_transaction(
            "authorize_payout", [claim_id, payout_id, amount, recipient],
            signer_private_key=signer_private_key,
        )

    async def complete_payout(self, payout_id: str, tx_hash: str, signer_private_key: Optional[str] = None) -> dict:
        return await self.send_transaction("complete_payout", [payout_id, tx_hash], signer_private_key=signer_private_key)

    async def get_claim(self, claim_id: str) -> Optional[dict]:
        return await self.call_view("get_claim", [claim_id])

    async def get_payout(self, payout_id: str) -> Optional[dict]:
        return await self.call_view("get_payout", [payout_id])

    # ── Reputation & Risk ─────────────────────────────────────────────────────

    async def compute_reputation(
        self,
        operator_address: str,
        uptime_30d: int,
        uptime_90d: int,
        slash_total: int,
        slash_90d: int,
        incident_90d: int,
        missed_30d: int,
        total_30d: int,
        oracle_score: int,
        peer_score: int,
        stake_stability: int,
        network: str,
        signer_private_key: Optional[str] = None,
    ) -> dict:
        return await self.send_transaction(
            "compute_reputation",
            [operator_address, uptime_30d, uptime_90d, slash_total, slash_90d,
             incident_90d, missed_30d, total_30d, oracle_score, peer_score,
             stake_stability, network],
            signer_private_key=signer_private_key,
        )

    async def predict_risk(
        self,
        operator_address: str,
        perf_trend: str,
        infra_alerts: str,
        peer_comparison: str,
        market_conditions: str,
        historical_patterns: str,
        days_since_incident: int,
        stake_growth_rate: int,
        delegator_change_rate: int,
        signer_private_key: Optional[str] = None,
    ) -> dict:
        return await self.send_transaction(
            "predict_risk",
            [operator_address, perf_trend, infra_alerts, peer_comparison,
             market_conditions, historical_patterns, days_since_incident,
             stake_growth_rate, delegator_change_rate],
            signer_private_key=signer_private_key,
        )

    async def get_risk_prediction(self, operator_address: str) -> Optional[dict]:
        return await self.call_view("get_risk_prediction", [operator_address])

    # ── Governance ────────────────────────────────────────────────────────────

    async def create_proposal(
        self,
        target_id: str,
        proposal_type: str,
        description_hash: str,
        voting_period_blocks: int,
        signer_private_key: Optional[str] = None,
    ) -> dict:
        return await self.send_transaction(
            "create_proposal",
            [target_id, proposal_type, description_hash, voting_period_blocks],
            signer_private_key=signer_private_key,
        )

    async def vote(self, proposal_id: str, vote_for: bool, signer_private_key: Optional[str] = None) -> dict:
        return await self.send_transaction("vote", [proposal_id, vote_for], signer_private_key=signer_private_key)

    async def finalize_proposal(self, proposal_id: str, signer_private_key: Optional[str] = None) -> dict:
        return await self.send_transaction("finalize_proposal", [proposal_id], signer_private_key=signer_private_key)

    async def get_proposal(self, proposal_id: str) -> Optional[dict]:
        return await self.call_view("get_proposal", [proposal_id])

    # ── Global Stats ──────────────────────────────────────────────────────────

    async def get_stats(self) -> Optional[dict]:
        return await self.call_view("get_stats", [])

    async def is_operator_jailed(self, address: str) -> bool:
        result = await self.call_view("is_operator_jailed", [address])
        return bool(result)

    async def get_audit_entry(self, index: int) -> Optional[str]:
        return await self.call_view("get_audit_entry", [index])

    # ── Admin ─────────────────────────────────────────────────────────────────

    async def pause(self) -> dict:
        return await self.send_transaction("pause", [])

    async def unpause(self) -> dict:
        return await self.send_transaction("unpause", [])

    async def transfer_ownership(self, new_owner: str) -> dict:
        return await self.send_transaction("transfer_ownership", [new_owner])

    async def update_params(
        self,
        min_confidence_slash: int,
        min_confidence_claim: int,
        appeal_window_blocks: int,
        max_slash_bps: int,
    ) -> dict:
        return await self.send_transaction(
            "update_params",
            [min_confidence_slash, min_confidence_claim, appeal_window_blocks, max_slash_bps],
        )


# ── Merkle helper ─────────────────────────────────────────────────────────────

def compute_merkle_root(evidence_items: list[str]) -> str:
    """SHA-256 Merkle root for evidence anchoring."""
    if not evidence_items:
        return hashlib.sha256(b"empty").hexdigest()
    leaves = [hashlib.sha256(item.encode()).digest() for item in evidence_items]
    while len(leaves) > 1:
        if len(leaves) % 2 != 0:
            leaves.append(leaves[-1])
        leaves = [
            hashlib.sha256(leaves[i] + leaves[i + 1]).digest()
            for i in range(0, len(leaves), 2)
        ]
    return leaves[0].hex()


# Singleton
genlayer_client = GenLayerClient()
