# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *

import json
import hashlib


# ─── SlashSure Intelligent Contract ──────────────────────────────────────────
#
# Deployed on GenLayer StudioNet. Token: GEN.
#
# Responsibilities:
#   1. Operator registration and status management
#   2. Evidence package anchoring (Merkle root on-chain)
#   3. AI-powered fault analysis  [non-deterministic LLM]
#   4. Slashing recommendation    [non-deterministic LLM]
#   5. Insurance claim adjudication [non-deterministic LLM]
#   6. Reputation scoring         [non-deterministic LLM]
#   7. Predictive risk engine     [non-deterministic LLM]
#   8. Payout authorization
#   9. Governance / appeals
#  10. Immutable audit trail
#
# Consensus strategy:
#   All LLM methods return numeric scores (0–100 integers) + a short
#   categorical string. eq_principle.prompt_comparative is used with a
#   tolerance-aware principle so minor numeric variance is accepted and
#   UNDETERMINED is avoided.
# ─────────────────────────────────────────────────────────────────────────────


# ── Storable data classes ─────────────────────────────────────────────────────

@allow_storage
@dataclass
class OperatorRecord:
    address: str
    name: str
    network: str
    status: str           # active | inactive | jailed | slashed | suspended
    total_stake: u256
    slash_count: u256
    reputation_score: u256    # 0-100
    reliability_score: u256   # 0-100
    security_score: u256      # 0-100
    slashing_risk_score: u256 # 0-100
    insurance_premium_score: u256  # 0-100
    predicted_slash_prob: u256     # 0-100
    reputation_hash: str
    registered_at: u256   # block number
    last_updated: u256
    is_whitelisted: bool
    metadata_hash: str


@allow_storage
@dataclass
class EvidencePackage:
    incident_id: str
    operator_address: str
    violation_type: str
    network: str
    block_number: u256
    merkle_root: str
    evidence_count: u256
    evidence_summary_hash: str
    submitted_by: str
    timestamp: u256


@allow_storage
@dataclass
class AIVerdict:
    incident_id: str
    fault_probability: u256   # 0-100
    severity_score: u256      # 0-100
    confidence_score: u256    # 0-100
    recommended_action: str   # slash_critical|slash_high|slash_medium|slash_low|dismiss|monitor
    verdict_hash: str
    analysis_block: u256


@allow_storage
@dataclass
class SlashingRecord:
    case_id: str
    operator_address: str
    incident_id: str
    violation_type: str
    network: str
    stake_at_risk: u256
    slash_bps: u256           # basis points e.g. 500 = 5.00%
    slash_amount: u256
    executed_amount: u256
    fault_probability: u256
    severity_score: u256
    confidence_score: u256
    stage: str                # open|ai_analysis|recommended|approved|rejected|executed|appealed
    on_chain_hash: str
    appeal_deadline_block: u256
    created_block: u256
    resolved_block: u256


@allow_storage
@dataclass
class InsuranceClaim:
    claim_id: str
    organization: str
    incident_id: str
    claimant_address: str
    coverage_amount: u256
    claimed_amount: u256
    assessed_damage: u256
    approved_amount: u256
    status: str               # submitted|under_review|approved|rejected|partial|paid
    ai_eligible: bool
    ai_confidence: u256
    adjudication_hash: str
    on_chain_hash: str
    submitted_block: u256
    adjudicated_block: u256


@allow_storage
@dataclass
class PayoutRecord:
    payout_id: str
    claim_id: str
    amount: u256
    recipient_address: str
    token: str
    status: str
    approval_hash: str
    initiated_block: u256
    completed_block: u256


@allow_storage
@dataclass
class GovernanceProposal:
    proposal_id: str
    proposal_type: str   # appeal_slash|review_claim|update_params|whitelist_operator
    target_id: str
    proposer: str
    description_hash: str
    votes_for: u256
    votes_against: u256
    status: str          # active|passed|failed|executed
    created_block: u256
    deadline_block: u256


@allow_storage
@dataclass
class RiskPrediction:
    operator_address: str
    prediction_block: u256
    failure_probability: u256    # 0-100
    slash_probability: u256      # 0-100
    instability_score: u256      # 0-100
    security_degradation: u256   # 0-100
    risk_trend: str              # improving|stable|degrading
    predicted_events_json: str   # JSON array string
    prediction_confidence: u256  # 0-100
    prediction_hash: str


# ── Contract ──────────────────────────────────────────────────────────────────

