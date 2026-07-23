# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *

import json
import hashlib
import re
from html import unescape


@gl.evm.contract_interface
class _Recipient:
    class View:
        pass

    class Write:
        pass


def _send_gen(to_address: str, amount: u256) -> None:
    if not to_address:
        raise gl.vm.UserError("Missing recipient address")
    if amount <= u256(0):
        raise gl.vm.UserError("Transfer amount must be positive")
    _Recipient(Address(to_address)).emit_transfer(value=amount)


# ─── SlashSure Intelligent Contract ───────────────────────────────────────────
#
# AI-powered slashing monitoring, risk assessment, and insurance coordination
# for decentralised networks: EigenLayer, Symbiotic, Babylon, Cosmos/IBC.
#
# All non-deterministic (LLM) decisions use GenLayer's Equivalence Principle
# with prompt_comparative + numeric-tolerance principles to avoid UNDETERMINED.
#
# Storage strategy: every complex record is JSON-serialised into
# TreeMap[str, str] to keep the schema loader happy (no custom dataclasses
# as generic type parameters).
# ──────────────────────────────────────────────────────────────────────────────


class SlashSureContract(gl.Contract):

    # ── Operator registry ─────────────────────────────────────────────────────
    # Each entry is a JSON-serialised dict:
    # { address, name, network, status, total_stake, slash_count,
    #   reputation_score, reliability_score, security_score,
    #   slashing_risk_score, insurance_premium_score,
    #   predicted_slash_prob, registered_at, last_updated,
    #   is_whitelisted, metadata_hash }
    operators: TreeMap[str, str]

    # ── Evidence packages ─────────────────────────────────────────────────────
    # { incident_id, operator_address, violation_type, network,
    #   block_number, merkle_root, evidence_count,
    #   evidence_summary_hash, submitted_by, timestamp }
    evidence_packages: TreeMap[str, str]

    # ── AI verdicts ───────────────────────────────────────────────────────────
    # { incident_id, fault_probability, severity_score, confidence_score,
    #   recommended_action, verdict_hash, analysis_block }
    ai_verdicts: TreeMap[str, str]

    # ── Slashing cases ────────────────────────────────────────────────────────
    # { case_id, operator_address, incident_id, violation_type, network,
    #   stake_at_risk, slash_bps, slash_amount, executed_amount,
    #   fault_probability, severity_score, confidence_score,
    #   stage, on_chain_hash, appeal_deadline_block,
    #   created_block, resolved_block }
    slashing_cases: TreeMap[str, str]

    # ── Insurance claims ──────────────────────────────────────────────────────
    # { claim_id, organization, incident_id, claimant_address,
    #   coverage_amount, claimed_amount, assessed_damage, approved_amount,
    #   status, ai_eligible, ai_confidence, adjudication_hash,
    #   on_chain_hash, submitted_block, adjudicated_block }
    insurance_claims: TreeMap[str, str]

    # ── Payouts ───────────────────────────────────────────────────────────────
    # { payout_id, claim_id, amount, recipient_address,
    #   token, status, approval_hash, initiated_block, completed_block }
    payouts: TreeMap[str, str]

    # ── Risk predictions ──────────────────────────────────────────────────────
    # { operator_address, prediction_block, failure_probability,
    #   slash_probability, instability_score, security_degradation,
    #   risk_trend, predicted_events, prediction_confidence,
    #   prediction_hash }
    risk_predictions: TreeMap[str, str]

    # ── Governance proposals ──────────────────────────────────────────────────
    # { proposal_id, proposal_type, target_id, proposer,
    #   description_hash, votes_for, votes_against,
    #   status, created_block, deadline_block }
    governance_proposals: TreeMap[str, str]

    # ── Index: operator_address → comma-separated incident IDs ────────────────
    operator_incidents: TreeMap[str, str]

    # ── Index: operator_address → comma-separated case IDs ───────────────────
    operator_cases: TreeMap[str, str]

    # ── Index: claimant_address → comma-separated claim IDs ──────────────────
    operator_claims: TreeMap[str, str]

    # ── Index: proposal_id → comma-separated voter addresses ─────────────────
    proposal_voters: TreeMap[str, str]

    # ── Audit trail: sequential index (as str) → audit entry hash ────────────
    audit_trail: TreeMap[str, str]

    # ── Global counters / config (stored as u256 for on-chain compatibility) ──
    owner: str
    contract_paused: bool
    total_operators: u256
    total_incidents: u256
    total_cases: u256
    total_claims: u256
    total_payouts_amount: u256
    total_staked_wei: u256
    total_slashed_wei: u256
    claim_pool_wei: u256
    audit_count: u256

    # Governable parameters
    min_confidence_slash: u256   # default 70 (out of 100)
    min_confidence_claim: u256   # default 55
    appeal_window: u256          # default 7200 blocks (~24 h on most chains)
    max_slash_bps: u256          # default 10000 (100.00 %)

    # ── Constructor ───────────────────────────────────────────────────────────

    def __init__(self) -> None:
        self.owner = gl.message.sender_address.as_hex
        self.contract_paused = False
        self.total_operators = u256(0)
        self.total_incidents = u256(0)
        self.total_cases = u256(0)
        self.total_claims = u256(0)
        self.total_payouts_amount = u256(0)
        self.total_staked_wei = u256(0)
        self.total_slashed_wei = u256(0)
        self.claim_pool_wei = u256(0)
        self.audit_count = u256(0)
        self.min_confidence_slash = u256(70)
        self.min_confidence_claim = u256(55)
        self.appeal_window = u256(7200)
        self.max_slash_bps = u256(10000)

    # ══════════════════════════════════════════════════════════════════════════
    # INTERNAL HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _only_owner(self) -> None:
        assert gl.message.sender_address.as_hex == self.owner, "Only owner"

    def _not_paused(self) -> None:
        assert not self.contract_paused, "Contract is paused"

    def _clamp(self, v: int, lo: int, hi: int) -> int:
        return max(lo, min(hi, v))

    def _hash(self, data: dict) -> str:
        raw = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def _audit(self, action: str, actor: str, resource_id: str) -> None:
        idx = str(int(self.audit_count))
        entry_hash = self._hash({"action": action, "actor": actor,
                                  "resource_id": resource_id,
                                  "block": 0})
        self.audit_trail[idx] = entry_hash
        self.audit_count = u256(int(self.audit_count) + 1)

    def _append_index(self, mapping: TreeMap, key: str, value: str) -> None:
        existing = ""
        try:
            existing = mapping[key]
        except Exception:
            pass
        if existing == "":
            mapping[key] = value
        else:
            if value not in existing.split(","):
                mapping[key] = existing + "," + value

    def _get_operator(self, address: str) -> dict:
        assert address in self.operators, "Operator not found"
        return json.loads(self.operators[address])

    def _set_operator(self, data: dict) -> None:
        self.operators[data["address"]] = json.dumps(data)

    def _get_case(self, case_id: str) -> dict:
        assert case_id in self.slashing_cases, "Case not found"
        return json.loads(self.slashing_cases[case_id])

    def _set_case(self, data: dict) -> None:
        self.slashing_cases[data["case_id"]] = json.dumps(data)

    def _get_claim(self, claim_id: str) -> dict:
        assert claim_id in self.insurance_claims, "Claim not found"
        return json.loads(self.insurance_claims[claim_id])

    def _set_claim(self, data: dict) -> None:
        self.insurance_claims[data["claim_id"]] = json.dumps(data)

    def _safe_int(self, data: dict, key: str, default: int) -> int:
        try:
            return self._clamp(int(data.get(key, default)), 0, 100)
        except Exception:
            return default

    def _state_u256(self, data: dict, key: str) -> u256:
        try:
            return u256(int(data.get(key, "0")))
        except Exception:
            return u256(0)

    def _fetch_text(self, url: str) -> str:
        if not url:
            return ""

        def _strip_html(html: str) -> str:
            text = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
            text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
            title = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
            description = re.search(
                r'(?is)<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
                html,
            )
            og_description = re.search(
                r'(?is)<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']',
                html,
            )
            head_bits = []
            if title:
                head_bits.append(unescape(title.group(1)))
            if description:
                head_bits.append(unescape(description.group(1)))
            if og_description:
                head_bits.append(unescape(og_description.group(1)))
            text = re.sub(r"(?is)<[^>]+>", " ", text)
            text = unescape(text)
            text = re.sub(r"\s+", " ", text).strip()
            if head_bits:
                text = " ".join(head_bits + ([text] if text else []))
            return text

        def _summarize(text: str, limit: int = 1200) -> str:
            if not text:
                return ""
            chunks = re.split(r"(?<=[.!?])\s+", text)
            summary = ""
            for chunk in chunks:
                chunk = chunk.strip()
                if not chunk:
                    continue
                candidate = f"{summary} {chunk}".strip()
                if len(candidate) > limit:
                    break
                summary = candidate
            if not summary:
                summary = text[:limit]
            return summary[:limit]

        def fetch() -> str:
            response = gl.nondet.web.get(url)
            status = getattr(response, "status_code", getattr(response, "status", 200))
            if status >= 400 and status < 500:
                raise gl.vm.UserError("Evidence source returned client error")
            if status >= 500:
                raise gl.vm.UserError("Evidence source temporarily unavailable")
            body = response.body.decode("utf-8")[:2000]
            summary = _summarize(_strip_html(body))
            if not summary or "<link " in summary or "<html" in summary.lower() or "</" in summary:
                summary = _summarize(re.sub(r"\s+", " ", re.sub(r"(?is)<[^>]+>", " ", body)).strip())
            return summary

        return gl.eq_principle.strict_eq(fetch)

    # ══════════════════════════════════════════════════════════════════════════
    # OPERATOR MANAGEMENT
    # ══════════════════════════════════════════════════════════════════════════

    @gl.public.write.payable
    def register_operator(
        self,
        address: str,
        name: str,
        network: str,
        total_stake: int,
        metadata_hash: str,
    ) -> str:
        self._not_paused()
        assert address not in self.operators, "Operator already registered"
        assert len(name) > 0, "Name is required"
        expected_stake = u256(total_stake)
        if expected_stake <= u256(0):
            raise gl.vm.UserError("Stake must be positive")
        if gl.message.value != expected_stake:
            raise gl.vm.UserError("Must stake exactly total_stake wei")

        op = {
            "address": address,
            "name": name,
            "network": network,
            "status": "active",
            "total_stake": str(gl.message.value),
            "staked_wei": str(gl.message.value),
            "slashed_wei": "0",
            "slash_count": 0,
            "reputation_score": 100,
            "reliability_score": 100,
            "security_score": 100,
            "slashing_risk_score": 0,
            "insurance_premium_score": 20,
            "predicted_slash_prob": 0,
            "registered_at": 0,
            "last_updated": 0,
            "is_whitelisted": False,
            "metadata_hash": metadata_hash,
        }
        self._set_operator(op)
        self.operator_incidents[address] = ""
        self.operator_cases[address] = ""
        self.operator_claims[address] = ""
        self.total_operators = u256(int(self.total_operators) + 1)
        self.total_staked_wei = self.total_staked_wei + gl.message.value
        self._audit("operator_registered", gl.message.sender_address.as_hex, address)
        return address

    @gl.public.write.payable
    def update_operator_stake(self, address: str, new_stake: int) -> bool:
        self._not_paused()
        op = self._get_operator(address)
        additional_stake = u256(new_stake)
        if additional_stake <= u256(0):
            raise gl.vm.UserError("Stake increase must be positive")
        if gl.message.value != additional_stake:
            raise gl.vm.UserError("Must stake exactly new_stake wei")
        current = self._state_u256(op, "staked_wei")
        updated = current + gl.message.value
        op["total_stake"] = str(updated)
        op["staked_wei"] = str(updated)
        op["last_updated"] = 0
        self._set_operator(op)
        self.total_staked_wei = self.total_staked_wei + gl.message.value
        self._audit("operator_stake_updated", gl.message.sender_address.as_hex, address)
        return True

    @gl.public.write
    def update_operator_status(self, address: str, status: str) -> bool:
        self._not_paused()
        self._only_owner()
        valid = ["active", "inactive", "jailed", "slashed", "suspended"]
        assert status in valid, "Invalid status"
        op = self._get_operator(address)
        op["status"] = status
        op["last_updated"] = 0
        self._set_operator(op)
        self._audit("operator_status_updated", gl.message.sender_address.as_hex, address)
        return True

    @gl.public.write
    def whitelist_operator(self, address: str) -> bool:
        self._only_owner()
        op = self._get_operator(address)
        op["is_whitelisted"] = True
        op["last_updated"] = 0
        self._set_operator(op)
        self._audit("operator_whitelisted", gl.message.sender_address.as_hex, address)
        return True

    @gl.public.view
    def get_operator(self, address: str) -> str:
        assert address in self.operators, "Operator not found"
        return self.operators[address]

    @gl.public.view
    def operator_exists(self, address: str) -> bool:
        return address in self.operators

    @gl.public.view
    def get_operator_incidents(self, operator_address: str) -> str:
        try:
            return self.operator_incidents[operator_address]
        except Exception:
            return ""

    @gl.public.view
    def get_operator_cases(self, operator_address: str) -> str:
        try:
            return self.operator_cases[operator_address]
        except Exception:
            return ""

    @gl.public.view
    def get_operator_claims(self, operator_address: str) -> str:
        try:
            return self.operator_claims[operator_address]
        except Exception:
            return ""

    # ══════════════════════════════════════════════════════════════════════════
    # EVIDENCE ANCHORING
    # ══════════════════════════════════════════════════════════════════════════

    @gl.public.write
    def submit_evidence(
        self,
        incident_id: str,
        operator_address: str,
        violation_type: str,
        network: str,
        block_number: int,
        merkle_root: str,
        evidence_count: int,
        evidence_summary_hash: str,
    ) -> str:
        self._not_paused()
        assert len(incident_id) > 0, "incident_id required"
        assert len(merkle_root) > 0, "merkle_root required"
        assert evidence_count > 0, "evidence_count must be positive"

        pkg = {
            "incident_id": incident_id,
            "operator_address": operator_address,
            "violation_type": violation_type,
            "network": network,
            "block_number": block_number,
            "merkle_root": merkle_root,
            "evidence_count": evidence_count,
            "evidence_summary_hash": evidence_summary_hash,
            "submitted_by": gl.message.sender_address.as_hex,
            "timestamp": 0,
        }
        self.evidence_packages[incident_id] = json.dumps(pkg)
        self.total_incidents = u256(int(self.total_incidents) + 1)
        self._append_index(self.operator_incidents, operator_address, incident_id)
        self._audit("evidence_submitted", gl.message.sender_address.as_hex, incident_id)
        return incident_id

    @gl.public.write
    def fetch_and_submit_evidence(
        self,
        incident_id: str,
        operator_address: str,
        violation_type: str,
        network: str,
        block_number: int,
        evidence_url: str,
    ) -> str:
        self._not_paused()
        assert len(incident_id) > 0, "incident_id required"
        assert len(evidence_url) > 0, "evidence_url required"

        fetched = self._fetch_text(evidence_url)
        summary_hash = self._hash({"url": evidence_url, "summary": fetched})
        pkg = {
            "incident_id": incident_id,
            "operator_address": operator_address,
            "violation_type": violation_type,
            "network": network,
            "block_number": block_number,
            "merkle_root": summary_hash,
            "evidence_count": 1,
            "evidence_summary_hash": summary_hash,
            "evidence_url": evidence_url,
            "web_evidence_preview": fetched[:500],
            "web_evidence_summary": fetched,
            "submitted_by": gl.message.sender_address.as_hex,
            "timestamp": 0,
        }
        self.evidence_packages[incident_id] = json.dumps(pkg)
        self.total_incidents = u256(int(self.total_incidents) + 1)
        self._append_index(self.operator_incidents, operator_address, incident_id)
        self._audit("web_evidence_submitted", gl.message.sender_address.as_hex, incident_id)
        return incident_id

    @gl.public.view
    def get_evidence(self, incident_id: str) -> str:
        assert incident_id in self.evidence_packages, "Evidence not found"
        return self.evidence_packages[incident_id]

    @gl.public.view
    def verify_merkle_root(self, incident_id: str, expected_root: str) -> bool:
        if incident_id not in self.evidence_packages:
            return False
        pkg = json.loads(self.evidence_packages[incident_id])
        return pkg["merkle_root"] == expected_root

    # ══════════════════════════════════════════════════════════════════════════
    # AI FAULT ANALYSIS  — non-deterministic LLM
    # ══════════════════════════════════════════════════════════════════════════

    @gl.public.write
    def analyze_fault(
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
        current_reputation: int,
    ) -> str:
        self._not_paused()

        prompt = f"""You are a senior blockchain security analyst for SlashSure.
Analyze the violation and return a fault assessment as JSON.

INCIDENT:
- ID: {incident_id}
- Network: {network}
- Violation: {violation_type}
- Evidence: {evidence_summary[:1200]}

OPERATOR:
- Address: {operator_address}
- Reputation: {current_reputation}/100
- Prior slashes: {prior_slash_count}
- Uptime: {uptime_pct}%
- Stake at risk: {stake_amount}
- History: {operator_history[:400]}

SEVERITY GUIDELINES:
- double_signing / coordinated_attack → fault_probability 75-95, severity 80-95
- oracle_manipulation / censorship → fault_probability 65-85, severity 70-85
- data_withholding / consensus_failure → fault_probability 55-80, severity 65-80
- downtime > 24h / sla_violation → fault_probability 40-70, severity 50-70
- downtime < 6h / incorrect_ai_output → fault_probability 15-45, severity 20-50
- Repeat offender (prior_slash_count > 1): add 10 to fault_probability

recommended_action rules:
- fault_probability < 25 → "dismiss"
- 25-39 → "monitor"
- 40-54 or severity < 40 → "slash_low"
- 55-69 and severity 40-69 → "slash_medium"
- 70-84 or severity 70-84 → "slash_high"
- >= 85 or severity >= 85 → "slash_critical"

Return ONLY valid JSON, no markdown fences:
{{"fault_probability": <0-100>, "severity_score": <0-100>, "confidence_score": <0-100>}}"""

        def nondet() -> str:
            res = gl.nondet.exec_prompt(prompt)
            res = res.replace("```json", "").replace("```", "").strip()
            data = json.loads(res)
            fp   = max(0, min(100, int(data["fault_probability"])))
            sv   = max(0, min(100, int(data["severity_score"])))
            cf   = max(0, min(100, int(data["confidence_score"])))
            return json.dumps({"fault_probability": fp,
                               "severity_score": sv,
                               "confidence_score": cf})

        raw = gl.eq_principle.prompt_comparative(
            nondet,
            principle="fault_probability within 20, severity_score within 20, "
                      "confidence_score within 20"
        )

        try:
            data = json.loads(raw)
            fp   = self._safe_int(data, "fault_probability", 50)
            sv   = self._safe_int(data, "severity_score", 50)
            cf   = self._safe_int(data, "confidence_score", 40)
        except Exception:
            fp, sv, cf = 50, 50, 40

        # Derive recommended_action deterministically from fault_probability
        if fp < 25:
            act = "dismiss"
        elif fp < 40:
            act = "monitor"
        elif fp < 55 or sv < 40:
            act = "slash_low"
        elif fp < 70 and sv < 70:
            act = "slash_medium"
        elif fp < 85 or sv < 85:
            act = "slash_high"
        else:
            act = "slash_critical"

        verdict = {
            "incident_id": incident_id,
            "fault_probability": fp,
            "severity_score": sv,
            "confidence_score": cf,
            "recommended_action": act,
            "verdict_hash": self._hash({"incident_id": incident_id, "fp": fp, "sv": sv, "act": act}),
            "analysis_block": 0,
        }
        self.ai_verdicts[incident_id] = json.dumps(verdict)
        self._audit("fault_analyzed", "llm", incident_id)
        return json.dumps(verdict)

    @gl.public.view
    def get_verdict(self, incident_id: str) -> str:
        assert incident_id in self.ai_verdicts, "No verdict found"
        return self.ai_verdicts[incident_id]

    # ══════════════════════════════════════════════════════════════════════════
    # SLASHING CASES
    # ══════════════════════════════════════════════════════════════════════════

    @gl.public.write
    def create_slashing_case(
        self,
        case_id: str,
        operator_address: str,
        incident_id: str,
        violation_type: str,
        network: str,
        stake_at_risk: int,
    ) -> str:
        self._not_paused()
        assert operator_address in self.operators, "Operator not found"
        assert case_id not in self.slashing_cases, "Case already exists"
        assert incident_id in self.ai_verdicts, "Run analyze_fault first"

        verdict = json.loads(self.ai_verdicts[incident_id])
        case = {
            "case_id": case_id,
            "operator_address": operator_address,
            "incident_id": incident_id,
            "violation_type": violation_type,
            "network": network,
            "stake_at_risk": stake_at_risk,
            "slash_bps": 0,
            "slash_amount": 0,
            "executed_amount": 0,
            "fault_probability": verdict["fault_probability"],
            "severity_score": verdict["severity_score"],
            "confidence_score": verdict["confidence_score"],
            "stage": "ai_analysis",
            "on_chain_hash": "",
            "appeal_deadline_block": 0,
            "created_block": 0,
            "resolved_block": 0,
        }
        self._set_case(case)
        self.total_cases = u256(int(self.total_cases) + 1)
        self._append_index(self.operator_cases, operator_address, case_id)
        self._audit("case_created", gl.message.sender_address.as_hex, case_id)
        return case_id

    @gl.public.write
    def generate_slash_recommendation(
        self,
        case_id: str,
        evidence_summary: str,
        operator_history: str,
        network_policy: str,
        current_reputation: int,
    ) -> str:
        self._not_paused()
        case = self._get_case(case_id)

        fp    = case["fault_probability"]
        sv    = case["severity_score"]
        cf    = case["confidence_score"]
        stake = int(case["stake_at_risk"])

        # Compute slash_bps deterministically from fault_probability and severity_score
        if cf < 60:
            bps = 0
        elif fp < 40:
            bps = max(50, int(fp * 4))
        elif fp < 66:
            bps = 200 + int((fp - 40) * 15)
        elif fp < 85:
            bps = 600 + int((fp - 66) * 47)
        else:
            bps = 1500 + int((fp - 85) * 56)
        # Adjust for reputation
        if current_reputation > 85 and bps > 0:
            bps = int(bps * 0.75)
        bps = max(0, min(int(self.max_slash_bps), bps))
        amt = max(0, int((bps * stake) / 10000))

        # Only ask AI for confidence score (narrow, non-blocking field)
        prompt = f"""You are a senior slashing arbitrator for SlashSure.
Rate your confidence in the following slashing recommendation.

CASE: {case_id} | Fault: {fp}/100 | Severity: {sv}/100 | Network: {network_policy}
EVIDENCE: {evidence_summary[:500]}

Return ONLY valid JSON, no markdown fences:
{{"confidence": <0-100>}}"""

        def nondet() -> str:
            res = gl.nondet.exec_prompt(prompt)
            res = res.replace("```json", "").replace("```", "").strip()
            data = json.loads(res)
            conf = max(0, min(100, int(data["confidence"])))
            return json.dumps({"confidence": conf})

        raw = gl.eq_principle.prompt_comparative(
            nondet,
            principle="confidence within 30"
        )

        try:
            conf = self._safe_int(json.loads(raw), "confidence", 50)
        except Exception:
            conf = 50

        rec_hash = self._hash({"case_id": case_id, "slash_bps": bps, "slash_amount": amt})
        case["slash_bps"]      = bps
        case["slash_amount"]   = amt
        case["confidence_score"] = conf
        case["stage"]          = "recommended"
        case["on_chain_hash"]  = rec_hash
        self._set_case(case)
        self._audit("slash_recommended", "llm", case_id)
        return json.dumps({"case_id": case_id, "slash_bps": bps,
                           "slash_amount": amt, "confidence": conf,
                           "on_chain_hash": rec_hash, "stage": "recommended"})

    @gl.public.write
    def approve_slashing(self, case_id: str) -> str:
        self._not_paused()
        self._only_owner()
        case = self._get_case(case_id)
        assert case["stage"] == "recommended", "Must be in recommended stage"

        case["stage"] = "approved"
        case["appeal_deadline_block"] = 0
        self._set_case(case)

        op = self._get_operator(case["operator_address"])
        op["status"] = "jailed"
        op["last_updated"] = 0
        self._set_operator(op)

        self._audit("slashing_approved", gl.message.sender_address.as_hex, case_id)
        return json.dumps({"case_id": case_id, "stage": "approved",
                           "appeal_deadline_block": case["appeal_deadline_block"]})

    @gl.public.write
    def reject_slashing(self, case_id: str, reason: str) -> str:
        self._not_paused()
        self._only_owner()
        case = self._get_case(case_id)
        assert case["stage"] in ["recommended", "ai_analysis"], "Cannot reject at this stage"

        case["stage"] = "rejected"
        case["resolved_block"] = 0
        self._set_case(case)
        self._audit("slashing_rejected", gl.message.sender_address.as_hex, case_id)
        return json.dumps({"case_id": case_id, "stage": "rejected"})

    @gl.public.write
    def execute_slashing(self, case_id: str, actual_slash_amount: int) -> str:
        self._not_paused()
        self._only_owner()
        case = self._get_case(case_id)
        assert case["stage"] == "approved", "Must be approved"
        slash_amount = u256(actual_slash_amount)
        if slash_amount <= u256(0):
            raise gl.vm.UserError("Slash amount must be positive")

        op = self._get_operator(case["operator_address"])
        staked = self._state_u256(op, "staked_wei")
        if staked <= u256(0):
            raise gl.vm.UserError("No operator stake deposited")
        if slash_amount > staked:
            raise gl.vm.UserError("Slash exceeds deposited stake")

        remaining = staked - slash_amount
        case["executed_amount"] = str(slash_amount)
        case["stage"] = "executed"
        case["resolved_block"] = 0
        self._set_case(case)

        op["status"] = "slashed"
        op["slash_count"] = op.get("slash_count", 0) + 1
        op["total_stake"] = str(remaining)
        op["staked_wei"] = str(remaining)
        op["slashed_wei"] = str(self._state_u256(op, "slashed_wei") + slash_amount)
        penalty = 15 + op["slash_count"] * 5
        op["reputation_score"] = max(0, op.get("reputation_score", 100) - penalty)
        op["last_updated"] = 0
        self._set_operator(op)
        self.total_staked_wei = self.total_staked_wei - slash_amount
        self.total_slashed_wei = self.total_slashed_wei + slash_amount

        self._audit("slashing_executed", gl.message.sender_address.as_hex, case_id)
        _send_gen(self.owner, slash_amount)
        return json.dumps({"case_id": case_id, "stage": "executed",
                           "executed_amount": str(slash_amount)})

    @gl.public.write
    def appeal_slashing(self, case_id: str, rationale_hash: str) -> str:
        self._not_paused()
        case = self._get_case(case_id)
        assert case["stage"] == "approved", "Can only appeal approved cases"
        # appeal always open (no block-based timing on StudioNet)

        case["stage"] = "appealed"
        self._set_case(case)
        self._audit("slashing_appealed", gl.message.sender_address.as_hex, case_id)
        return json.dumps({"case_id": case_id, "stage": "appealed"})

    @gl.public.write
    def ai_review_appeal(
        self,
        case_id: str,
        original_summary: str,
        appeal_arguments: str,
        new_evidence: str,
    ) -> str:
        self._not_paused()
        case = self._get_case(case_id)
        assert case["stage"] == "appealed", "Must be in appealed stage"

        orig_bps  = case["slash_bps"]
        orig_fp   = case["fault_probability"]
        orig_sv   = case["severity_score"]
        stake     = case["stake_at_risk"]

        prompt = f"""You are an impartial senior arbitrator for SlashSure.

Review this appeal and determine if the slashing decision should be upheld, reduced, or overturned.

ORIGINAL DECISION:
- Fault Probability: {orig_fp}/100
- Severity: {orig_sv}/100
- Slash: {orig_bps} basis points
- Summary: {original_summary[:600]}

APPEAL ARGUMENTS: {appeal_arguments[:700]}
NEW EVIDENCE: {new_evidence[:500]}

GUIDELINES:
- "uphold": original decision correct, no material new evidence
- "reduce": mitigating factors justify 20-50% reduction; revised_slash_bps < original
- "overturn": clearly wrong; new evidence exonerates operator

Return ONLY valid JSON, no markdown fences:
{{"outcome": "<uphold|reduce|overturn>", "revised_slash_bps": <0-{orig_bps}>, "confidence": <0-100>}}"""

        def nondet() -> str:
            res = gl.nondet.exec_prompt(prompt)
            res = res.replace("```json", "").replace("```", "").strip()
            data = json.loads(res)
            outcome = str(data["outcome"])
            if outcome not in ["uphold", "reduce", "overturn"]:
                outcome = "uphold"
            bps = max(0, min(orig_bps, int(data.get("revised_slash_bps", orig_bps))))
            conf = max(0, min(100, int(data.get("confidence", 50))))
            return json.dumps({"outcome": outcome, "revised_slash_bps": bps, "confidence": conf})

        raw = gl.eq_principle.prompt_comparative(
            nondet,
            principle="outcome must match exactly, revised_slash_bps within 100, confidence within 10"
        )

        try:
            data    = json.loads(raw)
            outcome = str(data.get("outcome", "uphold"))
            revised = max(0, min(orig_bps, int(data.get("revised_slash_bps", orig_bps))))
            conf    = self._safe_int(data, "confidence", 50)
        except Exception:
            outcome, revised, conf = "uphold", orig_bps, 40

        if outcome not in ["uphold", "reduce", "overturn"]:
            outcome = "uphold"

        if outcome == "overturn":
            case["stage"] = "rejected"
            case["slash_bps"] = 0
            case["slash_amount"] = 0
            case["resolved_block"] = 0
            op = self._get_operator(case["operator_address"])
            op["status"] = "active"
            op["last_updated"] = 0
            self._set_operator(op)
        elif outcome == "reduce":
            case["slash_bps"]    = revised
            case["slash_amount"] = int((revised * stake) / 10000)
            case["stage"]        = "approved"
            case["appeal_deadline_block"] = 0
        else:
            case["stage"] = "approved"
            case["appeal_deadline_block"] = 0

        case["confidence_score"] = conf
        self._set_case(case)
        self._audit("appeal_reviewed", "llm", case_id)

        return json.dumps({"case_id": case_id, "outcome": outcome,
                           "revised_slash_bps": case["slash_bps"],
                           "revised_slash_amount": case["slash_amount"],
                           "confidence": conf, "stage": case["stage"]})

    @gl.public.view
    def get_slashing_case(self, case_id: str) -> str:
        assert case_id in self.slashing_cases, "Not found"
        return self.slashing_cases[case_id]

    # ══════════════════════════════════════════════════════════════════════════
    # INSURANCE CLAIMS
    # ══════════════════════════════════════════════════════════════════════════

    @gl.public.write.payable
    def fund_claim_pool(self) -> str:
        self._not_paused()
        if gl.message.value <= u256(0):
            raise gl.vm.UserError("Claim pool funding must be positive")
        self.claim_pool_wei = self.claim_pool_wei + gl.message.value
        self._audit("claim_pool_funded", gl.message.sender_address.as_hex, str(gl.message.value))
        return json.dumps({"claim_pool_wei": str(self.claim_pool_wei)})

    @gl.public.write
    def submit_claim(
        self,
        claim_id: str,
        organization: str,
        incident_id: str,
        claimant_address: str,
        coverage_amount: int,
        claimed_amount: int,
    ) -> str:
        self._not_paused()
        assert claim_id not in self.insurance_claims, "Claim already exists"
        assert claimed_amount <= coverage_amount, "Claimed exceeds coverage"
        assert claimed_amount > 0, "Amount must be positive"

        claim = {
            "claim_id": claim_id,
            "organization": organization,
            "incident_id": incident_id,
            "claimant_address": claimant_address,
            "coverage_amount": coverage_amount,
            "claimed_amount": claimed_amount,
            "approved_deposited": "0",
            "assessed_damage": 0,
            "approved_amount": 0,
            "status": "submitted",
            "ai_eligible": False,
            "ai_confidence": 0,
            "adjudication_hash": "",
            "on_chain_hash": "",
            "submitted_block": 0,
            "adjudicated_block": 0,
        }
        self._set_claim(claim)
        self.total_claims = u256(int(self.total_claims) + 1)
        self._append_index(self.operator_claims, claimant_address, claim_id)
        self._audit("claim_submitted", gl.message.sender_address.as_hex, claim_id)
        return json.dumps({"claim_id": claim_id, "status": "submitted"})

    @gl.public.write
    def adjudicate_claim(
        self,
        claim_id: str,
        incident_summary: str,
        policy_terms: str,
        damage_evidence: str,
        negligence_score: int,
        claimant_history: str,
    ) -> str:
        self._not_paused()
        claim = self._get_claim(claim_id)
        coverage = claim["coverage_amount"]
        claimed  = claim["claimed_amount"]

        prompt = f"""You are a senior insurance adjudicator for SlashSure.

Adjudicate this claim for validator/operator insurance.

CLAIM: {claim_id}
Coverage: {coverage} GEN — Claimed: {claimed} GEN

INCIDENT: {incident_summary[:900]}
POLICY TERMS: {policy_terms[:500]}
DAMAGE EVIDENCE: {damage_evidence[:700]}
NEGLIGENCE SCORE: {negligence_score}/100 (higher = more at fault)
CLAIMANT HISTORY: {claimant_history[:200]}

GUIDELINES:
- coverage_eligible = true if incident matches policy, is documented, and not excluded
- Common exclusions: force majeure, pure protocol bugs, unregistered operators
- negligence_score > 70 → likely 80-100% of claimed
- negligence_score 40-70 → 40-75% of claimed
- negligence_score < 40 → likely not eligible
- assessed_damage ≤ claimed_amount; approved_amount ≤ assessed_damage

Return ONLY valid JSON, no markdown fences:
{{"assessed_damage": <integer>, "approved_amount": <integer>, "confidence_score": <0-100>}}"""

        def nondet() -> str:
            res = gl.nondet.exec_prompt(prompt)
            res = res.replace("```json", "").replace("```", "").strip()
            data     = json.loads(res)
            assessed = max(0, min(claimed, int(data["assessed_damage"])))
            approved = max(0, min(assessed, int(data["approved_amount"])))
            conf     = max(0, min(100, int(data["confidence_score"])))
            return json.dumps({"assessed_damage": assessed,
                               "approved_amount": approved,
                               "confidence_score": conf})

        raw = gl.eq_principle.prompt_comparative(
            nondet,
            principle="approved_amount within 10%, assessed_damage within 10%, "
                      "confidence_score within 20"
        )

        try:
            data     = json.loads(raw)
            assessed = max(0, min(claimed, int(data.get("assessed_damage", 0))))
            approved = max(0, min(assessed, int(data.get("approved_amount", 0))))
            conf     = self._safe_int(data, "confidence_score", 40)
        except Exception:
            assessed, approved, conf = 0, 0, 30

        # Derive eligible and status deterministically from numeric outputs
        eligible = approved > 0
        if approved >= assessed and assessed > 0:
            status = "approved"
        elif approved > 0:
            status = "partial"
        else:
            status = "rejected"

        adj_hash    = self._hash({"claim_id": claim_id, "eligible": eligible, "approved": approved})
        status_hash = self._hash({"claim_id": claim_id, "status": status, "amount": approved})

        claim["ai_eligible"]       = eligible
        claim["assessed_damage"]   = assessed
        claim["approved_amount"]   = approved
        claim["approved_deposited"] = str(approved)
        claim["ai_confidence"]     = conf
        claim["adjudication_hash"] = adj_hash
        claim["on_chain_hash"]     = status_hash
        claim["status"]            = status
        claim["adjudicated_block"] = 0
        self._set_claim(claim)
        self._audit("claim_adjudicated", "llm", claim_id)

        return json.dumps({"claim_id": claim_id, "status": status,
                           "ai_eligible": eligible, "assessed_damage": assessed,
                           "approved_amount": approved, "ai_confidence": conf,
                           "adjudication_hash": adj_hash})

    @gl.public.write
    def authorize_payout(
        self,
        claim_id: str,
        payout_id: str,
        amount: int,
        recipient_address: str,
    ) -> str:
        self._not_paused()
        self._only_owner()
        claim = self._get_claim(claim_id)
        assert claim["status"] in ["approved", "partial"], "Claim not approved"
        assert payout_id not in self.payouts, "Payout already exists"
        assert amount <= claim["approved_amount"], "Exceeds approved amount"
        assert amount > 0, "Amount must be positive"
        payout_amount = u256(amount)
        approved_deposited = self._state_u256(claim, "approved_deposited")
        if approved_deposited <= u256(0):
            raise gl.vm.UserError("No approved claim balance")
        if payout_amount > approved_deposited:
            raise gl.vm.UserError("Payout exceeds approved claim balance")
        if payout_amount > self.claim_pool_wei:
            raise gl.vm.UserError("Claim pool has insufficient GEN")

        approval_hash = self._hash({"claim_id": claim_id, "payout_id": payout_id,
                                     "amount": amount, "recipient": recipient_address,
                                     "block": 0})
        claim["approved_deposited"] = str(approved_deposited - payout_amount)
        claim["status"] = "paid"
        self._set_claim(claim)
        self.claim_pool_wei = self.claim_pool_wei - payout_amount
        self.total_payouts_amount = self.total_payouts_amount + payout_amount

        payout = {
            "payout_id": payout_id,
            "claim_id": claim_id,
            "amount": str(payout_amount),
            "recipient_address": recipient_address,
            "token": "GEN",
            "status": "completed",
            "approval_hash": approval_hash,
            "initiated_block": 0,
            "completed_block": 0,
        }
        self.payouts[payout_id] = json.dumps(payout)
        self._audit("payout_authorized", gl.message.sender_address.as_hex, payout_id)
        _send_gen(recipient_address, payout_amount)

        return json.dumps({"payout_id": payout_id, "approval_hash": approval_hash,
                           "status": "completed", "amount": str(payout_amount)})

    @gl.public.write
    def complete_payout(self, payout_id: str, tx_hash: str) -> str:
        self._only_owner()
        assert payout_id in self.payouts, "Payout not found"
        payout = json.loads(self.payouts[payout_id])
        payout["status"] = "completed"
        payout["completed_block"] = 0
        self.payouts[payout_id] = json.dumps(payout)
        self._audit("payout_completed", gl.message.sender_address.as_hex, payout_id)
        return json.dumps({"payout_id": payout_id, "status": "completed", "tx_hash": tx_hash})

    @gl.public.view
    def get_claim(self, claim_id: str) -> str:
        assert claim_id in self.insurance_claims, "Not found"
        return self.insurance_claims[claim_id]

    @gl.public.view
    def get_payout(self, payout_id: str) -> str:
        assert payout_id in self.payouts, "Not found"
        return self.payouts[payout_id]

    # ══════════════════════════════════════════════════════════════════════════
    # REPUTATION SCORING  — non-deterministic LLM
    # ══════════════════════════════════════════════════════════════════════════

    @gl.public.write
    def compute_reputation(
        self,
        operator_address: str,
        uptime_30d: int,
        uptime_90d: int,
        slash_total: int,
        slash_90d: int,
        incidents_90d: int,
        missed_blocks_30d: int,
        total_blocks_30d: int,
        oracle_accuracy: int,
        peer_score: int,
        stake_stability: int,
        network: str,
    ) -> str:
        self._not_paused()
        assert operator_address in self.operators, "Operator not found"

        missed_pct = 0 if total_blocks_30d == 0 else int((missed_blocks_30d * 100) / total_blocks_30d)

        prompt = f"""You are a reputation scoring engine for SlashSure.

Compute comprehensive operator scores.

OPERATOR: {operator_address} — Network: {network}
- Uptime 30d: {uptime_30d}% | Uptime 90d: {uptime_90d}%
- Missed blocks 30d: {missed_blocks_30d}/{total_blocks_30d} ({missed_pct}%)
- Total slashes: {slash_total} | Slashes 90d: {slash_90d}
- Incidents 90d: {incidents_90d}
- Oracle accuracy: {oracle_accuracy}/100
- Peer score: {peer_score}/100
- Stake stability: {stake_stability}/100

SCORING RULES:

reliability_score (0-100):
- >= 99% uptime, < 0.1% missed → 95-100
- 97-99% uptime → 80-94
- 95-97% → 65-79
- 90-95% → 40-64
- < 90% → 0-39

security_score (0-100):
- No incidents/slashes → 90-100
- 1-2 minor incidents → 70-89
- 1 slash → 50-69
- 2+ slashes → 20-49

slashing_risk_score (0-100, higher = MORE risky):
- 0 slashes, clean 90d → 0-10
- 1 minor slash → 20-35
- 1 major slash → 40-60
- 2+ or recent → 65-85
- Active jailed/suspended → 85-100

insurance_premium_score (0-100, higher = higher premium):
- overall >= 90 → 10-25
- overall 70-89 → 30-50
- overall 50-69 → 55-70
- overall < 50 → 75-100

overall_score = reliability*0.35 + security*0.35 + (100-slash_risk)*0.20 + peer_score*0.10

Return ONLY valid JSON, no markdown fences:
{{"reliability_score": <0-100>, "security_score": <0-100>, "slashing_risk_score": <0-100>, "insurance_premium_score": <0-100>, "overall_score": <0-100>}}"""

        def nondet() -> str:
            res = gl.nondet.exec_prompt(prompt)
            res = res.replace("```json", "").replace("```", "").strip()
            data = json.loads(res)
            rel  = max(0, min(100, int(data["reliability_score"])))
            sec  = max(0, min(100, int(data["security_score"])))
            sr   = max(0, min(100, int(data["slashing_risk_score"])))
            ins  = max(0, min(100, int(data["insurance_premium_score"])))
            ov   = max(0, min(100, int(data["overall_score"])))
            return json.dumps({"reliability_score": rel, "security_score": sec,
                               "slashing_risk_score": sr, "insurance_premium_score": ins,
                               "overall_score": ov})

        raw = gl.eq_principle.prompt_comparative(
            nondet,
            principle="All numeric score fields within 20"
        )

        try:
            data = json.loads(raw)
            rel  = self._safe_int(data, "reliability_score", 80)
            sec  = self._safe_int(data, "security_score", 80)
            sr   = self._safe_int(data, "slashing_risk_score", 20)
            ins  = self._safe_int(data, "insurance_premium_score", 40)
            ov   = self._safe_int(data, "overall_score", 80)
        except Exception:
            rel, sec, sr, ins, ov = 75, 75, 25, 40, 75

        # Derive risk_trend deterministically from slashing_risk_score
        if sr <= 15:
            rt = "improving"
        elif sr >= 50:
            rt = "degrading"
        else:
            rt = "stable"

        score_hash = self._hash({"operator": operator_address, "reliability": rel,
                                  "security": sec, "overall": ov})

        op = self._get_operator(operator_address)
        op["reliability_score"]       = rel
        op["security_score"]          = sec
        op["slashing_risk_score"]     = sr
        op["insurance_premium_score"] = ins
        op["reputation_score"]        = ov
        op["last_updated"]            = 0
        self._set_operator(op)
        self._audit("reputation_computed", "llm", operator_address)

        return json.dumps({"operator_address": operator_address,
                           "reliability_score": rel, "security_score": sec,
                           "slashing_risk_score": sr, "insurance_premium_score": ins,
                           "overall_score": ov, "risk_trend": rt,
                           "score_hash": score_hash})

    # ══════════════════════════════════════════════════════════════════════════
    # PREDICTIVE RISK ENGINE  — non-deterministic LLM
    # ══════════════════════════════════════════════════════════════════════════

    @gl.public.write
    def predict_risk(
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
    ) -> str:
        self._not_paused()
        assert operator_address in self.operators, "Operator not found"
        op = self._get_operator(operator_address)

        prompt = f"""You are a predictive risk analyst for SlashSure.

Predict future risk for this operator over the next 30 days.

CURRENT STATE:
- Reputation: {op["reputation_score"]}/100
- Reliability: {op["reliability_score"]}/100
- Security: {op["security_score"]}/100
- Slashing Risk: {op["slashing_risk_score"]}/100
- Total Slashes: {op["slash_count"]}
- Status: {op["status"]}

TRENDS:
- Performance: {perf_trend[:300]}
- Infra Alerts (30d): {infra_alerts[:300]}
- Peer Comparison: {peer_comparison[:200]}
- Market Conditions: {market_conditions[:200]}
- Historical Patterns: {historical_patterns[:300]}
- Days Since Last Incident: {days_since_incident}
- Stake Growth Rate (%/mo): {stake_growth_rate}
- Delegator Change Rate (%/mo): {delegator_change_rate}

PREDICTION GUIDELINES:

failure_probability (any failure in 30d):
- Excellent trend, no alerts → 0-10
- Minor degradation → 10-25
- Concerning alerts → 25-50
- Multiple red flags → 50-75
- Imminent failure indicators → 75-95

slash_probability always <= failure_probability:
- Clean history + improving → 0-5
- Some risk factors → 5-15
- Significant risk → 15-35
- High risk + active violations → 35-65

predicted_events: one or more from [downtime, double_signing, oracle_manipulation, consensus_failure, sla_violation, performance_degradation, none]

Return ONLY valid JSON, no markdown fences:
{{"failure_probability": <0-100>, "slash_probability": <0-100>, "instability_score": <0-100>, "security_degradation": <0-100>, "risk_trend": "<improving|stable|degrading>", "predicted_events": "<comma-separated or none>", "prediction_confidence": <0-100>}}"""

        def nondet() -> str:
            res = gl.nondet.exec_prompt(prompt)
            res = res.replace("```json", "").replace("```", "").strip()
            data = json.loads(res)
            fp   = max(0, min(100, int(data["failure_probability"])))
            sp   = max(0, min(fp,  int(data["slash_probability"])))
            ins  = max(0, min(100, int(data["instability_score"])))
            sd   = max(0, min(100, int(data["security_degradation"])))
            rt   = str(data.get("risk_trend", "stable"))
            if rt not in ["improving", "stable", "degrading"]:
                rt = "stable"
            pe   = str(data.get("predicted_events", "none"))
            pc   = max(0, min(100, int(data["prediction_confidence"])))
            return json.dumps({"failure_probability": fp, "slash_probability": sp,
                               "instability_score": ins, "security_degradation": sd,
                               "risk_trend": rt, "predicted_events": pe,
                               "prediction_confidence": pc})

        raw = gl.eq_principle.prompt_comparative(
            nondet,
            principle="failure_probability within 10, slash_probability within 10, "
                      "instability_score within 10, security_degradation within 10, "
                      "risk_trend must match exactly, prediction_confidence within 15"
        )

        try:
            data = json.loads(raw)
            fp   = self._safe_int(data, "failure_probability", 20)
            sp   = max(0, min(fp, self._safe_int(data, "slash_probability", 5)))
            ins  = self._safe_int(data, "instability_score", 20)
            sd   = self._safe_int(data, "security_degradation", 20)
            rt   = str(data.get("risk_trend", "stable"))
            pe   = str(data.get("predicted_events", "none"))
            pc   = self._safe_int(data, "prediction_confidence", 50)
        except Exception:
            fp, sp, ins, sd, rt, pe, pc = 20, 5, 20, 20, "stable", "none", 40

        if rt not in ["improving", "stable", "degrading"]:
            rt = "stable"

        pred_hash = self._hash({"operator": operator_address, "fp": fp, "sp": sp, "rt": rt})
        prediction = {
            "operator_address": operator_address,
            "prediction_block": 0,
            "failure_probability": fp,
            "slash_probability": sp,
            "instability_score": ins,
            "security_degradation": sd,
            "risk_trend": rt,
            "predicted_events": pe,
            "prediction_confidence": pc,
            "prediction_hash": pred_hash,
        }
        self.risk_predictions[operator_address] = json.dumps(prediction)

        op["predicted_slash_prob"] = sp
        op["last_updated"] = 0
        self._set_operator(op)
        self._audit("risk_predicted", "llm", operator_address)

        return json.dumps(prediction)

    @gl.public.view
    def get_risk_prediction(self, operator_address: str) -> str:
        assert operator_address in self.risk_predictions, "No prediction found"
        return self.risk_predictions[operator_address]

    # ══════════════════════════════════════════════════════════════════════════
    # GOVERNANCE
    # ══════════════════════════════════════════════════════════════════════════

    @gl.public.write
    def create_proposal(
        self,
        target_id: str,
        proposal_type: str,
        description_hash: str,
        voting_period_blocks: int,
    ) -> str:
        self._not_paused()
        assert len(target_id) > 0, "target_id required"
        valid_types = ["appeal_slash", "review_claim", "update_params", "whitelist_operator"]
        assert proposal_type in valid_types, "Invalid proposal type"

        raw_id = "{}:{}:{}:{}".format(
            gl.message.sender_address.as_hex, target_id, proposal_type, 0
        )
        proposal_id = hashlib.sha256(raw_id.encode()).hexdigest()[:32]
        assert proposal_id not in self.governance_proposals, "Proposal already exists"

        proposal = {
            "proposal_id": proposal_id,
            "proposal_type": proposal_type,
            "target_id": target_id,
            "proposer": gl.message.sender_address.as_hex,
            "description_hash": description_hash,
            "votes_for": 0,
            "votes_against": 0,
            "status": "active",
            "created_block": 0,
            "deadline_block": 0,
        }
        self.governance_proposals[proposal_id] = json.dumps(proposal)
        self.proposal_voters[proposal_id] = ""
        self._audit("proposal_created", gl.message.sender_address.as_hex, proposal_id)

        return json.dumps({"proposal_id": proposal_id, "status": "active",
                           "deadline_block": proposal["deadline_block"]})

    @gl.public.write
    def vote(self, proposal_id: str, vote_for: bool) -> str:
        self._not_paused()
        assert proposal_id in self.governance_proposals, "Proposal not found"
        proposal = json.loads(self.governance_proposals[proposal_id])
        assert proposal["status"] == "active", "Proposal not active"
        # no deadline enforcement without block number

        voter    = gl.message.sender_address.as_hex
        existing = ""
        try:
            existing = self.proposal_voters[proposal_id]
        except Exception:
            pass

        assert voter not in existing.split(","), "Already voted"
        self.proposal_voters[proposal_id] = (existing + "," + voter).lstrip(",")

        if vote_for:
            proposal["votes_for"] += 1
        else:
            proposal["votes_against"] += 1
        self.governance_proposals[proposal_id] = json.dumps(proposal)
        self._audit("proposal_voted", voter, proposal_id)

        return json.dumps({"proposal_id": proposal_id,
                           "votes_for": proposal["votes_for"],
                           "votes_against": proposal["votes_against"]})

    @gl.public.write
    def finalize_proposal(self, proposal_id: str) -> str:
        self._not_paused()
        assert proposal_id in self.governance_proposals, "Not found"
        proposal = json.loads(self.governance_proposals[proposal_id])
        assert proposal["status"] == "active", "Already finalized"
        # no deadline enforcement without block number

        total = proposal["votes_for"] + proposal["votes_against"]
        if total == 0:
            proposal["status"] = "failed"
        elif proposal["votes_for"] > proposal["votes_against"]:
            proposal["status"] = "passed"
        else:
            proposal["status"] = "failed"

        self.governance_proposals[proposal_id] = json.dumps(proposal)
        self._audit("proposal_finalized", gl.message.sender_address.as_hex, proposal_id)

        return json.dumps({"proposal_id": proposal_id, "status": proposal["status"],
                           "votes_for": proposal["votes_for"],
                           "votes_against": proposal["votes_against"]})

    @gl.public.view
    def get_proposal(self, proposal_id: str) -> str:
        assert proposal_id in self.governance_proposals, "Not found"
        return self.governance_proposals[proposal_id]

    # ══════════════════════════════════════════════════════════════════════════
    # ADMIN
    # ══════════════════════════════════════════════════════════════════════════

    @gl.public.write
    def pause(self) -> bool:
        self._only_owner()
        self.contract_paused = True
        self._audit("contract_paused", gl.message.sender_address.as_hex, "contract")
        return True

    @gl.public.write
    def unpause(self) -> bool:
        self._only_owner()
        self.contract_paused = False
        self._audit("contract_unpaused", gl.message.sender_address.as_hex, "contract")
        return True

    @gl.public.write
    def transfer_ownership(self, new_owner: str) -> bool:
        self._only_owner()
        assert len(new_owner) > 0, "new_owner required"
        old_owner  = self.owner
        self.owner = new_owner
        self._audit("ownership_transferred", old_owner, new_owner)
        return True

    @gl.public.write
    def update_params(
        self,
        min_confidence_slash: int,
        min_confidence_claim: int,
        appeal_window_blocks: int,
        max_slash_bps: int,
    ) -> bool:
        self._only_owner()
        assert 0 < min_confidence_slash <= 100, "Invalid min_confidence_slash"
        assert 0 < min_confidence_claim <= 100, "Invalid min_confidence_claim"
        assert appeal_window_blocks > 0, "Invalid appeal_window_blocks"
        assert 0 < max_slash_bps <= 10000, "Invalid max_slash_bps"
        self.min_confidence_slash = u256(min_confidence_slash)
        self.min_confidence_claim = u256(min_confidence_claim)
        self.appeal_window        = u256(appeal_window_blocks)
        self.max_slash_bps        = u256(max_slash_bps)
        self._audit("params_updated", gl.message.sender_address.as_hex, "contract")
        return True

    # ══════════════════════════════════════════════════════════════════════════
    # VIEWS
    # ══════════════════════════════════════════════════════════════════════════

    @gl.public.view
    def get_stats(self) -> str:
        return json.dumps({
            "owner": self.owner,
            "paused": self.contract_paused,
            "total_operators": int(self.total_operators),
            "total_incidents": int(self.total_incidents),
            "total_cases": int(self.total_cases),
            "total_claims": int(self.total_claims),
            "total_payouts_amount": int(self.total_payouts_amount),
            "total_staked_wei": str(self.total_staked_wei),
            "total_slashed_wei": str(self.total_slashed_wei),
            "claim_pool_wei": str(self.claim_pool_wei),
            "audit_count": int(self.audit_count),
            "min_confidence_slash": int(self.min_confidence_slash),
            "min_confidence_claim": int(self.min_confidence_claim),
            "appeal_window_blocks": int(self.appeal_window),
            "max_slash_bps": int(self.max_slash_bps),
        })

    @gl.public.view
    def get_audit_entry(self, index: int) -> str:
        key = str(index)
        assert key in self.audit_trail, "Index out of range"
        return self.audit_trail[key]

    @gl.public.view
    def is_operator_jailed(self, operator_address: str) -> bool:
        if operator_address not in self.operators:
            return False
        op = json.loads(self.operators[operator_address])
        return op["status"] in ["jailed", "slashed", "suspended"]
