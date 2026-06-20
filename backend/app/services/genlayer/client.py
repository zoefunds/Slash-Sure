"""
GenLayer client — all on-chain calls for SlashSure contract
0x80DD0F48bC6cB64bbc6e2923A76cEb94F69Ce24d (StudioNet)
"""

import asyncio
import hashlib
import json
from typing import Any, Optional

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

CONTRACT_ADDRESS = "0x80DD0F48bC6cB64bbc6e2923A76cEb94F69Ce24d"


class GenLayerClient:

    def __init__(self):
        self.rpc_url          = settings.GENLAYER_RPC_URL
        self.contract_address = settings.GENLAYER_CONTRACT_ADDRESS or CONTRACT_ADDRESS
        self.private_key      = settings.GENLAYER_DEPLOYER_PRIVATE_KEY
        self._http            = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self._http.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def _call_rpc(self, method: str, params: list) -> Any:
        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        resp = await self._http.post(self.rpc_url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise Exception(f"GenLayer RPC error: {data['error']}")
        return data.get("result", {})

    async def send_transaction(
        self,
        function_name: str,
        args: list,
        wait_for_receipt: bool = True,
    ) -> dict:
        """Send a write transaction to the SlashSure contract."""
        if not self.contract_address:
            logger.warning("Contract address not set — skipping on-chain call: %s", function_name)
            return {"tx_hash": None, "status": "skipped", "function": function_name}

        try:
            result = await self._call_rpc(
                "gen_sendTransaction",
                [{
                    "from": self._deployer_address(),
                    "to": self.contract_address,
                    "function": function_name,
                    "args": args,
                    "value": 0,
                }],
            )
            tx_hash = result.get("transactionHash") or result.get("tx_hash")
            logger.info("GenLayer tx sent: %s → %s", function_name, tx_hash)

            if wait_for_receipt and tx_hash:
                receipt = await self._wait_for_receipt(tx_hash)
                return {"tx_hash": tx_hash, "receipt": receipt, "status": "confirmed"}
            return {"tx_hash": tx_hash, "status": "pending"}

        except Exception as exc:
            logger.error("GenLayer tx failed: %s — %s", function_name, exc)
            return {"tx_hash": None, "status": "failed", "error": str(exc)}

    async def call_view(self, function_name: str, args: list) -> Any:
        """Call a view (read-only) function."""
        if not self.contract_address:
            return None
        try:
            result = await self._call_rpc(
                "gen_call",
                [{"to": self.contract_address, "function": function_name, "args": args}],
            )
            # View functions return JSON strings — parse them transparently
            if isinstance(result, str):
                try:
                    return json.loads(result)
                except Exception:
                    return result
            return result
        except Exception as exc:
            logger.error("GenLayer view failed: %s — %s", function_name, exc)
            return None

    async def _wait_for_receipt(self, tx_hash: str, max_wait: int = 300) -> dict:
        waited = 0
        while waited < max_wait:
            try:
                receipt = await self._call_rpc("gen_getTransactionReceipt", [tx_hash])
                if receipt and receipt.get("status"):
                    return receipt
            except Exception:
                pass
            await asyncio.sleep(5)
            waited += 5
        logger.warning("Receipt timeout for tx: %s", tx_hash)
        return {"status": "timeout", "tx_hash": tx_hash}

    def _deployer_address(self) -> str:
        if not self.private_key:
            return "0x0000000000000000000000000000000000000000"
        from eth_account import Account
        return Account.from_key(self.private_key).address

    # ── Operator Management ───────────────────────────────────────────────────

    async def register_operator(
        self, address: str, name: str, network: str, stake: int, metadata_hash: str
    ) -> dict:
        return await self.send_transaction(
            "register_operator", [address, name, network, stake, metadata_hash]
        )

    async def update_operator_stake(self, address: str, new_stake: int) -> dict:
        return await self.send_transaction("update_operator_stake", [address, new_stake])

    async def update_operator_status(self, address: str, status: str) -> dict:
        return await self.send_transaction("update_operator_status", [address, status])

    async def whitelist_operator(self, address: str) -> dict:
        return await self.send_transaction("whitelist_operator", [address])

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
    ) -> dict:
        return await self.send_transaction(
            "submit_evidence",
            [incident_id, operator_address, violation_type, network,
             block_number, merkle_root, evidence_count, evidence_summary_hash],
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
    ) -> dict:
        return await self.send_transaction(
            "analyze_fault",
            [incident_id, operator_address, violation_type, network,
             evidence_summary, operator_history, stake_amount,
             uptime_pct, prior_slash_count, reputation],
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
    ) -> dict:
        return await self.send_transaction(
            "create_slashing_case",
            [case_id, operator_address, incident_id, violation_type, network, stake_at_risk],
        )

    async def generate_slash_recommendation(
        self,
        case_id: str,
        evidence_summary: str,
        operator_history: str,
        network_policy: str,
        current_reputation: int,
    ) -> dict:
        return await self.send_transaction(
            "generate_slash_recommendation",
            [case_id, evidence_summary, operator_history, network_policy, current_reputation],
        )

    async def approve_slashing(self, case_id: str) -> dict:
        return await self.send_transaction("approve_slashing", [case_id])

    async def reject_slashing(self, case_id: str, reason: str) -> dict:
        return await self.send_transaction("reject_slashing", [case_id, reason])

    async def execute_slashing(self, case_id: str, actual_slash_amount: int) -> dict:
        return await self.send_transaction("execute_slashing", [case_id, actual_slash_amount])

    async def appeal_slashing(self, case_id: str, rationale_hash: str) -> dict:
        return await self.send_transaction("appeal_slashing", [case_id, rationale_hash])

    async def ai_review_appeal(
        self,
        case_id: str,
        original_summary: str,
        appeal_arguments: str,
        new_evidence: str,
    ) -> dict:
        return await self.send_transaction(
            "ai_review_appeal",
            [case_id, original_summary, appeal_arguments, new_evidence],
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
    ) -> dict:
        return await self.send_transaction(
            "submit_claim",
            [claim_id, organization, incident_id, claimant_address, coverage_amount, claimed_amount],
        )

    async def adjudicate_claim(
        self,
        claim_id: str,
        incident_summary: str,
        policy_terms: str,
        damage_evidence: str,
        negligence_score: int,
        claimant_history: str,
    ) -> dict:
        return await self.send_transaction(
            "adjudicate_claim",
            [claim_id, incident_summary, policy_terms, damage_evidence,
             negligence_score, claimant_history],
        )

    async def authorize_payout(
        self, claim_id: str, payout_id: str, amount: int, recipient: str
    ) -> dict:
        return await self.send_transaction(
            "authorize_payout", [claim_id, payout_id, amount, recipient]
        )

    async def complete_payout(self, payout_id: str, tx_hash: str) -> dict:
        return await self.send_transaction("complete_payout", [payout_id, tx_hash])

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
    ) -> dict:
        return await self.send_transaction(
            "compute_reputation",
            [operator_address, uptime_30d, uptime_90d, slash_total, slash_90d,
             incident_90d, missed_30d, total_30d, oracle_score, peer_score,
             stake_stability, network],
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
    ) -> dict:
        return await self.send_transaction(
            "predict_risk",
            [operator_address, perf_trend, infra_alerts, peer_comparison,
             market_conditions, historical_patterns, days_since_incident,
             stake_growth_rate, delegator_change_rate],
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
    ) -> dict:
        return await self.send_transaction(
            "create_proposal",
            [target_id, proposal_type, description_hash, voting_period_blocks],
        )

    async def vote(self, proposal_id: str, vote_for: bool) -> dict:
        return await self.send_transaction("vote", [proposal_id, vote_for])

    async def finalize_proposal(self, proposal_id: str) -> dict:
        return await self.send_transaction("finalize_proposal", [proposal_id])

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