class SlashSureContract(gl.Contract):

    # ── State ─────────────────────────────────────────────────────────────────

    # Core registries
    operators: TreeMap[str, OperatorRecord]
    evidence_packages: TreeMap[str, EvidencePackage]
    ai_verdicts: TreeMap[str, AIVerdict]
    slashing_cases: TreeMap[str, SlashingRecord]
    insurance_claims: TreeMap[str, InsuranceClaim]
    payouts: TreeMap[str, PayoutRecord]
    governance_proposals: TreeMap[str, GovernanceProposal]
    risk_predictions: TreeMap[str, RiskPrediction]

    # Indexes: operator → comma-separated IDs stored as a single str
    # (Avoids nested generics that break schema loading)
    operator_incidents: TreeMap[str, str]
    operator_cases: TreeMap[str, str]
    operator_claims: TreeMap[str, str]

    # Governance: proposal_id → comma-separated voter addresses
    proposal_voters: TreeMap[str, str]

    # Audit trail: index → audit_hash  (u256 key → str value)
    audit_trail: TreeMap[u256, str]

    # Administration
    owner: str
    contract_paused: bool
    total_operators: u256
    total_incidents: u256
    total_cases: u256
    total_claims: u256
    total_payouts_amount: u256
    audit_count: u256

    # Governable parameters
    min_confidence_slash: u256   # default 70
    min_confidence_claim: u256   # default 55
    appeal_window: u256          # default 7200 blocks (~24 h)
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
        self.audit_count = u256(0)
        self.min_confidence_slash = u256(70)
        self.min_confidence_claim = u256(55)
        self.appeal_window = u256(7200)
        self.max_slash_bps = u256(10000)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _only_owner(self) -> None:
        assert gl.message.sender_address.as_hex == self.owner, "Only owner"

    def _not_paused(self) -> None:
        assert not self.contract_paused, "Contract paused"

    def _require_operator(self, address: str) -> None:
        assert address in self.operators, "Operator not found"

    def _hash(self, data: dict) -> str:
        raw = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def _audit(self, action: str, actor: str, resource_id: str, extra: dict) -> str:
        entry = {
            "action": action,
            "actor": actor,
            "resource_id": resource_id,
            "block": int(gl.block.number),
            "extra_hash": self._hash(extra),
        }
        h = self._hash(entry)
        idx = self.audit_count
        self.audit_trail[idx] = h
        self.audit_count = u256(int(self.audit_count) + 1)
        return h

    def _append_index(self, tmap: TreeMap, key: str, value: str) -> None:
        existing = tmap.get(key, "")
        if existing == "":
            tmap[key] = value
        else:
            tmap[key] = existing + "," + value

    def _clamp(self, val: int, lo: int, hi: int) -> int:
        return max(lo, min(hi, val))

    def _safe_parse_int(self, data: dict, key: str, default: int) -> int:
        try:
            return self._clamp(int(data.get(key, default)), 0, 100)
        except Exception:
            return default

    # ── Operator Management ───────────────────────────────────────────────────

    @gl.public.write
    def register_operator(
        self,
        address: str,
        name: str,
        network: str,
        total_stake: int,
        metadata_hash: str,
    ) -> str:
        self._not_paused()
        assert address not in self.operators, "Already registered"
        assert len(name) > 0, "Name required"

        rec = OperatorRecord(
            address=address,
            name=name,
            network=network,
            status="active",
            total_stake=u256(total_stake),
            slash_count=u256(0),
            reputation_score=u256(100),
            reliability_score=u256(100),
            security_score=u256(100),
            slashing_risk_score=u256(0),
            insurance_premium_score=u256(100),
            predicted_slash_prob=u256(0),
            reputation_hash="",
            registered_at=u256(int(gl.block.number)),
            last_updated=u256(int(gl.block.number)),
            is_whitelisted=False,
            metadata_hash=metadata_hash,
        )
        self.operators[address] = rec
        self.operator_incidents[address] = ""
        self.operator_cases[address] = ""
        self.operator_claims[address] = ""
        self.total_operators = u256(int(self.total_operators) + 1)
        self._audit("operator_registered", gl.message.sender_address.as_hex, address, {"name": name, "network": network})
        return address

    @gl.public.write
    def update_operator_stake(self, address: str, new_stake: int) -> bool:
        self._not_paused()
        self._require_operator(address)
        rec = self.operators[address]
        rec.total_stake = u256(new_stake)
        rec.last_updated = u256(int(gl.block.number))
        self.operators[address] = rec
        self._audit("operator_stake_updated", gl.message.sender_address.as_hex, address, {"new_stake": new_stake})
        return True

    @gl.public.write
    def update_operator_status(self, address: str, status: str) -> bool:
        self._not_paused()
        self._only_owner()
        self._require_operator(address)
        valid = ["active", "inactive", "jailed", "slashed", "suspended"]
        assert status in valid, "Invalid status"
        rec = self.operators[address]
        rec.status = status
        rec.last_updated = u256(int(gl.block.number))
        self.operators[address] = rec
        self._audit("operator_status_updated", gl.message.sender_address.as_hex, address, {"status": status})
        return True

    @gl.public.write
    def whitelist_operator(self, address: str) -> bool:
        self._only_owner()
        self._require_operator(address)
        rec = self.operators[address]
        rec.is_whitelisted = True
        rec.last_updated = u256(int(gl.block.number))
        self.operators[address] = rec
        return True

    @gl.public.view
    def get_operator(self, address: str) -> dict:
        self._require_operator(address)
        rec = self.operators[address]
        return {
            "address": rec.address,
            "name": rec.name,
            "network": rec.network,
            "status": rec.status,
            "total_stake": int(rec.total_stake),
            "slash_count": int(rec.slash_count),
            "reputation_score": int(rec.reputation_score),
            "reliability_score": int(rec.reliability_score),
            "security_score": int(rec.security_score),
            "slashing_risk_score": int(rec.slashing_risk_score),
            "insurance_premium_score": int(rec.insurance_premium_score),
            "predicted_slash_prob": int(rec.predicted_slash_prob),
            "reputation_hash": rec.reputation_hash,
            "is_whitelisted": rec.is_whitelisted,
            "registered_at": int(rec.registered_at),
            "last_updated": int(rec.last_updated),
        }

    @gl.public.view
    def operator_exists(self, address: str) -> bool:
        return address in self.operators

    # ── Evidence Anchoring ────────────────────────────────────────────────────

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
        assert evidence_count > 0, "evidence_count must be > 0"

        pkg = EvidencePackage(
            incident_id=incident_id,
            operator_address=operator_address,
            violation_type=violation_type,
            network=network,
            block_number=u256(block_number),
            merkle_root=merkle_root,
            evidence_count=u256(evidence_count),
            evidence_summary_hash=evidence_summary_hash,
            submitted_by=gl.message.sender_address.as_hex,
            timestamp=u256(int(gl.block.number)),
        )
        self.evidence_packages[incident_id] = pkg
        self.total_incidents = u256(int(self.total_incidents) + 1)

        if operator_address in self.operator_incidents:
            self._append_index(self.operator_incidents, operator_address, incident_id)

        self._audit("evidence_submitted", gl.message.sender_address.as_hex, incident_id, {
            "operator": operator_address, "violation": violation_type, "merkle": merkle_root
        })
        return incident_id

    @gl.public.view
    def get_evidence(self, incident_id: str) -> dict:
        assert incident_id in self.evidence_packages, "Not found"
        pkg = self.evidence_packages[incident_id]
        return {
            "incident_id": pkg.incident_id,
            "operator_address": pkg.operator_address,
            "violation_type": pkg.violation_type,
            "network": pkg.network,
            "block_number": int(pkg.block_number),
            "merkle_root": pkg.merkle_root,
            "evidence_count": int(pkg.evidence_count),
            "evidence_summary_hash": pkg.evidence_summary_hash,
            "submitted_by": pkg.submitted_by,
        }

    @gl.public.view
    def verify_evidence(self, incident_id: str, expected_merkle_root: str) -> bool:
        if incident_id not in self.evidence_packages:
            return False
        return self.evidence_packages[incident_id].merkle_root == expected_merkle_root

    # ── AI Fault Analysis (non-deterministic) ─────────────────────────────────

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
    ) -> dict:
        self._not_paused()

        prompt = f"""You are an expert blockchain security analyst for SlashSure, an AI-native slashing monitoring platform.

Analyze the following protocol violation and return a fault assessment.

INCIDENT:
- ID: {incident_id}
- Network: {network}
- Violation Type: {violation_type}
- Evidence: {evidence_summary[:1500]}

OPERATOR CONTEXT:
- Address: {operator_address}
- Reputation Score: {current_reputation}/100
- Prior Slash Count: {prior_slash_count}
- Uptime: {uptime_pct}%
- Stake at Risk: {stake_amount}
- History: {operator_history[:500]}

SEVERITY GUIDELINES:
- double_signing or coordinated_attack: fault_probability 75-95, severity 80-95
- oracle_manipulation or censorship: fault_probability 65-85, severity 70-85
- data_withholding or consensus_failure: fault_probability 55-80, severity 65-80
- downtime > 24h or sla_violation: fault_probability 40-70, severity 50-70
- downtime < 6h or incorrect_ai_output: fault_probability 15-45, severity 20-50
- Repeat offender (prior_slash_count > 1): increase fault_probability by 10

OUTPUT: Return ONLY valid JSON, no markdown, no extra text:
{{"fault_probability": <integer 0-100>, "severity_score": <integer 0-100>, "confidence_score": <integer 0-100>, "recommended_action": "<slash_critical|slash_high|slash_medium|slash_low|dismiss|monitor>", "reasoning": "<one sentence>"}}

Rules for recommended_action:
- fault_probability < 25 → dismiss
- fault_probability 25-39 → monitor
- fault_probability 40-54 OR severity < 40 → slash_low
- fault_probability 55-69 AND severity 40-69 → slash_medium
- fault_probability 70-84 OR severity 70-84 → slash_high
- fault_probability >= 85 OR severity >= 85 → slash_critical"""

        def run_analysis() -> str:
            result = gl.nondet.exec_prompt(prompt)
            return result.replace("```json", "").replace("```", "").strip()

        raw = gl.eq_principle.prompt_comparative(
            run_analysis,
            "fault_probability within 8, severity_score within 8, confidence_score within 10, recommended_action must match exactly"
        )

        try:
            data = json.loads(raw)
            fault_prob = self._clamp(int(data.get("fault_probability", 50)), 0, 100)
            severity   = self._clamp(int(data.get("severity_score", 50)), 0, 100)
            confidence = self._clamp(int(data.get("confidence_score", 50)), 0, 100)
            action     = str(data.get("recommended_action", "monitor"))
        except Exception:
            fault_prob, severity, confidence, action = 50, 50, 40, "monitor"

        valid_actions = ["slash_critical", "slash_high", "slash_medium", "slash_low", "dismiss", "monitor"]
        if action not in valid_actions:
            action = "monitor"

        verdict_data = {"incident_id": incident_id, "fault_probability": fault_prob, "severity_score": severity, "confidence_score": confidence, "recommended_action": action}
        v_hash = self._hash(verdict_data)

        verdict = AIVerdict(
            incident_id=incident_id,
            fault_probability=u256(fault_prob),
            severity_score=u256(severity),
            confidence_score=u256(confidence),
            recommended_action=action,
            verdict_hash=v_hash,
            analysis_block=u256(int(gl.block.number)),
        )
        self.ai_verdicts[incident_id] = verdict
        self._audit("ai_fault_analyzed", "llm", incident_id, verdict_data)

        return {
            "incident_id": incident_id,
            "fault_probability": fault_prob,
            "severity_score": severity,
            "confidence_score": confidence,
            "recommended_action": action,
            "verdict_hash": v_hash,
        }

    @gl.public.view
    def get_verdict(self, incident_id: str) -> dict:
        assert incident_id in self.ai_verdicts, "No verdict found"
        v = self.ai_verdicts[incident_id]
        return {
            "incident_id": v.incident_id,
            "fault_probability": int(v.fault_probability),
            "severity_score": int(v.severity_score),
            "confidence_score": int(v.confidence_score),
            "recommended_action": v.recommended_action,
            "verdict_hash": v.verdict_hash,
            "analysis_block": int(v.analysis_block),
        }

    # ── Slashing Cases ────────────────────────────────────────────────────────

    @gl.public.write
    def create_slashing_case(
        self,
        case_id: str,
        operator_address: str,
        incident_id: str,
        violation_type: str,
        network: str,
        stake_at_risk: int,
    ) -> dict:
        self._not_paused()
        self._require_operator(operator_address)
        assert case_id not in self.slashing_cases, "Case already exists"
        assert incident_id in self.ai_verdicts, "Run analyze_fault first"

        v = self.ai_verdicts[incident_id]

        rec = SlashingRecord(
            case_id=case_id,
            operator_address=operator_address,
            incident_id=incident_id,
            violation_type=violation_type,
            network=network,
            stake_at_risk=u256(stake_at_risk),
            slash_bps=u256(0),
            slash_amount=u256(0),
            executed_amount=u256(0),
            fault_probability=v.fault_probability,
            severity_score=v.severity_score,
            confidence_score=v.confidence_score,
            stage="ai_analysis",
            on_chain_hash="",
            appeal_deadline_block=u256(0),
            created_block=u256(int(gl.block.number)),
            resolved_block=u256(0),
        )
        self.slashing_cases[case_id] = rec
        self.total_cases = u256(int(self.total_cases) + 1)

        if operator_address in self.operator_cases:
            self._append_index(self.operator_cases, operator_address, case_id)

        self._audit("slashing_case_created", gl.message.sender_address.as_hex, case_id, {
            "operator": operator_address, "incident": incident_id, "stake": stake_at_risk
        })
        return {"case_id": case_id, "stage": "ai_analysis"}

    @gl.public.write
    def generate_slash_recommendation(
        self,
        case_id: str,
        operator_address: str,
        evidence_summary: str,
        operator_history: str,
        network_policy: str,
        stake_at_risk: int,
        current_reputation: int,
    ) -> dict:
        self._not_paused()
        assert case_id in self.slashing_cases, "Case not found"
        case = self.slashing_cases[case_id]

        fault_prob = int(case.fault_probability)
        severity   = int(case.severity_score)
        confidence = int(case.confidence_score)

        prompt = f"""You are a senior slashing arbitrator for SlashSure, a decentralized network security platform.

Compute a slashing recommendation for the following case.

CASE:
- Case ID: {case_id}
- Operator: {operator_address}
- Network: {network_policy}
- AI Fault Probability: {fault_prob}/100
- AI Severity Score: {severity}/100
- AI Confidence Score: {confidence}/100
- Stake at Risk: {stake_at_risk} (token units)
- Current Operator Reputation: {current_reputation}/100

EVIDENCE:
{evidence_summary[:1200]}

OPERATOR HISTORY:
{operator_history[:500]}

SLASHING PERCENTAGE GUIDELINES (in basis points, 100 bps = 1%):
- Unconfirmed (confidence < 60): 0 bps → dismiss or monitor only
- Minor/low severity (fault < 40): 50–200 bps (0.5%–2%)
- Medium severity (fault 40–65): 200–600 bps (2%–6%)
- High severity (fault 66–84): 600–1500 bps (6%–15%)
- Critical (fault >= 85): 1500–10000 bps (15%–100%)
- Repeat offender: multiply base by 1.5
- First offense + high reputation (>85): reduce base by 25%

slash_amount = floor(slash_bps * stake_at_risk / 10000)

OUTPUT: Return ONLY valid JSON, no markdown:
{{"slash_bps": <integer 0-10000>, "slash_amount": <integer>, "confidence": <integer 0-100>, "is_first_offense": <true|false>, "rationale": "<two sentences max>"}}"""

        def run_recommendation() -> str:
            result = gl.nondet.exec_prompt(prompt)
            return result.replace("```json", "").replace("```", "").strip()

        raw = gl.eq_principle.prompt_comparative(
            run_recommendation,
            "slash_bps within 50 basis points, slash_amount proportionally within 1%, confidence within 10, is_first_offense must match exactly"
        )

        try:
            data = json.loads(raw)
            slash_bps    = self._clamp(int(data.get("slash_bps", 0)), 0, int(self.max_slash_bps))
            slash_amount = max(0, int((slash_bps * stake_at_risk) / 10000))
            rec_confidence = self._clamp(int(data.get("confidence", 50)), 0, 100)
        except Exception:
            slash_bps = max(0, int(severity * 30))
            slash_amount = int((slash_bps * stake_at_risk) / 10000)
            rec_confidence = 40

        record_data = {"case_id": case_id, "slash_bps": slash_bps, "slash_amount": slash_amount}
        rec_hash = self._hash(record_data)

        case.slash_bps      = u256(slash_bps)
        case.slash_amount   = u256(slash_amount)
        case.confidence_score = u256(rec_confidence)
        case.stage          = "recommended"
        case.on_chain_hash  = rec_hash
        self.slashing_cases[case_id] = case

        self._audit("slash_recommended", "llm", case_id, record_data)
        return {
            "case_id": case_id,
            "slash_bps": slash_bps,
            "slash_amount": slash_amount,
            "confidence": rec_confidence,
            "on_chain_hash": rec_hash,
            "stage": "recommended",
        }

    @gl.public.write
    def approve_slashing(self, case_id: str) -> dict:
        self._not_paused()
        self._only_owner()
        assert case_id in self.slashing_cases, "Not found"
        case = self.slashing_cases[case_id]
        assert case.stage == "recommended", "Must be in recommended stage"

        case.stage = "approved"
        case.appeal_deadline_block = u256(int(gl.block.number) + int(self.appeal_window))
        self.slashing_cases[case_id] = case

        if case.operator_address in self.operators:
            op = self.operators[case.operator_address]
            op.status = "jailed"
            op.last_updated = u256(int(gl.block.number))
            self.operators[case.operator_address] = op

        self._audit("slashing_approved", gl.message.sender_address.as_hex, case_id, {"slash_bps": int(case.slash_bps)})
        return {"case_id": case_id, "stage": "approved", "appeal_deadline_block": int(case.appeal_deadline_block)}

    @gl.public.write
    def reject_slashing(self, case_id: str, reason: str) -> dict:
        self._not_paused()
        self._only_owner()
        assert case_id in self.slashing_cases, "Not found"
        case = self.slashing_cases[case_id]
        assert case.stage in ["recommended", "ai_analysis"], "Cannot reject at this stage"

        case.stage = "rejected"
        case.resolved_block = u256(int(gl.block.number))
        self.slashing_cases[case_id] = case
        self._audit("slashing_rejected", gl.message.sender_address.as_hex, case_id, {"reason": reason})
        return {"case_id": case_id, "stage": "rejected"}

    @gl.public.write
    def execute_slashing(self, case_id: str, actual_slash_amount: int) -> dict:
        self._not_paused()
        self._only_owner()
        assert case_id in self.slashing_cases, "Not found"
        case = self.slashing_cases[case_id]
        assert case.stage == "approved", "Must be approved"
        appeal_done = int(gl.block.number) >= int(case.appeal_deadline_block)
        assert appeal_done, "Appeal window still open"

        case.executed_amount = u256(actual_slash_amount)
        case.stage = "executed"
        case.resolved_block = u256(int(gl.block.number))
        self.slashing_cases[case_id] = case

        if case.operator_address in self.operators:
            op = self.operators[case.operator_address]
            op.status = "slashed"
            op.slash_count = u256(int(op.slash_count) + 1)
            stake = int(op.total_stake)
            op.total_stake = u256(max(0, stake - actual_slash_amount))
            penalty = 15 + int(op.slash_count) * 5
            new_rep = max(0, int(op.reputation_score) - penalty)
            op.reputation_score = u256(new_rep)
            op.last_updated = u256(int(gl.block.number))
            self.operators[case.operator_address] = op

        self._audit("slashing_executed", gl.message.sender_address.as_hex, case_id, {"actual": actual_slash_amount})
        return {"case_id": case_id, "stage": "executed", "executed_amount": actual_slash_amount}

    @gl.public.write
    def appeal_slashing(self, case_id: str, rationale_hash: str) -> dict:
        self._not_paused()
        assert case_id in self.slashing_cases, "Not found"
        case = self.slashing_cases[case_id]
        assert case.stage == "approved", "Can only appeal approved cases"
        assert int(gl.block.number) <= int(case.appeal_deadline_block), "Appeal window closed"

        case.stage = "appealed"
        self.slashing_cases[case_id] = case
        self._audit("slashing_appealed", gl.message.sender_address.as_hex, case_id, {"rationale_hash": rationale_hash})
        return {"case_id": case_id, "stage": "appealed"}

    @gl.public.write
    def ai_review_appeal(
        self,
        case_id: str,
        original_summary: str,
        appeal_arguments: str,
        new_evidence: str,
        operator_record: str,
    ) -> dict:
        self._not_paused()
        assert case_id in self.slashing_cases, "Not found"
        case = self.slashing_cases[case_id]
        assert case.stage == "appealed", "Must be in appealed stage"

        orig_bps = int(case.slash_bps)
        orig_fault = int(case.fault_probability)
        orig_sev = int(case.severity_score)

        prompt = f"""You are an impartial senior arbitrator for SlashSure.

Review this appeal against a slashing decision and determine if it should be upheld, reduced, or overturned.

ORIGINAL DECISION:
- Case ID: {case_id}
- Fault Probability: {orig_fault}/100
- Severity: {orig_sev}/100
- Slash: {orig_bps} basis points
- Summary: {original_summary[:600]}

APPEAL ARGUMENTS:
{appeal_arguments[:800]}

NEW EVIDENCE (if any):
{new_evidence[:600]}

OPERATOR RECORD:
{operator_record[:400]}

GUIDELINES:
- uphold: original decision correct, no material new evidence
- reduce: mitigating factors justify 20-50% lower slash
- overturn: clearly wrong, new evidence exonerates operator

revised_slash_bps must be <= {orig_bps} if reducing/overturning.

OUTPUT: Return ONLY valid JSON, no markdown:
{{"outcome": "<uphold|reduce|overturn>", "revised_slash_bps": <integer 0-{orig_bps}>, "confidence": <integer 0-100>, "rationale": "<two sentences>"}}"""

        def run_review() -> str:
            result = gl.nondet.exec_prompt(prompt)
            return result.replace("```json", "").replace("```", "").strip()

        raw = gl.eq_principle.prompt_comparative(
            run_review,
            "outcome must match exactly, revised_slash_bps within 100 basis points, confidence within 10"
        )

        try:
            data = json.loads(raw)
            outcome = str(data.get("outcome", "uphold"))
            revised_bps = self._clamp(int(data.get("revised_slash_bps", orig_bps)), 0, orig_bps)
            confidence = self._clamp(int(data.get("confidence", 50)), 0, 100)
        except Exception:
            outcome = "uphold"
            revised_bps = orig_bps
            confidence = 40

        if outcome not in ["uphold", "reduce", "overturn"]:
            outcome = "uphold"

        stake = int(case.stake_at_risk)

        if outcome == "overturn":
            case.stage = "rejected"
            case.slash_bps = u256(0)
            case.slash_amount = u256(0)
            case.resolved_block = u256(int(gl.block.number))
            if case.operator_address in self.operators:
                op = self.operators[case.operator_address]
                op.status = "active"
                op.last_updated = u256(int(gl.block.number))
                self.operators[case.operator_address] = op
        elif outcome == "reduce":
            case.slash_bps = u256(revised_bps)
            case.slash_amount = u256(int((revised_bps * stake) / 10000))
            case.stage = "approved"
            case.appeal_deadline_block = u256(0)
        else:
            case.stage = "approved"
            case.appeal_deadline_block = u256(0)

        case.confidence_score = u256(confidence)
        self.slashing_cases[case_id] = case
        self._audit("appeal_reviewed", "llm", case_id, {"outcome": outcome, "revised_bps": revised_bps})

        return {
            "case_id": case_id,
            "outcome": outcome,
            "revised_slash_bps": revised_bps,
            "revised_slash_amount": int(case.slash_amount),
            "confidence": confidence,
            "stage": case.stage,
        }

    @gl.public.view
    def get_slashing_case(self, case_id: str) -> dict:
        assert case_id in self.slashing_cases, "Not found"
        c = self.slashing_cases[case_id]
        return {
            "case_id": c.case_id,
            "operator_address": c.operator_address,
            "incident_id": c.incident_id,
            "violation_type": c.violation_type,
            "network": c.network,
            "stake_at_risk": int(c.stake_at_risk),
            "slash_bps": int(c.slash_bps),
            "slash_amount": int(c.slash_amount),
            "executed_amount": int(c.executed_amount),
            "fault_probability": int(c.fault_probability),
            "severity_score": int(c.severity_score),
            "confidence_score": int(c.confidence_score),
            "stage": c.stage,
            "on_chain_hash": c.on_chain_hash,
            "appeal_deadline_block": int(c.appeal_deadline_block),
            "created_block": int(c.created_block),
            "resolved_block": int(c.resolved_block),
        }

    # ── Insurance Claims ──────────────────────────────────────────────────────

    @gl.public.write
    def submit_claim(
        self,
        claim_id: str,
        organization: str,
        incident_id: str,
        claimant_address: str,
        coverage_amount: int,
        claimed_amount: int,
    ) -> dict:
        self._not_paused()
        assert claim_id not in self.insurance_claims, "Claim already exists"
        assert claimed_amount <= coverage_amount, "Claimed exceeds coverage"
        assert claimed_amount > 0, "Amount must be > 0"

        claim = InsuranceClaim(
            claim_id=claim_id,
            organization=organization,
            incident_id=incident_id,
            claimant_address=claimant_address,
            coverage_amount=u256(coverage_amount),
            claimed_amount=u256(claimed_amount),
            assessed_damage=u256(0),
            approved_amount=u256(0),
            status="submitted",
            ai_eligible=False,
            ai_confidence=u256(0),
            adjudication_hash="",
            on_chain_hash="",
            submitted_block=u256(int(gl.block.number)),
            adjudicated_block=u256(0),
        )
        self.insurance_claims[claim_id] = claim
        self.total_claims = u256(int(self.total_claims) + 1)

        if claimant_address in self.operator_claims:
            self._append_index(self.operator_claims, claimant_address, claim_id)

        self._audit("claim_submitted", gl.message.sender_address.as_hex, claim_id, {
            "claimed": claimed_amount, "coverage": coverage_amount
        })
        return {"claim_id": claim_id, "status": "submitted"}

    @gl.public.write
    def adjudicate_claim(
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
        self._not_paused()
        assert claim_id in self.insurance_claims, "Not found"
        claim = self.insurance_claims[claim_id]

        prompt = f"""You are a senior insurance adjudicator for SlashSure, specializing in decentralized network validator insurance.

Adjudicate this insurance claim fairly and precisely according to policy terms.

CLAIM:
- Claim ID: {claim_id}
- Coverage Amount: {coverage_amount} GEN
- Claimed Amount: {claimed_amount} GEN

INCIDENT:
{incident_summary[:1000]}

POLICY TERMS:
{policy_terms[:600]}

DAMAGE EVIDENCE:
{damage_evidence[:800]}

CONTEXT:
- Operator Negligence Score: {negligence_score}/100 (higher = more negligent)
- Network Conditions: {network_conditions[:200]}
- Claimant History: {claimant_history[:200]}

ADJUDICATION GUIDELINES:
- coverage_eligible = true if incident matches policy AND damage is documented AND not excluded
- Common exclusions: force majeure, protocol bugs (not operator fault), unregistered operators
- negligence_score > 70 → full coverage likely (80-100% of claimed)
- negligence_score 40-70 → partial coverage (40-75% of claimed)
- negligence_score < 40 → likely not eligible unless exceptional circumstances
- assessed_damage <= claimed_amount <= coverage_amount
- approved_amount <= assessed_damage

OUTPUT: Return ONLY valid JSON, no markdown:
{{"coverage_eligible": <true|false>, "assessed_damage": <integer>, "approved_amount": <integer>, "confidence_score": <integer 0-100>, "claim_status": "<approved|rejected|partial>", "coverage_pct": <integer 0-100>}}"""

        def run_adjudication() -> str:
            result = gl.nondet.exec_prompt(prompt)
            return result.replace("```json", "").replace("```", "").strip()

        raw = gl.eq_principle.prompt_comparative(
            run_adjudication,
            "coverage_eligible boolean must match exactly, approved_amount within 2% proportional tolerance, assessed_damage within 5%, confidence_score within 10, claim_status must match exactly"
        )

        try:
            data = json.loads(raw)
            eligible       = bool(data.get("coverage_eligible", False))
            assessed       = self._clamp(int(data.get("assessed_damage", 0)), 0, claimed_amount)
            approved       = self._clamp(int(data.get("approved_amount", 0)), 0, assessed)
            ai_conf        = self._clamp(int(data.get("confidence_score", 50)), 0, 100)
            claim_status   = str(data.get("claim_status", "rejected"))
        except Exception:
            eligible, assessed, approved, ai_conf, claim_status = False, 0, 0, 30, "rejected"

        if claim_status not in ["approved", "rejected", "partial"]:
            claim_status = "rejected"

        adj_hash = self._hash({"claim_id": claim_id, "eligible": eligible, "approved": approved, "confidence": ai_conf})
        status_hash = self._hash({"claim_id": claim_id, "status": claim_status, "amount": approved})

        claim.ai_eligible        = eligible
        claim.assessed_damage    = u256(assessed)
        claim.approved_amount    = u256(approved)
        claim.ai_confidence      = u256(ai_conf)
        claim.adjudication_hash  = adj_hash
        claim.on_chain_hash      = status_hash
        claim.status             = claim_status
        claim.adjudicated_block  = u256(int(gl.block.number))
        self.insurance_claims[claim_id] = claim

        self._audit("claim_adjudicated", "llm", claim_id, {
            "eligible": eligible, "approved": approved, "confidence": ai_conf
        })
        return {
            "claim_id": claim_id,
            "status": claim_status,
            "ai_eligible": eligible,
            "assessed_damage": assessed,
            "approved_amount": approved,
            "ai_confidence": ai_conf,
            "adjudication_hash": adj_hash,
        }

    @gl.public.write
    def authorize_payout(
        self,
        claim_id: str,
        payout_id: str,
        amount: int,
        recipient_address: str,
    ) -> dict:
        self._not_paused()
        self._only_owner()
        assert claim_id in self.insurance_claims, "Claim not found"
        assert payout_id not in self.payouts, "Payout already exists"

        claim = self.insurance_claims[claim_id]
        assert claim.status in ["approved", "partial"], "Claim not approved"
        assert amount <= int(claim.approved_amount), "Exceeds approved amount"
        assert amount > 0, "Amount must be > 0"

        approval_data = {
            "claim_id": claim_id, "payout_id": payout_id,
            "amount": amount, "recipient": recipient_address,
            "block": int(gl.block.number),
        }
        approval_hash = self._hash(approval_data)

        payout = PayoutRecord(
            payout_id=payout_id,
            claim_id=claim_id,
            amount=u256(amount),
            recipient_address=recipient_address,
            token="GEN",
            status="authorized",
            approval_hash=approval_hash,
            initiated_block=u256(int(gl.block.number)),
            completed_block=u256(0),
        )
        self.payouts[payout_id] = payout
        self.total_payouts_amount = u256(int(self.total_payouts_amount) + amount)

        claim.status = "paid"
        self.insurance_claims[claim_id] = claim

        self._audit("payout_authorized", gl.message.sender_address.as_hex, payout_id, {"amount": amount})
        return {
            "payout_id": payout_id,
            "claim_id": claim_id,
            "amount": amount,
            "recipient_address": recipient_address,
            "approval_hash": approval_hash,
            "status": "authorized",
        }

    @gl.public.write
    def complete_payout(self, payout_id: str, tx_hash: str) -> dict:
        self._only_owner()
        assert payout_id in self.payouts, "Not found"
        payout = self.payouts[payout_id]
        payout.status = "completed"
        payout.completed_block = u256(int(gl.block.number))
        self.payouts[payout_id] = payout
        self._audit("payout_completed", gl.message.sender_address.as_hex, payout_id, {"tx_hash": tx_hash})
        return {"payout_id": payout_id, "status": "completed"}

    @gl.public.view
    def get_claim(self, claim_id: str) -> dict:
        assert claim_id in self.insurance_claims, "Not found"
        c = self.insurance_claims[claim_id]
        return {
            "claim_id": c.claim_id,
            "organization": c.organization,
            "incident_id": c.incident_id,
            "claimant_address": c.claimant_address,
            "coverage_amount": int(c.coverage_amount),
            "claimed_amount": int(c.claimed_amount),
            "assessed_damage": int(c.assessed_damage),
            "approved_amount": int(c.approved_amount),
            "status": c.status,
            "ai_eligible": c.ai_eligible,
            "ai_confidence": int(c.ai_confidence),
            "adjudication_hash": c.adjudication_hash,
            "on_chain_hash": c.on_chain_hash,
            "submitted_block": int(c.submitted_block),
            "adjudicated_block": int(c.adjudicated_block),
        }

    @gl.public.view
    def get_payout(self, payout_id: str) -> dict:
        assert payout_id in self.payouts, "Not found"
        p = self.payouts[payout_id]
        return {
            "payout_id": p.payout_id,
            "claim_id": p.claim_id,
            "amount": int(p.amount),
            "recipient_address": p.recipient_address,
            "token": p.token,
            "status": p.status,
            "approval_hash": p.approval_hash,
            "initiated_block": int(p.initiated_block),
            "completed_block": int(p.completed_block),
        }

    # ── Reputation Scoring (non-deterministic) ────────────────────────────────

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
    ) -> dict:
        self._not_paused()
        self._require_operator(operator_address)

        missed_pct = 0 if total_blocks_30d == 0 else int((missed_blocks_30d * 100) / total_blocks_30d)

        prompt = f"""You are a reputation scoring engine for SlashSure, computing comprehensive operator scores.

OPERATOR METRICS:
- Address: {operator_address}
- Network: {network}
- Uptime 30d: {uptime_30d}%
- Uptime 90d: {uptime_90d}%
- Missed Blocks 30d: {missed_blocks_30d} / {total_blocks_30d} ({missed_pct}%)
- Total Slashes (all time): {slash_total}
- Slashes (90d): {slash_90d}
- Incidents (90d): {incidents_90d}
- Oracle Accuracy: {oracle_accuracy}/100
- Peer Review Score: {peer_score}/100
- Stake Stability: {stake_stability}/100

SCORING RULES:

reliability_score (0-100):
- >= 99% uptime, < 0.1% missed: 95-100
- 97-99% uptime: 80-94
- 95-97% uptime: 65-79
- 90-95% uptime: 40-64
- < 90% uptime: 0-39

security_score (0-100):
- No incidents/slashes: 90-100
- 1-2 minor incidents: 70-89
- 1 slash: 50-69
- 2+ slashes: 20-49
- Active violations: 0-19

slashing_risk_score (0-100, higher = MORE risky):
- 0 slashes, clean 90d: 0-10
- 1 minor slash: 20-35
- 1 major slash: 40-60
- 2+ slashes or recent: 65-85
- Active jailed/suspended: 85-100

insurance_premium_score (0-100, higher = higher premium charged):
- Excellent (overall >= 90): 10-25
- Good (overall 70-89): 30-50
- Average (overall 50-69): 55-70
- Risky (overall 30-49): 75-90
- High risk (overall < 30): 90-100

overall_score = reliability_score*0.35 + security_score*0.35 + (100 - slashing_risk_score)*0.20 + peer_score*0.10 (round to integer)

OUTPUT: Return ONLY valid JSON, no markdown:
{{"reliability_score": <integer 0-100>, "security_score": <integer 0-100>, "slashing_risk_score": <integer 0-100>, "insurance_premium_score": <integer 0-100>, "overall_score": <integer 0-100>, "risk_trend": "<improving|stable|degrading>"}}"""

        def run_scoring() -> str:
            result = gl.nondet.exec_prompt(prompt)
            return result.replace("```json", "").replace("```", "").strip()

        raw = gl.eq_principle.prompt_comparative(
            run_scoring,
            "All numeric score fields within 5 of each other, risk_trend must match exactly"
        )

        try:
            data = json.loads(raw)
            reliability  = self._clamp(int(data.get("reliability_score", 80)), 0, 100)
            security     = self._clamp(int(data.get("security_score", 80)), 0, 100)
            slash_risk   = self._clamp(int(data.get("slashing_risk_score", 20)), 0, 100)
            ins_premium  = self._clamp(int(data.get("insurance_premium_score", 40)), 0, 100)
            overall      = self._clamp(int(data.get("overall_score", 80)), 0, 100)
            risk_trend   = str(data.get("risk_trend", "stable"))
        except Exception:
            reliability, security, slash_risk, ins_premium, overall, risk_trend = 75, 75, 25, 40, 75, "stable"

        if risk_trend not in ["improving", "stable", "degrading"]:
            risk_trend = "stable"

        score_data = {
            "operator": operator_address,
            "reliability": reliability,
            "security": security,
            "slashing_risk": slash_risk,
            "overall": overall,
        }
        score_hash = self._hash(score_data)

        op = self.operators[operator_address]
        op.reliability_score       = u256(reliability)
        op.security_score          = u256(security)
        op.slashing_risk_score     = u256(slash_risk)
        op.insurance_premium_score = u256(ins_premium)
        op.reputation_score        = u256(overall)
        op.reputation_hash         = score_hash
        op.last_updated            = u256(int(gl.block.number))
        self.operators[operator_address] = op

        self._audit("reputation_computed", "llm", operator_address, score_data)
        return {
            "operator_address": operator_address,
            "reliability_score": reliability,
            "security_score": security,
            "slashing_risk_score": slash_risk,
            "insurance_premium_score": ins_premium,
            "overall_score": overall,
            "risk_trend": risk_trend,
            "score_hash": score_hash,
        }

    # ── Predictive Risk Engine (non-deterministic) ────────────────────────────

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
    ) -> dict:
        self._not_paused()
        self._require_operator(operator_address)
        op = self.operators[operator_address]

        prompt = f"""You are a predictive risk analyst for SlashSure.

Predict future risk for the following validator/operator over the next 30 days.

CURRENT STATE:
- Address: {operator_address}
- Reputation: {int(op.reputation_score)}/100
- Reliability: {int(op.reliability_score)}/100
- Security: {int(op.security_score)}/100
- Slashing Risk: {int(op.slashing_risk_score)}/100
- Total Slashes: {int(op.slash_count)}
- Status: {op.status}

TREND DATA:
- Performance Trend: {perf_trend[:300]}
- Infrastructure Alerts (30d): {infra_alerts[:300]}
- Peer Comparison: {peer_comparison[:200]}
- Market Conditions: {market_conditions[:200]}
- Historical Patterns: {historical_patterns[:300]}
- Days Since Last Incident: {days_since_incident}
- Stake Growth Rate (%/month): {stake_growth_rate}
- Delegator Change Rate (%/month): {delegator_change_rate}

PREDICTION GUIDELINES:

failure_probability (probability of any failure in 30d):
- Excellent trend, no alerts: 0-10
- Minor degradation: 10-25
- Concerning alerts or deteriorating trend: 25-50
- Multiple red flags: 50-75
- Imminent failure indicators: 75-95

slash_probability (probability of slashable event in 30d):
- Always <= failure_probability
- Clean history + improving: 0-5
- Some risk factors: 5-15
- Significant risk: 15-35
- High risk + active violations: 35-65
- Imminent: 65-90

predicted_events: choose from [downtime, double_signing, oracle_manipulation, consensus_failure, sla_violation, performance_degradation, none]

OUTPUT: Return ONLY valid JSON, no markdown:
{{"failure_probability": <integer 0-100>, "slash_probability": <integer 0-100>, "instability_score": <integer 0-100>, "security_degradation": <integer 0-100>, "risk_trend": "<improving|stable|degrading>", "predicted_events": "<comma-separated event types or none>", "prediction_confidence": <integer 0-100>}}"""

        def run_prediction() -> str:
            result = gl.nondet.exec_prompt(prompt)
            return result.replace("```json", "").replace("```", "").strip()

        raw = gl.eq_principle.prompt_comparative(
            run_prediction,
            "failure_probability within 10, slash_probability within 10, instability_score within 10, security_degradation within 10, risk_trend must match exactly, prediction_confidence within 15"
        )

        try:
            data = json.loads(raw)
            fail_prob    = self._clamp(int(data.get("failure_probability", 20)), 0, 100)
            slash_prob   = self._clamp(int(data.get("slash_probability", 5)), 0, fail_prob)
            instability  = self._clamp(int(data.get("instability_score", 20)), 0, 100)
            sec_degrade  = self._clamp(int(data.get("security_degradation", 20)), 0, 100)
            risk_trend   = str(data.get("risk_trend", "stable"))
            pred_events  = str(data.get("predicted_events", "none"))
            pred_conf    = self._clamp(int(data.get("prediction_confidence", 50)), 0, 100)
        except Exception:
            fail_prob, slash_prob, instability, sec_degrade = 20, 5, 20, 20
            risk_trend, pred_events, pred_conf = "stable", "none", 40

        if risk_trend not in ["improving", "stable", "degrading"]:
            risk_trend = "stable"

        pred_data = {
            "operator": operator_address,
            "fail_prob": fail_prob,
            "slash_prob": slash_prob,
            "trend": risk_trend,
        }
        pred_hash = self._hash(pred_data)

        prediction = RiskPrediction(
            operator_address=operator_address,
            prediction_block=u256(int(gl.block.number)),
            failure_probability=u256(fail_prob),
            slash_probability=u256(slash_prob),
            instability_score=u256(instability),
            security_degradation=u256(sec_degrade),
            risk_trend=risk_trend,
            predicted_events_json=pred_events,
            prediction_confidence=u256(pred_conf),
            prediction_hash=pred_hash,
        )
        self.risk_predictions[operator_address] = prediction

        op.predicted_slash_prob = u256(slash_prob)
        op.last_updated = u256(int(gl.block.number))
        self.operators[operator_address] = op

        self._audit("risk_predicted", "llm", operator_address, pred_data)
        return {
            "operator_address": operator_address,
            "failure_probability": fail_prob,
            "slash_probability": slash_prob,
            "instability_score": instability,
            "security_degradation": sec_degrade,
            "risk_trend": risk_trend,
            "predicted_events": pred_events,
            "prediction_confidence": pred_conf,
            "prediction_hash": pred_hash,
        }

    @gl.public.view
    def get_risk_prediction(self, operator_address: str) -> dict:
        assert operator_address in self.risk_predictions, "No prediction found"
        p = self.risk_predictions[operator_address]
        return {
            "operator_address": p.operator_address,
            "prediction_block": int(p.prediction_block),
            "failure_probability": int(p.failure_probability),
            "slash_probability": int(p.slash_probability),
            "instability_score": int(p.instability_score),
            "security_degradation": int(p.security_degradation),
            "risk_trend": p.risk_trend,
            "predicted_events": p.predicted_events_json,
            "prediction_confidence": int(p.prediction_confidence),
            "prediction_hash": p.prediction_hash,
        }

    # ── Governance ────────────────────────────────────────────────────────────

    @gl.public.write
    def create_proposal(
        self,
        target_id: str,
        proposal_type: str,
        description_hash: str,
        voting_period_blocks: int,
    ) -> dict:
        self._not_paused()
        assert len(target_id) > 0, "target_id required"
        valid_types = ["appeal_slash", "review_claim", "update_params", "whitelist_operator"]
        assert proposal_type in valid_types, "Invalid proposal type"

        raw_id = f"proposal:{gl.message.sender_address.as_hex}:{target_id}:{int(gl.block.number)}"
        proposal_id = hashlib.sha256(raw_id.encode()).hexdigest()[:32]
        assert proposal_id not in self.governance_proposals, "Already exists"

        proposal = GovernanceProposal(
            proposal_id=proposal_id,
            proposal_type=proposal_type,
            target_id=target_id,
            proposer=gl.message.sender_address.as_hex,
            description_hash=description_hash,
            votes_for=u256(0),
            votes_against=u256(0),
            status="active",
            created_block=u256(int(gl.block.number)),
            deadline_block=u256(int(gl.block.number) + voting_period_blocks),
        )
        self.governance_proposals[proposal_id] = proposal
        self.proposal_voters[proposal_id] = ""
        self._audit("proposal_created", gl.message.sender_address.as_hex, proposal_id, {
            "type": proposal_type, "target": target_id
        })
        return {"proposal_id": proposal_id, "status": "active", "deadline_block": int(proposal.deadline_block)}

    @gl.public.write
    def vote(self, proposal_id: str, vote_for: bool) -> dict:
        self._not_paused()
        assert proposal_id in self.governance_proposals, "Not found"
        proposal = self.governance_proposals[proposal_id]
        assert proposal.status == "active", "Proposal not active"
        assert int(gl.block.number) <= int(proposal.deadline_block), "Voting closed"

        voter = gl.message.sender_address.as_hex
        existing_voters = self.proposal_voters.get(proposal_id, "")
        assert voter not in existing_voters.split(","), "Already voted"

        new_voters = existing_voters + ("," if existing_voters else "") + voter
        self.proposal_voters[proposal_id] = new_voters

        if vote_for:
            proposal.votes_for = u256(int(proposal.votes_for) + 1)
        else:
            proposal.votes_against = u256(int(proposal.votes_against) + 1)

        self.governance_proposals[proposal_id] = proposal
        self._audit("proposal_voted", voter, proposal_id, {"vote_for": vote_for})
        return {
            "proposal_id": proposal_id,
            "votes_for": int(proposal.votes_for),
            "votes_against": int(proposal.votes_against),
        }

    @gl.public.write
    def finalize_proposal(self, proposal_id: str) -> dict:
        self._not_paused()
        assert proposal_id in self.governance_proposals, "Not found"
        proposal = self.governance_proposals[proposal_id]
        assert proposal.status == "active", "Already finalized"
        assert int(gl.block.number) > int(proposal.deadline_block), "Voting still open"

        total = int(proposal.votes_for) + int(proposal.votes_against)
        if total == 0:
            proposal.status = "failed"
        elif int(proposal.votes_for) > int(proposal.votes_against):
            proposal.status = "passed"
        else:
            proposal.status = "failed"

        self.governance_proposals[proposal_id] = proposal
        self._audit("proposal_finalized", gl.message.sender_address.as_hex, proposal_id, {
            "result": proposal.status, "for": int(proposal.votes_for), "against": int(proposal.votes_against)
        })
        return {
            "proposal_id": proposal_id,
            "status": proposal.status,
            "votes_for": int(proposal.votes_for),
            "votes_against": int(proposal.votes_against),
        }

    @gl.public.view
    def get_proposal(self, proposal_id: str) -> dict:
        assert proposal_id in self.governance_proposals, "Not found"
        p = self.governance_proposals[proposal_id]
        return {
            "proposal_id": p.proposal_id,
            "proposal_type": p.proposal_type,
            "target_id": p.target_id,
            "proposer": p.proposer,
            "votes_for": int(p.votes_for),
            "votes_against": int(p.votes_against),
            "status": p.status,
            "created_block": int(p.created_block),
            "deadline_block": int(p.deadline_block),
        }

    # ── Admin ─────────────────────────────────────────────────────────────────

    @gl.public.write
    def pause(self) -> bool:
        self._only_owner()
        self.contract_paused = True
        self._audit("contract_paused", gl.message.sender_address.as_hex, "contract", {})
        return True

    @gl.public.write
    def unpause(self) -> bool:
        self._only_owner()
        self.contract_paused = False
        self._audit("contract_unpaused", gl.message.sender_address.as_hex, "contract", {})
        return True

    @gl.public.write
    def transfer_ownership(self, new_owner: str) -> bool:
        self._only_owner()
        assert len(new_owner) > 0, "new_owner required"
        old_owner = self.owner
        self.owner = new_owner
        self._audit("ownership_transferred", old_owner, "contract", {"new_owner": new_owner})
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
        assert 0 < min_confidence_slash <= 100, "Invalid"
        assert 0 < min_confidence_claim <= 100, "Invalid"
        assert appeal_window_blocks > 0, "Invalid"
        assert 0 < max_slash_bps <= 10000, "Invalid"
        self.min_confidence_slash = u256(min_confidence_slash)
        self.min_confidence_claim = u256(min_confidence_claim)
        self.appeal_window        = u256(appeal_window_blocks)
        self.max_slash_bps        = u256(max_slash_bps)
        self._audit("params_updated", gl.message.sender_address.as_hex, "contract", {
            "min_conf_slash": min_confidence_slash,
            "min_conf_claim": min_confidence_claim,
            "appeal_window": appeal_window_blocks,
        })
        return True

    # ── Views ─────────────────────────────────────────────────────────────────

    @gl.public.view
    def get_stats(self) -> dict:
        return {
            "owner": self.owner,
            "paused": self.contract_paused,
            "total_operators": int(self.total_operators),
            "total_incidents": int(self.total_incidents),
            "total_cases": int(self.total_cases),
            "total_claims": int(self.total_claims),
            "total_payouts_amount": int(self.total_payouts_amount),
            "audit_count": int(self.audit_count),
            "min_confidence_slash": int(self.min_confidence_slash),
            "min_confidence_claim": int(self.min_confidence_claim),
            "appeal_window_blocks": int(self.appeal_window),
            "max_slash_bps": int(self.max_slash_bps),
        }

    @gl.public.view
    def get_operator_incidents(self, operator_address: str) -> str:
        return self.operator_incidents.get(operator_address, "")

    @gl.public.view
    def get_operator_cases(self, operator_address: str) -> str:
        return self.operator_cases.get(operator_address, "")

    @gl.public.view
    def get_operator_claims(self, operator_address: str) -> str:
        return self.operator_claims.get(operator_address, "")

    @gl.public.view
    def get_audit_entry(self, index: int) -> str:
        key = u256(index)
        assert key in self.audit_trail, "Index out of range"
        return self.audit_trail[key]

    @gl.public.view
    def get_audit_count(self) -> int:
        return int(self.audit_count)

    @gl.public.view
    def is_operator_jailed(self, operator_address: str) -> bool:
        if operator_address not in self.operators:
            return False
        return self.operators[operator_address].status in ["jailed", "slashed", "suspended"]
