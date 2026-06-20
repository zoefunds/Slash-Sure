"""
GenLayer client wrapper — all on-chain calls route through here.
Handles transaction signing, retries, and result parsing.
"""

import asyncio
import hashlib
import json
from typing import Any, Optional

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings


class GenLayerClient:

    def __init__(self):
        self.rpc_url = settings.GENLAYER_RPC_URL
        self.contract_address = settings.GENLAYER_CONTRACT_ADDRESS
        self.private_key = settings.GENLAYER_DEPLOYER_PRIVATE_KEY
        self._http = httpx.AsyncClient(timeout=120.0)

    async def close(self):
        await self._http.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def _call_rpc(self, method: str, params: list) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1,
        }
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
            logger.warning("GenLayer contract address not configured, skipping on-chain call")
            return {"tx_hash": None, "status": "skipped", "function": function_name}

        try:
            result = await self._call_rpc(
                "gen_sendTransaction",
                [{
                    "from": self._get_deployer_address(),
                    "to": self.contract_address,
                    "function": function_name,
                    "args": args,
                    "value": 0,
                }],
            )
            tx_hash = result.get("transactionHash") or result.get("tx_hash")
            logger.info(f"GenLayer tx sent: {function_name} → {tx_hash}")

            if wait_for_receipt and tx_hash:
                receipt = await self._wait_for_receipt(tx_hash)
                return {"tx_hash": tx_hash, "receipt": receipt, "status": "confirmed"}

            return {"tx_hash": tx_hash, "status": "pending"}
        except Exception as e:
            logger.error(f"GenLayer transaction failed: {function_name} — {e}")
            return {"tx_hash": None, "status": "failed", "error": str(e)}

    async def call_view(self, function_name: str, args: list) -> Any:
        """Call a view function (read-only) on the contract."""
        if not self.contract_address:
            return None
        try:
            result = await self._call_rpc(
                "gen_call",
                [{
                    "to": self.contract_address,
                    "function": function_name,
                    "args": args,
                }],
            )
            return result
        except Exception as e:
            logger.error(f"GenLayer view call failed: {function_name} — {e}")
            return None

    async def _wait_for_receipt(self, tx_hash: str, max_wait: int = 300) -> dict:
        """Poll for transaction receipt with timeout."""
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
        logger.warning(f"Receipt timeout for tx: {tx_hash}")
        return {"status": "timeout", "tx_hash": tx_hash}

    def _get_deployer_address(self) -> str:
        if not self.private_key:
            return "0x0000000000000000000000000000000000000000"
        from eth_account import Account
        account = Account.from_key(self.private_key)
        return account.address

    # ─── Contract-specific wrappers ───────────────────────────────────────────

    async def register_operator(
        self, address: str, name: str, network: str, stake: int, metadata_hash: str
    ) -> dict:
        return await self.send_transaction(
            "register_operator", [address, name, network, stake, metadata_hash]
        )

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
            "submit_evidence_package",
            [incident_id, operator_address, violation_type, network,
             block_number, merkle_root, evidence_count, evidence_summary_hash],
        )

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

    async def generate_slashing_recommendation(
        self,
        case_id: str,
        operator_address: str,
        evidence_summary: str,
        operator_history: str,
        network_policy: str,
        stake_at_risk: int,
        reputation: int,
    ) -> dict:
        return await self.send_transaction(
            "generate_slashing_recommendation",
            [case_id, operator_address, evidence_summary, operator_history,
             network_policy, stake_at_risk, reputation],
        )

    async def submit_insurance_claim(
        self,
        claim_id: str,
        organization: str,
        incident_id: str,
        claimant_address: str,
        coverage_amount: int,
        claimed_amount: int,
    ) -> dict:
        return await self.send_transaction(
            "submit_insurance_claim",
            [claim_id, organization, incident_id, claimant_address, coverage_amount, claimed_amount],
        )

    async def adjudicate_claim(
        self,
        claim_id: str,
        incident_summary: str,
        policy_terms: str,
        damage_evidence: str,
        negligence_score: int,
        network_conditions: str,
        claimant_history: str,
        coverage_amount: int,
        claimed_amount: int,
    ) -> dict:
        return await self.send_transaction(
            "adjudicate_insurance_claim",
            [claim_id, incident_summary, policy_terms, damage_evidence,
             negligence_score, network_conditions, claimant_history,
             coverage_amount, claimed_amount],
        )

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
            "compute_reputation_score",
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
            "predict_operator_risk",
            [operator_address, perf_trend, infra_alerts, peer_comparison,
             market_conditions, historical_patterns, days_since_incident,
             stake_growth_rate, delegator_change_rate],
        )

    async def authorize_payout(
        self, claim_id: str, payout_id: str, amount: int, recipient: str
    ) -> dict:
        return await self.send_transaction(
            "authorize_payout", [claim_id, payout_id, amount, recipient]
        )

    async def get_operator(self, address: str) -> Optional[dict]:
        return await self.call_view("get_operator", [address])

    async def get_contract_stats(self) -> Optional[dict]:
        return await self.call_view("get_contract_stats", [])

    async def get_operator_reputation(self, address: str) -> Optional[dict]:
        return await self.call_view("get_operator_reputation_summary", [address])

    async def verify_evidence(self, incident_id: str, merkle_root: str) -> bool:
        result = await self.call_view("verify_evidence_integrity", [incident_id, merkle_root])
        return bool(result)


# ─── Merkle helper ────────────────────────────────────────────────────────────

def compute_merkle_root(evidence_items: list[str]) -> str:
    """Simple SHA-256 Merkle root computation for evidence anchoring."""
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


genlayer_client = GenLayerClient()
