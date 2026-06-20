# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
from typing import Optional
import json
import hashlib


# ─── Constants ────────────────────────────────────────────────────────────────

CONTRACT_VERSION = "1.0.0"
NETWORK_GEN = "GEN"

# Slashing severity thresholds
SLASH_THRESHOLD_CRITICAL = 80   # >= 80 fault probability → critical slash
SLASH_THRESHOLD_HIGH = 60       # >= 60 → high severity
SLASH_THRESHOLD_MEDIUM = 40     # >= 40 → medium severity
SLASH_THRESHOLD_LOW = 20        # >= 20 → low severity

# Insurance adjudication thresholds
CLAIM_APPROVAL_CONFIDENCE_MIN = 55   # minimum AI confidence to approve
CLAIM_PARTIAL_THRESHOLD = 40         # below this → reject or partial

# Reputation score bounds
REPUTATION_MAX = 100
REPUTATION_MIN = 0
REPUTATION_DEGRADATION_PER_SLASH = 15
REPUTATION_RECOVERY_PER_CLEAN_PERIOD = 2

# Predictive risk
RISK_HIGH_THRESHOLD = 70
RISK_MEDIUM_THRESHOLD = 40

# Governance
APPEAL_WINDOW_BLOCKS = 7200  # ~24h at 12s/block

# Violation type codes
VIOLATION_DOWNTIME = "downtime"
VIOLATION_DOUBLE_SIGN = "double_signing"
VIOLATION_ORACLE_MANIP = "oracle_manipulation"
VIOLATION_CONSENSUS_FAIL = "consensus_failure"
VIOLATION_CENSORSHIP = "censorship"
VIOLATION_INCORRECT_AI = "incorrect_ai_output"
VIOLATION_SLA = "sla_violation"
VIOLATION_DATA_WITHHOLD = "data_withholding"
VIOLATION_COORDINATED = "coordinated_attack"
VIOLATION_OTHER = "other"

# Operator status codes
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
STATUS_JAILED = "jailed"
STATUS_SLASHED = "slashed"
STATUS_SUSPENDED = "suspended"

# Claim status codes
CLAIM_SUBMITTED = "submitted"
CLAIM_UNDER_REVIEW = "under_review"
CLAIM_APPROVED = "approved"
CLAIM_REJECTED = "rejected"
CLAIM_PARTIAL = "partial"
CLAIM_PAID = "paid"

# Review stage codes
STAGE_OPEN = "open"
STAGE_AI_ANALYSIS = "ai_analysis"
STAGE_RECOMMENDED = "recommended"
STAGE_APPROVED = "approved"
STAGE_REJECTED = "rejected"
STAGE_EXECUTED = "executed"
STAGE_APPEALED = "appealed"


# ─── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class OperatorRecord:
    address: str
    name: str
    network: str
    status: str
    total_stake: int          # in wei / smallest unit
    slash_count: int
    reputation_score: int     # 0-100
    reliability_score: int    # 0-100
    security_score: int       # 0-100
    slashing_risk_score: int  # 0-100 (higher = more risky)
    insurance_premium_score: int  # basis points multiplier
    predicted_slash_probability: int  # 0-100
    on_chain_reputation_hash: str
    registered_at: int        # block number
    last_updated: int         # block number
    is_whitelisted: bool
    metadata_hash: str        # hash of off-chain metadata


@dataclass
class EvidencePackage:
    incident_id: str
    operator_address: str
    violation_type: str
    network: str
    block_number: int
    merkle_root: str          # Merkle root of all evidence items
    evidence_count: int
    evidence_summary_hash: str
    submitted_by: str
    timestamp: int


@dataclass
class AIVerdict:
    incident_id: str
    fault_probability: int    # 0-100
    severity_score: int       # 0-100
    confidence_score: int     # 0-100
    recommended_action: str   # "slash_critical" | "slash_high" | "slash_medium" | "slash_low" | "dismiss" | "monitor"
    verdict_hash: str
    analysis_timestamp: int
    llm_model_hint: str


@dataclass
class SlashingRecord:
    case_id: str
    operator_address: str
    incident_id: str
    violation_type: str
    network: str
    stake_at_risk: int
    recommended_slash_percentage: int   # 0-100 (percent * 100 for precision, e.g. 500 = 5%)
    recommended_slash_amount: int
    executed_slash_amount: int
    fault_probability: int
    severity_score: int
    confidence_score: int
    stage: str
    on_chain_record_hash: str
    appeal_deadline_block: int
    created_at_block: int
    resolved_at_block: int


@dataclass
class InsuranceClaimRecord:
    claim_id: str
    organization: str
    incident_id: str
    claimant_address: str
    coverage_amount: int
    claimed_amount: int
    assessed_damage: int
    approved_amount: int
    status: str
    ai_coverage_eligible: bool
    ai_confidence_score: int
    ai_adjudication_hash: str
    on_chain_status_hash: str
    submitted_at_block: int
    adjudicated_at_block: int


@dataclass
class PayoutRecord:
    payout_id: str
    claim_id: str
    amount: int
    recipient_address: str
    token: str
    status: str
    approval_hash: str
    initiated_at_block: int
    completed_at_block: int


@dataclass
class GovernanceProposal:
    proposal_id: str
    proposal_type: str       # "appeal_slash" | "review_claim" | "update_params" | "whitelist_operator"
    target_id: str           # case_id or claim_id being reviewed
    proposer: str
    description_hash: str
    votes_for: int
    votes_against: int
    status: str              # "active" | "passed" | "failed" | "executed"
    created_at_block: int
    voting_deadline_block: int


@dataclass
class RiskPrediction:
    operator_address: str
    prediction_timestamp: int
    failure_probability: int       # 0-100
    slash_probability: int         # 0-100
    instability_score: int         # 0-100
    security_degradation_score: int  # 0-100
    risk_trend: str                # "improving" | "stable" | "degrading"
    predicted_risk_events: str     # JSON array of predicted event types
    prediction_confidence: int     # 0-100
    prediction_hash: str


# ─── Contract State ───────────────────────────────────────────────────────────

@gl.contract
class SlashSureContract:

    # Core registries
    operators: TreeMap[str, OperatorRecord]              # address → operator
    evidence_packages: TreeMap[str, EvidencePackage]     # incident_id → evidence
    ai_verdicts: TreeMap[str, AIVerdict]                 # incident_id → verdict
    slashing_cases: TreeMap[str, SlashingRecord]         # case_id → slashing record
    insurance_claims: TreeMap[str, InsuranceClaimRecord] # claim_id → claim
    payouts: TreeMap[str, PayoutRecord]                  # payout_id → payout
    governance_proposals: TreeMap[str, GovernanceProposal]  # proposal_id → proposal
    risk_predictions: TreeMap[str, RiskPrediction]       # operator_address → latest prediction

    # Audit trail
    audit_entries: DynArray[str]          # list of audit hashes for full trail
    operator_incident_index: TreeMap[str, DynArray[str]]  # operator_address → [incident_ids]
    operator_case_index: TreeMap[str, DynArray[str]]      # operator_address → [case_ids]
    operator_claim_index: TreeMap[str, DynArray[str]]     # operator_address → [claim_ids]

    # Governance votes
    proposal_votes: TreeMap[str, DynArray[str]]   # proposal_id → [voter_addresses]

    # Contract administration
    owner: str
    contract_paused: bool
    total_operators: int
    total_incidents: int
    total_slashing_cases: int
    total_insurance_claims: int
    total_payouts_amount: int
    contract_version: str

    # Configurable parameters (governable)
    min_confidence_for_auto_slash: int   # default 70
    min_confidence_for_auto_claim: int   # default 55
    appeal_window_blocks: int            # default 7200
    max_slash_percentage: int            # default 10000 (100.00%)
    min_stake_for_coverage: int          # default 0

    def __init__(self) -> None:
        self.owner = gl.message.sender_address
        self.contract_paused = False
        self.total_operators = 0
        self.total_incidents = 0
        self.total_slashing_cases = 0
        self.total_insurance_claims = 0
        self.total_payouts_amount = 0
        self.contract_version = CONTRACT_VERSION
        self.min_confidence_for_auto_slash = 70
        self.min_confidence_for_auto_claim = 55
        self.appeal_window_blocks = APPEAL_WINDOW_BLOCKS
        self.max_slash_percentage = 10000
        self.min_stake_for_coverage = 0

    # ─── Modifiers / Guards ───────────────────────────────────────────────────

    def _require_owner(self) -> None:
        assert gl.message.sender_address == self.owner, "Only contract owner"

    def _require_not_paused(self) -> None:
        assert not self.contract_paused, "Contract is paused"

    def _require_operator_exists(self, address: str) -> None:
        assert address in self.operators, f"Operator {address} not registered"

    def _make_case_id(self, operator: str, incident_id: str, block: int) -> str:
        raw = f"case:{operator}:{incident_id}:{block}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def _make_claim_id(self, claimant: str, incident_id: str, block: int) -> str:
        raw = f"claim:{claimant}:{incident_id}:{block}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def _make_payout_id(self, claim_id: str, block: int) -> str:
        raw = f"payout:{claim_id}:{block}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def _make_proposal_id(self, proposer: str, target_id: str, block: int) -> str:
        raw = f"proposal:{proposer}:{target_id}:{block}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def _hash_record(self, data: dict) -> str:
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def _add_audit(self, action: str, actor: str, resource_id: str, data: dict) -> str:
        entry = {
            "action": action,
            "actor": actor,
            "resource_id": resource_id,
            "block": gl.block.number,
            "data_hash": self._hash_record(data),
        }
        entry_hash = self._hash_record(entry)
        self.audit_entries.append(entry_hash)
        return entry_hash

    # ─── Operator Management ──────────────────────────────────────────────────

    @gl.public.write
    def register_operator(
        self,
        address: str,
        name: str,
        network: str,
        total_stake: int,
        metadata_hash: str,
    ) -> str:
        self._require_not_paused()
        assert address not in self.operators, "Operator already registered"
        assert len(name) > 0, "Name required"
        assert total_stake >= 0, "Stake must be non-negative"

        record = OperatorRecord(
            address=address,
            name=name,
            network=network,
            status=STATUS_ACTIVE,
            total_stake=total_stake,
            slash_count=0,
            reputation_score=100,
            reliability_score=100,
            security_score=100,
            slashing_risk_score=0,
            insurance_premium_score=100,
            predicted_slash_probability=0,
            on_chain_reputation_hash="",
            registered_at=gl.block.number,
            last_updated=gl.block.number,
            is_whitelisted=False,
            metadata_hash=metadata_hash,
        )
        self.operators[address] = record
        self.operator_incident_index[address] = DynArray[str]([])
        self.operator_case_index[address] = DynArray[str]([])
        self.operator_claim_index[address] = DynArray[str]([])
        self.total_operators += 1

        self._add_audit("operator_registered", gl.message.sender_address, address, {
            "name": name, "network": network, "stake": total_stake
        })
        return address

    @gl.public.write
    def update_operator_stake(self, address: str, new_stake: int) -> bool:
        self._require_not_paused()
        self._require_operator_exists(address)
        op = self.operators[address]
        op.total_stake = new_stake
        op.last_updated = gl.block.number
        self.operators[address] = op
        self._add_audit("operator_stake_updated", gl.message.sender_address, address, {
            "new_stake": new_stake
        })
        return True

    @gl.public.write
    def update_operator_status(self, address: str, status: str) -> bool:
        self._require_not_paused()
        self._require_owner()
        self._require_operator_exists(address)
        valid_statuses = [STATUS_ACTIVE, STATUS_INACTIVE, STATUS_JAILED, STATUS_SLASHED, STATUS_SUSPENDED]
        assert status in valid_statuses, f"Invalid status: {status}"
        op = self.operators[address]
        op.status = status
        op.last_updated = gl.block.number
        self.operators[address] = op
        self._add_audit("operator_status_updated", gl.message.sender_address, address, {
            "new_status": status
        })
        return True

    @gl.public.write
    def whitelist_operator(self, address: str) -> bool:
        self._require_owner()
        self._require_operator_exists(address)
        op = self.operators[address]
        op.is_whitelisted = True
        op.last_updated = gl.block.number
        self.operators[address] = op
        return True

    @gl.public.view
    def get_operator(self, address: str) -> OperatorRecord:
        self._require_operator_exists(address)
        return self.operators[address]

    @gl.public.view
    def get_operator_count(self) -> int:
        return self.total_operators

    # ─── Evidence Anchoring ───────────────────────────────────────────────────

    @gl.public.write
    def submit_evidence_package(
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
        self._require_not_paused()
        assert len(incident_id) > 0, "Incident ID required"
        assert len(merkle_root) > 0, "Merkle root required"
        assert evidence_count > 0, "Must have at least one evidence item"

        package = EvidencePackage(
            incident_id=incident_id,
            operator_address=operator_address,
            violation_type=violation_type,
            network=network,
            block_number=block_number,
            merkle_root=merkle_root,
            evidence_count=evidence_count,
            evidence_summary_hash=evidence_summary_hash,
            submitted_by=gl.message.sender_address,
            timestamp=gl.block.number,
        )
        self.evidence_packages[incident_id] = package
        self.total_incidents += 1

        if operator_address in self.operator_incident_index:
            self.operator_incident_index[operator_address].append(incident_id)

        self._add_audit("evidence_submitted", gl.message.sender_address, incident_id, {
            "operator": operator_address, "violation": violation_type, "merkle": merkle_root
        })
        return incident_id

    @gl.public.view
    def get_evidence_package(self, incident_id: str) -> EvidencePackage:
        assert incident_id in self.evidence_packages, "Evidence package not found"
        return self.evidence_packages[incident_id]

    # ─── AI Fault Analysis (Non-Deterministic LLM) ────────────────────────────

    @gl.public.write
    def analyze_fault(
        self,
        incident_id: str,
        operator_address: str,
        violation_type: str,
        network: str,
        evidence_summary: str,
        operator_history_summary: str,
        stake_amount: int,
        uptime_percentage: int,
        prior_slash_count: int,
        current_reputation: int,
    ) -> AIVerdict:
        """
        Non-deterministic: calls GenLayer LLM to analyze fault.
        Returns numeric scores (0-100) to ensure consensus via fuzzy eq_principle.
        Validators reach consensus by comparing scores within tolerance bands.
        """
        self._require_not_paused()

        prompt = f"""
You are an expert blockchain security analyst and slashing arbitrator for the SlashSure platform.

Analyze the following protocol violation and provide a structured fault assessment.

=== INCIDENT DATA ===
Incident ID: {incident_id}
Network: {network}
Violation Type: {violation_type}
Evidence Summary: {evidence_summary}

=== OPERATOR CONTEXT ===
Operator Address: {operator_address}
Current Reputation Score: {current_reputation}/100
Prior Slashing Count: {prior_slash_count}
Uptime Percentage: {uptime_percentage}%
Stake at Risk: {stake_amount} (smallest unit)
Operator History: {operator_history_summary}

=== VIOLATION SEVERITY GUIDE ===
- double_signing: Typically very high fault probability (75-95), critical severity
- coordinated_attack: Very high fault probability (80-95), critical severity
- oracle_manipulation: High fault probability (65-85), high severity
- downtime > 24h: Medium-high fault probability (50-75), medium-high severity
- downtime < 6h: Low fault probability (10-35), low severity
- sla_violation: Moderate fault probability (40-65), medium severity
- data_withholding: Moderate-high fault probability (55-80), high severity
- incorrect_ai_output: Depends on frequency (30-75), medium severity
- consensus_failure: High fault probability (60-85), high severity
- censorship: High fault probability (65-90), high severity

=== ASSESSMENT INSTRUCTIONS ===
Provide a JSON object with EXACTLY these fields and ONLY integer values for scores:

{{
  "fault_probability": <integer 0-100>,
  "severity_score": <integer 0-100>,
  "confidence_score": <integer 0-100>,
  "recommended_action": "<one of: slash_critical|slash_high|slash_medium|slash_low|dismiss|monitor>",
  "reasoning_summary": "<2-3 sentence explanation>"
}}

Rules:
- fault_probability: probability (0-100) that the operator is at fault
- severity_score: severity of the violation (0-100)
- confidence_score: your confidence in this assessment (0-100)
- recommended_action must be exactly one of the listed options
- For dismiss: fault_probability < 25
- For monitor: fault_probability 25-39
- For slash_low: fault_probability 40-54 OR severity < 40
- For slash_medium: fault_probability 55-69 AND severity 40-69
- For slash_high: fault_probability 70-84 OR severity 70-84
- For slash_critical: fault_probability >= 85 OR severity >= 85

Return ONLY the JSON object, no other text.
"""

        result = gl.get_webpage(
            "https://api.genlayer.com/llm",
            task=prompt,
            eq_principle=(
                "The JSON response is equivalent if: "
                "fault_probability values are within 8 of each other, "
                "severity_score values are within 8 of each other, "
                "confidence_score values are within 10 of each other, "
                "and recommended_action is the same string. "
                "Minor differences in reasoning_summary text are acceptable."
            ),
        )

        try:
            parsed = json.loads(result.strip())
        except Exception:
            # Fallback: extract numbers from result if JSON parsing fails
            parsed = {
                "fault_probability": 50,
                "severity_score": 50,
                "confidence_score": 40,
                "recommended_action": "monitor",
                "reasoning_summary": "Automated fallback assessment due to parsing error.",
            }

        fault_probability = max(0, min(100, int(parsed.get("fault_probability", 50))))
        severity_score = max(0, min(100, int(parsed.get("severity_score", 50))))
        confidence_score = max(0, min(100, int(parsed.get("confidence_score", 40))))
        recommended_action = str(parsed.get("recommended_action", "monitor"))

        valid_actions = ["slash_critical", "slash_high", "slash_medium", "slash_low", "dismiss", "monitor"]
        if recommended_action not in valid_actions:
            recommended_action = "monitor"

        verdict_data = {
            "incident_id": incident_id,
            "fault_probability": fault_probability,
            "severity_score": severity_score,
            "confidence_score": confidence_score,
            "recommended_action": recommended_action,
        }
        verdict_hash = self._hash_record(verdict_data)

        verdict = AIVerdict(
            incident_id=incident_id,
            fault_probability=fault_probability,
            severity_score=severity_score,
            confidence_score=confidence_score,
            recommended_action=recommended_action,
            verdict_hash=verdict_hash,
            analysis_timestamp=gl.block.number,
            llm_model_hint="genlayer-llm",
        )
        self.ai_verdicts[incident_id] = verdict

        self._add_audit("ai_fault_analysis", "llm", incident_id, verdict_data)
        return verdict

    @gl.public.view
    def get_ai_verdict(self, incident_id: str) -> AIVerdict:
        assert incident_id in self.ai_verdicts, "No AI verdict found for this incident"
        return self.ai_verdicts[incident_id]

    # ─── Slashing Recommendation ──────────────────────────────────────────────

    @gl.public.write
    def create_slashing_case(
        self,
        case_id: str,
        operator_address: str,
        incident_id: str,
        violation_type: str,
        network: str,
        stake_at_risk: int,
    ) -> SlashingRecord:
        self._require_not_paused()
        self._require_operator_exists(operator_address)
        assert case_id not in self.slashing_cases, "Case already exists"
        assert incident_id in self.ai_verdicts, "Must run AI analysis before creating case"

        verdict = self.ai_verdicts[incident_id]

        record = SlashingRecord(
            case_id=case_id,
            operator_address=operator_address,
            incident_id=incident_id,
            violation_type=violation_type,
            network=network,
            stake_at_risk=stake_at_risk,
            recommended_slash_percentage=0,
            recommended_slash_amount=0,
            executed_slash_amount=0,
            fault_probability=verdict.fault_probability,
            severity_score=verdict.severity_score,
            confidence_score=verdict.confidence_score,
            stage=STAGE_AI_ANALYSIS,
            on_chain_record_hash="",
            appeal_deadline_block=0,
            created_at_block=gl.block.number,
            resolved_at_block=0,
        )
        self.slashing_cases[case_id] = record
        self.total_slashing_cases += 1

        if operator_address in self.operator_case_index:
            self.operator_case_index[operator_address].append(case_id)

        self._add_audit("slashing_case_created", gl.message.sender_address, case_id, {
            "operator": operator_address, "incident": incident_id, "stake": stake_at_risk
        })
        return record

    @gl.public.write
    def generate_slashing_recommendation(
        self,
        case_id: str,
        operator_address: str,
        evidence_summary: str,
        operator_history: str,
        network_policy: str,
        stake_at_risk: int,
        current_reputation: int,
    ) -> SlashingRecord:
        """
        Non-deterministic: calls GenLayer LLM to compute precise slash percentage and rationale.
        Uses numeric outputs with fuzzy tolerance for consensus.
        """
        self._require_not_paused()
        assert case_id in self.slashing_cases, "Slashing case not found"
        case = self.slashing_cases[case_id]
        assert case_id in self.slashing_cases, "Case not found"

        prompt = f"""
You are a senior slashing arbitrator for the SlashSure decentralized security platform.

Your task is to determine the precise slashing recommendation for the following case.

=== CASE DATA ===
Case ID: {case_id}
Operator: {operator_address}
Network: {network_policy}
AI Fault Probability: {case.fault_probability}/100
AI Severity Score: {case.severity_score}/100
AI Confidence Score: {case.confidence_score}/100
Stake at Risk: {stake_at_risk} units
Current Reputation Score: {current_reputation}/100

=== EVIDENCE SUMMARY ===
{evidence_summary}

=== OPERATOR HISTORY ===
{operator_history}

=== NETWORK SLASHING POLICY ===
{network_policy}

=== SLASHING PERCENTAGE GUIDELINES ===
- Minimum slash: 0.5% (50 basis points) for confirmed minor violations
- Low severity confirmed: 1-3% (100-300 basis points)
- Medium severity confirmed: 3-7% (300-700 basis points)
- High severity confirmed: 7-15% (700-1500 basis points)
- Critical confirmed: 15-100% (1500-10000 basis points)
- Repeat offenders: multiply base by 1.5x
- First-time with high reputation: reduce base by 25%
- Unconfirmed (confidence < 60): reduce by 50% or dismiss

=== OUTPUT INSTRUCTIONS ===
Return ONLY a JSON object with these fields:

{{
  "slash_percentage_bps": <integer 0-10000>,
  "slash_amount": <integer, calculated from stake>,
  "rationale": "<3-5 sentence detailed rationale>",
  "confidence": <integer 0-100>,
  "is_first_offense": <true|false>,
  "mitigating_factors": "<comma-separated list or 'none'>",
  "aggravating_factors": "<comma-separated list or 'none'>"
}}

Where slash_percentage_bps is in basis points (100 = 1.00%, 1000 = 10.00%, 10000 = 100.00%).
slash_amount = (slash_percentage_bps * stake_at_risk) / 10000, rounded to integer.
Return ONLY the JSON object.
"""

        result = gl.get_webpage(
            "https://api.genlayer.com/llm",
            task=prompt,
            eq_principle=(
                "Two slashing recommendations are equivalent if: "
                "slash_percentage_bps values are within 50 basis points (0.5%) of each other, "
                "slash_amount values are within 1% of each other (proportional tolerance), "
                "and confidence values are within 10 of each other. "
                "The rationale text may differ in wording as long as the numerical outcome is equivalent."
            ),
        )

        try:
            parsed = json.loads(result.strip())
            slash_bps = max(0, min(self.max_slash_percentage, int(parsed.get("slash_percentage_bps", 0))))
            slash_amount = max(0, int((slash_bps * stake_at_risk) / 10000))
            confidence = max(0, min(100, int(parsed.get("confidence", 50))))
        except Exception:
            slash_bps = max(0, int(case.severity_score * 50))
            slash_amount = int((slash_bps * stake_at_risk) / 10000)
            confidence = 40

        case.recommended_slash_percentage = slash_bps
        case.recommended_slash_amount = slash_amount
        case.confidence_score = confidence
        case.stage = STAGE_RECOMMENDED

        record_data = {
            "case_id": case_id,
            "slash_bps": slash_bps,
            "slash_amount": slash_amount,
        }
        case.on_chain_record_hash = self._hash_record(record_data)
        self.slashing_cases[case_id] = case

        self._add_audit("slashing_recommended", "llm", case_id, record_data)
        return case

    @gl.public.write
    def approve_slashing(self, case_id: str) -> SlashingRecord:
        self._require_not_paused()
        self._require_owner()
        assert case_id in self.slashing_cases, "Case not found"
        case = self.slashing_cases[case_id]
        assert case.stage == STAGE_RECOMMENDED, "Case must be in RECOMMENDED stage"

        case.stage = STAGE_APPROVED
        case.appeal_deadline_block = gl.block.number + self.appeal_window_blocks
        self.slashing_cases[case_id] = case

        # Update operator status
        if case.operator_address in self.operators:
            op = self.operators[case.operator_address]
            op.status = STATUS_JAILED
            op.last_updated = gl.block.number
            self.operators[case.operator_address] = op

        self._add_audit("slashing_approved", gl.message.sender_address, case_id, {
            "slash_amount": case.recommended_slash_amount
        })
        return case

    @gl.public.write
    def reject_slashing(self, case_id: str, reason: str) -> SlashingRecord:
        self._require_not_paused()
        self._require_owner()
        assert case_id in self.slashing_cases, "Case not found"
        case = self.slashing_cases[case_id]
        assert case.stage in [STAGE_RECOMMENDED, STAGE_AI_ANALYSIS], "Cannot reject in this stage"

        case.stage = STAGE_REJECTED
        case.resolved_at_block = gl.block.number
        self.slashing_cases[case_id] = case

        self._add_audit("slashing_rejected", gl.message.sender_address, case_id, {"reason": reason})
        return case

    @gl.public.write
    def execute_slashing(self, case_id: str, actual_slash_amount: int) -> SlashingRecord:
        self._require_not_paused()
        self._require_owner()
        assert case_id in self.slashing_cases, "Case not found"
        case = self.slashing_cases[case_id]
        assert case.stage == STAGE_APPROVED, "Case must be approved"
        assert gl.block.number >= case.appeal_deadline_block or case.appeal_deadline_block == 0, \
            "Appeal window still open"

        case.executed_slash_amount = actual_slash_amount
        case.stage = STAGE_EXECUTED
        case.resolved_at_block = gl.block.number
        self.slashing_cases[case_id] = case

        # Update operator record
        if case.operator_address in self.operators:
            op = self.operators[case.operator_address]
            op.status = STATUS_SLASHED
            op.slash_count += 1
            op.total_stake = max(0, op.total_stake - actual_slash_amount)
            op.last_updated = gl.block.number
            # Degrade reputation
            penalty = REPUTATION_DEGRADATION_PER_SLASH + (op.slash_count * 5)
            op.reputation_score = max(REPUTATION_MIN, op.reputation_score - penalty)
            self.operators[case.operator_address] = op

        self._add_audit("slashing_executed", gl.message.sender_address, case_id, {
            "actual_slash_amount": actual_slash_amount
        })
        return case

    @gl.public.view
    def get_slashing_case(self, case_id: str) -> SlashingRecord:
        assert case_id in self.slashing_cases, "Case not found"
        return self.slashing_cases[case_id]

    # ─── Insurance Adjudication (Non-Deterministic LLM) ──────────────────────

    @gl.public.write
    def submit_insurance_claim(
        self,
        claim_id: str,
        organization: str,
        incident_id: str,
        claimant_address: str,
        coverage_amount: int,
        claimed_amount: int,
    ) -> InsuranceClaimRecord:
        self._require_not_paused()
        assert claim_id not in self.insurance_claims, "Claim already submitted"
        assert claimed_amount <= coverage_amount, "Claimed amount exceeds coverage"
        assert claimed_amount > 0, "Claimed amount must be positive"

        claim = InsuranceClaimRecord(
            claim_id=claim_id,
            organization=organization,
            incident_id=incident_id,
            claimant_address=claimant_address,
            coverage_amount=coverage_amount,
            claimed_amount=claimed_amount,
            assessed_damage=0,
            approved_amount=0,
            status=CLAIM_SUBMITTED,
            ai_coverage_eligible=False,
            ai_confidence_score=0,
            ai_adjudication_hash="",
            on_chain_status_hash="",
            submitted_at_block=gl.block.number,
            adjudicated_at_block=0,
        )
        self.insurance_claims[claim_id] = claim
        self.total_insurance_claims += 1

        if claimant_address in self.operator_claim_index:
            self.operator_claim_index[claimant_address].append(claim_id)

        self._add_audit("claim_submitted", gl.message.sender_address, claim_id, {
            "claimed": claimed_amount, "coverage": coverage_amount
        })
        return claim

    @gl.public.write
    def adjudicate_insurance_claim(
        self,
        claim_id: str,
        incident_summary: str,
        policy_terms: str,
        damage_evidence: str,
        operator_negligence_score: int,
        network_conditions: str,
        claimant_history: str,
        coverage_amount: int,
        claimed_amount: int,
    ) -> InsuranceClaimRecord:
        """
        Non-deterministic: AI adjudicates the insurance claim via GenLayer LLM.
        Returns structured numeric assessment with fuzzy consensus.
        """
        self._require_not_paused()
        assert claim_id in self.insurance_claims, "Claim not found"

        prompt = f"""
You are a senior insurance adjudicator specializing in decentralized network and validator insurance for the SlashSure platform.

Adjudicate the following insurance claim with precision, fairness, and alignment to policy terms.

=== CLAIM INFORMATION ===
Claim ID: {claim_id}
Coverage Amount: {coverage_amount} GEN tokens
Claimed Amount: {claimed_amount} GEN tokens

=== INCIDENT SUMMARY ===
{incident_summary}

=== POLICY TERMS ===
{policy_terms}

=== DAMAGE EVIDENCE ===
{damage_evidence}

=== CONTEXTUAL FACTORS ===
Operator Negligence Score: {operator_negligence_score}/100 (higher = more negligent)
Network Conditions: {network_conditions}
Claimant History: {claimant_history}

=== ADJUDICATION GUIDELINES ===
- Coverage eligible if: incident matches policy terms AND damage is documented AND not excluded
- Common exclusions: force majeure, acts of war, protocol bugs (not operator fault), unregistered operators
- Partial coverage: when damage is partially attributable to factors outside policy scope
- Damage assessment: use on-chain evidence and market rates for token valuation
- Operator negligence score > 70: full coverage likely eligible
- Operator negligence score 40-70: partial coverage likely (50-80% of claimed)
- Operator negligence score < 40: coverage may not be eligible unless other factors apply
- Reduce payout by 10-30% if claimant had prior fraudulent claims

=== OUTPUT INSTRUCTIONS ===
Return ONLY a JSON object with these exact fields:

{{
  "coverage_eligible": <true|false>,
  "assessed_damage": <integer, your assessment of actual damage in token units>,
  "approved_amount": <integer, amount to approve for payout>,
  "confidence_score": <integer 0-100>,
  "claim_status": "<approved|rejected|partial>",
  "adjudication_rationale": "<3-5 sentence detailed rationale>",
  "coverage_percentage": <integer 0-100>,
  "exclusions_applied": "<comma-separated exclusions or 'none'>",
  "fraud_indicators": "<comma-separated indicators or 'none'>"
}}

Ensure: approved_amount <= assessed_damage <= claimed_amount <= coverage_amount.
Return ONLY the JSON object.
"""

        result = gl.get_webpage(
            "https://api.genlayer.com/llm",
            task=prompt,
            eq_principle=(
                "Two insurance adjudications are equivalent if: "
                "coverage_eligible boolean is identical, "
                "approved_amount values are within 2% of each other (proportional tolerance), "
                "assessed_damage values are within 5% of each other, "
                "confidence_score values are within 10 of each other, "
                "and claim_status string is identical. "
                "Rationale text may differ as long as numerical outcomes match."
            ),
        )

        try:
            parsed = json.loads(result.strip())
            coverage_eligible = bool(parsed.get("coverage_eligible", False))
            assessed_damage = max(0, min(claimed_amount, int(parsed.get("assessed_damage", 0))))
            approved_amount = max(0, min(assessed_damage, int(parsed.get("approved_amount", 0))))
            confidence_score = max(0, min(100, int(parsed.get("confidence_score", 50))))
            claim_status_str = str(parsed.get("claim_status", "rejected"))
        except Exception:
            coverage_eligible = False
            assessed_damage = 0
            approved_amount = 0
            confidence_score = 30
            claim_status_str = "rejected"

        valid_statuses = [CLAIM_APPROVED, CLAIM_REJECTED, CLAIM_PARTIAL]
        if claim_status_str not in valid_statuses:
            claim_status_str = CLAIM_REJECTED

        adjudication_data = {
            "claim_id": claim_id,
            "coverage_eligible": coverage_eligible,
            "approved_amount": approved_amount,
            "confidence_score": confidence_score,
        }
        adj_hash = self._hash_record(adjudication_data)

        claim = self.insurance_claims[claim_id]
        claim.ai_coverage_eligible = coverage_eligible
        claim.assessed_damage = assessed_damage
        claim.approved_amount = approved_amount
        claim.ai_confidence_score = confidence_score
        claim.ai_adjudication_hash = adj_hash
        claim.status = claim_status_str
        claim.adjudicated_at_block = gl.block.number
        claim.on_chain_status_hash = self._hash_record({
            "claim_id": claim_id, "status": claim_status_str, "amount": approved_amount
        })
        self.insurance_claims[claim_id] = claim
        self.total_insurance_claims += 0  # counter already incremented on submission

        self._add_audit("claim_adjudicated", "llm", claim_id, adjudication_data)
        return claim

    @gl.public.write
    def authorize_payout(
        self,
        claim_id: str,
        payout_id: str,
        amount: int,
        recipient_address: str,
    ) -> PayoutRecord:
        self._require_not_paused()
        self._require_owner()
        assert claim_id in self.insurance_claims, "Claim not found"
        assert payout_id not in self.payouts, "Payout already exists"

        claim = self.insurance_claims[claim_id]
        assert claim.status in [CLAIM_APPROVED, CLAIM_PARTIAL], "Claim must be approved"
        assert amount <= claim.approved_amount, "Payout exceeds approved amount"
        assert amount > 0, "Payout amount must be positive"

        approval_data = {
            "claim_id": claim_id,
            "payout_id": payout_id,
            "amount": amount,
            "recipient": recipient_address,
            "block": gl.block.number,
        }
        approval_hash = self._hash_record(approval_data)

        payout = PayoutRecord(
            payout_id=payout_id,
            claim_id=claim_id,
            amount=amount,
            recipient_address=recipient_address,
            token=NETWORK_GEN,
            status="authorized",
            approval_hash=approval_hash,
            initiated_at_block=gl.block.number,
            completed_at_block=0,
        )
        self.payouts[payout_id] = payout
        self.total_payouts_amount += amount

        # Update claim status
        claim.status = CLAIM_PAID
        self.insurance_claims[claim_id] = claim

        self._add_audit("payout_authorized", gl.message.sender_address, payout_id, {
            "amount": amount, "recipient": recipient_address
        })
        return payout

    @gl.public.write
    def mark_payout_completed(self, payout_id: str, tx_hash: str) -> PayoutRecord:
        self._require_owner()
        assert payout_id in self.payouts, "Payout not found"
        payout = self.payouts[payout_id]
        payout.status = "completed"
        payout.completed_at_block = gl.block.number
        self.payouts[payout_id] = payout
        self._add_audit("payout_completed", gl.message.sender_address, payout_id, {"tx_hash": tx_hash})
        return payout

    @gl.public.view
    def get_insurance_claim(self, claim_id: str) -> InsuranceClaimRecord:
        assert claim_id in self.insurance_claims, "Claim not found"
        return self.insurance_claims[claim_id]

    @gl.public.view
    def get_payout(self, payout_id: str) -> PayoutRecord:
        assert payout_id in self.payouts, "Payout not found"
        return self.payouts[payout_id]

    # ─── Reputation Scoring (Non-Deterministic LLM) ───────────────────────────

    @gl.public.write
    def compute_reputation_score(
        self,
        operator_address: str,
        uptime_30d: int,
        uptime_90d: int,
        slash_count_total: int,
        slash_count_90d: int,
        incident_count_90d: int,
        missed_blocks_30d: int,
        total_blocks_30d: int,
        oracle_accuracy_score: int,
        peer_review_score: int,
        stake_stability_score: int,
        network: str,
    ) -> OperatorRecord:
        """
        Non-deterministic: LLM computes a comprehensive reputation score.
        All outputs are 0-100 integers for fuzzy consensus.
        """
        self._require_not_paused()
        self._require_operator_exists(operator_address)

        missed_pct = 0 if total_blocks_30d == 0 else int((missed_blocks_30d * 100) / total_blocks_30d)

        prompt = f"""
You are a decentralized network reputation scoring engine for SlashSure.

Compute comprehensive reputation scores for a validator/operator.

=== OPERATOR METRICS ===
Operator: {operator_address}
Network: {network}
Uptime (30d): {uptime_30d}%
Uptime (90d): {uptime_90d}%
Missed Blocks (30d): {missed_blocks_30d} out of {total_blocks_30d} ({missed_pct}%)
Total Slash Count (all time): {slash_count_total}
Slash Count (90d): {slash_count_90d}
Incidents (90d): {incident_count_90d}
Oracle Accuracy Score: {oracle_accuracy_score}/100
Peer Review Score: {peer_review_score}/100
Stake Stability Score: {stake_stability_score}/100

=== SCORING GUIDELINES ===

Reliability Score (0-100):
- Start at 100, deduct based on downtime and missed blocks
- 99%+ uptime, <0.1% missed: 95-100
- 97-99% uptime: 80-94
- 95-97% uptime: 65-79
- <95% uptime: 40-64
- <90% uptime: 0-39

Security Score (0-100):
- Start at 100, deduct for security incidents
- No incidents, no slashes: 90-100
- 1-2 minor incidents: 70-89
- 1 slash event: 50-69
- 2+ slash events: 20-49
- Critical breach: 0-19

Slashing Risk Score (0-100, higher = MORE risky):
- Based on slash history, incident trend, and behavior patterns
- 0 slashes, clean history: 0-10
- 1 minor slash: 20-35
- 1 major slash: 40-60
- 2+ slashes or recent incidents: 65-85
- Active violations or jailed: 85-100

Insurance Premium Score (0-100, 100 = standard rate, >100 = surcharge):
- Based on risk profile
- Excellent operator: 70-85 (discount)
- Good operator: 86-100 (standard)
- Moderate risk: 101-130 (surcharge)
- High risk: 131-175 (high surcharge)
Note: cap at 100 for this field since we use integer 0-100 scale, where 100 = highest premium multiplier.

Overall Score (0-100):
- Weighted average: reliability (35%) + security (35%) + (100 - slashing_risk) (20%) + peer_review (10%)

=== OUTPUT INSTRUCTIONS ===
Return ONLY a JSON object:

{{
  "reliability_score": <integer 0-100>,
  "security_score": <integer 0-100>,
  "slashing_risk_score": <integer 0-100>,
  "insurance_premium_score": <integer 0-100>,
  "overall_score": <integer 0-100>,
  "risk_trend": "<improving|stable|degrading>",
  "score_rationale": "<2-3 sentence summary>"
}}

Return ONLY the JSON object.
"""

        result = gl.get_webpage(
            "https://api.genlayer.com/llm",
            task=prompt,
            eq_principle=(
                "Two reputation assessments are equivalent if: "
                "all numeric score fields are within 5 of each other, "
                "risk_trend string is identical. "
                "Rationale text differences are acceptable."
            ),
        )

        try:
            parsed = json.loads(result.strip())
            reliability = max(0, min(100, int(parsed.get("reliability_score", 80))))
            security = max(0, min(100, int(parsed.get("security_score", 80))))
            slashing_risk = max(0, min(100, int(parsed.get("slashing_risk_score", 20))))
            insurance_premium = max(0, min(100, int(parsed.get("insurance_premium_score", 80))))
            overall = max(0, min(100, int(parsed.get("overall_score", 80))))
            risk_trend = str(parsed.get("risk_trend", "stable"))
        except Exception:
            reliability = 75
            security = 75
            slashing_risk = 25
            insurance_premium = 80
            overall = 75
            risk_trend = "stable"

        valid_trends = ["improving", "stable", "degrading"]
        if risk_trend not in valid_trends:
            risk_trend = "stable"

        score_data = {
            "operator": operator_address,
            "reliability": reliability,
            "security": security,
            "slashing_risk": slashing_risk,
            "overall": overall,
        }
        score_hash = self._hash_record(score_data)

        op = self.operators[operator_address]
        op.reliability_score = reliability
        op.security_score = security
        op.slashing_risk_score = slashing_risk
        op.insurance_premium_score = insurance_premium
        op.reputation_score = overall
        op.on_chain_reputation_hash = score_hash
        op.last_updated = gl.block.number
        self.operators[operator_address] = op

        self._add_audit("reputation_computed", "llm", operator_address, score_data)
        return op

    # ─── Predictive Risk Engine (Non-Deterministic LLM) ──────────────────────

    @gl.public.write
    def predict_operator_risk(
        self,
        operator_address: str,
        recent_performance_trend: str,
        infrastructure_alerts: str,
        peer_comparison: str,
        market_conditions: str,
        historical_patterns: str,
        days_since_last_incident: int,
        stake_growth_rate: int,
        delegator_change_rate: int,
    ) -> RiskPrediction:
        """
        Non-deterministic: GenLayer LLM predicts future risk events.
        Returns probability scores (0-100) for fuzzy consensus.
        """
        self._require_not_paused()
        self._require_operator_exists(operator_address)
        op = self.operators[operator_address]

        prompt = f"""
You are a predictive risk analyst for SlashSure, specialized in forecasting validator and operator failures in decentralized networks.

Analyze current and historical data to predict future risk for the following operator.

=== OPERATOR CURRENT STATE ===
Address: {operator_address}
Current Reputation Score: {op.reputation_score}/100
Current Reliability Score: {op.reliability_score}/100
Current Security Score: {op.security_score}/100
Current Slashing Risk Score: {op.slashing_risk_score}/100
Total Slash Count: {op.slash_count}
Operator Status: {op.status}

=== TREND DATA ===
Recent Performance Trend: {recent_performance_trend}
Infrastructure Alerts (last 30d): {infrastructure_alerts}
Peer Comparison: {peer_comparison}
Market Conditions: {market_conditions}
Historical Patterns: {historical_patterns}
Days Since Last Incident: {days_since_last_incident}
Stake Growth Rate (monthly %): {stake_growth_rate}
Delegator Change Rate (monthly %): {delegator_change_rate}

=== PREDICTION GUIDELINES ===

Failure Probability (probability of any failure in next 30d):
- Excellent trend, no alerts, good peers: 0-10%
- Minor degradation: 10-25%
- Concerning alerts or deteriorating trend: 25-50%
- Multiple red flags: 50-75%
- Imminent failure indicators: 75-95%

Slash Probability (probability of slashable event in next 30d):
- Always lower than or equal to failure probability
- Clean history, improving trend: 0-5%
- Some risk factors: 5-15%
- Significant risk factors: 15-35%
- High risk, active violations: 35-65%
- Imminent slash risk: 65-90%

Instability Score (0-100, current level of instability):
- Based on variance in performance, alerts, peer comparison

Security Degradation Score (0-100, trend of security health):
- Higher score = more degradation occurring

=== OUTPUT INSTRUCTIONS ===
Return ONLY a JSON object:

{{
  "failure_probability": <integer 0-100>,
  "slash_probability": <integer 0-100>,
  "instability_score": <integer 0-100>,
  "security_degradation_score": <integer 0-100>,
  "risk_trend": "<improving|stable|degrading>",
  "predicted_risk_events": ["<event_type_1>", "<event_type_2>"],
  "prediction_confidence": <integer 0-100>,
  "key_risk_factors": "<comma-separated list of top 3 risk factors>",
  "recommended_actions": "<comma-separated list of recommended mitigations>"
}}

predicted_risk_events must be from: ["downtime", "double_signing", "oracle_manipulation", "consensus_failure", "sla_violation", "performance_degradation", "none"]
Return ONLY the JSON object.
"""

        result = gl.get_webpage(
            "https://api.genlayer.com/llm",
            task=prompt,
            eq_principle=(
                "Two risk predictions are equivalent if: "
                "failure_probability values are within 10 of each other, "
                "slash_probability values are within 10 of each other, "
                "instability_score values are within 10 of each other, "
                "security_degradation_score values are within 10 of each other, "
                "risk_trend strings are identical, "
                "and prediction_confidence values are within 15 of each other."
            ),
        )

        try:
            parsed = json.loads(result.strip())
            failure_prob = max(0, min(100, int(parsed.get("failure_probability", 20))))
            slash_prob = max(0, min(failure_prob, int(parsed.get("slash_probability", 5))))
            instability = max(0, min(100, int(parsed.get("instability_score", 20))))
            security_deg = max(0, min(100, int(parsed.get("security_degradation_score", 20))))
            risk_trend = str(parsed.get("risk_trend", "stable"))
            pred_confidence = max(0, min(100, int(parsed.get("prediction_confidence", 50))))
            pred_events = parsed.get("predicted_risk_events", ["none"])
            if not isinstance(pred_events, list):
                pred_events = ["none"]
            predicted_events_str = json.dumps(pred_events)
        except Exception:
            failure_prob = 20
            slash_prob = 5
            instability = 20
            security_deg = 20
            risk_trend = "stable"
            pred_confidence = 40
            predicted_events_str = '["none"]'

        valid_trends = ["improving", "stable", "degrading"]
        if risk_trend not in valid_trends:
            risk_trend = "stable"

        prediction_data = {
            "operator": operator_address,
            "failure_prob": failure_prob,
            "slash_prob": slash_prob,
            "trend": risk_trend,
        }
        pred_hash = self._hash_record(prediction_data)

        prediction = RiskPrediction(
            operator_address=operator_address,
            prediction_timestamp=gl.block.number,
            failure_probability=failure_prob,
            slash_probability=slash_prob,
            instability_score=instability,
            security_degradation_score=security_deg,
            risk_trend=risk_trend,
            predicted_risk_events=predicted_events_str,
            prediction_confidence=pred_confidence,
            prediction_hash=pred_hash,
        )
        self.risk_predictions[operator_address] = prediction

        # Update operator's predicted risk
        op.predicted_slash_probability = slash_prob
        op.last_updated = gl.block.number
        self.operators[operator_address] = op

        self._add_audit("risk_predicted", "llm", operator_address, prediction_data)
        return prediction

    @gl.public.view
    def get_risk_prediction(self, operator_address: str) -> RiskPrediction:
        assert operator_address in self.risk_predictions, "No prediction found"
        return self.risk_predictions[operator_address]

    # ─── Governance ───────────────────────────────────────────────────────────

    @gl.public.write
    def create_governance_proposal(
        self,
        target_id: str,
        proposal_type: str,
        description_hash: str,
        voting_period_blocks: int,
    ) -> GovernanceProposal:
        self._require_not_paused()
        assert len(target_id) > 0, "Target ID required"
        valid_types = ["appeal_slash", "review_claim", "update_params", "whitelist_operator"]
        assert proposal_type in valid_types, f"Invalid proposal type: {proposal_type}"

        proposal_id = self._make_proposal_id(
            gl.message.sender_address, target_id, gl.block.number
        )
        assert proposal_id not in self.governance_proposals, "Proposal already exists"

        proposal = GovernanceProposal(
            proposal_id=proposal_id,
            proposal_type=proposal_type,
            target_id=target_id,
            proposer=gl.message.sender_address,
            description_hash=description_hash,
            votes_for=0,
            votes_against=0,
            status="active",
            created_at_block=gl.block.number,
            voting_deadline_block=gl.block.number + voting_period_blocks,
        )
        self.governance_proposals[proposal_id] = proposal
        self.proposal_votes[proposal_id] = DynArray[str]([])

        self._add_audit("proposal_created", gl.message.sender_address, proposal_id, {
            "type": proposal_type, "target": target_id
        })
        return proposal

    @gl.public.write
    def vote_on_proposal(self, proposal_id: str, vote_for: bool) -> GovernanceProposal:
        self._require_not_paused()
        assert proposal_id in self.governance_proposals, "Proposal not found"
        proposal = self.governance_proposals[proposal_id]
        assert proposal.status == "active", "Proposal is not active"
        assert gl.block.number <= proposal.voting_deadline_block, "Voting period ended"

        voter = gl.message.sender_address
        voters = self.proposal_votes[proposal_id]
        assert voter not in voters, "Already voted"

        voters.append(voter)
        self.proposal_votes[proposal_id] = voters

        if vote_for:
            proposal.votes_for += 1
        else:
            proposal.votes_against += 1

        self.governance_proposals[proposal_id] = proposal

        self._add_audit("proposal_voted", voter, proposal_id, {"vote_for": vote_for})
        return proposal

    @gl.public.write
    def finalize_proposal(self, proposal_id: str) -> GovernanceProposal:
        self._require_not_paused()
        assert proposal_id in self.governance_proposals, "Proposal not found"
        proposal = self.governance_proposals[proposal_id]
        assert proposal.status == "active", "Already finalized"
        assert gl.block.number > proposal.voting_deadline_block, "Voting period not ended"

        total_votes = proposal.votes_for + proposal.votes_against
        if total_votes == 0:
            proposal.status = "failed"
        elif proposal.votes_for > proposal.votes_against:
            proposal.status = "passed"
        else:
            proposal.status = "failed"

        self.governance_proposals[proposal_id] = proposal

        self._add_audit("proposal_finalized", gl.message.sender_address, proposal_id, {
            "result": proposal.status, "for": proposal.votes_for, "against": proposal.votes_against
        })
        return proposal

    @gl.public.write
    def appeal_slashing_case(
        self,
        case_id: str,
        appeal_rationale_hash: str,
    ) -> SlashingRecord:
        self._require_not_paused()
        assert case_id in self.slashing_cases, "Case not found"
        case = self.slashing_cases[case_id]
        assert case.stage == STAGE_APPROVED, "Can only appeal approved cases"
        assert gl.block.number <= case.appeal_deadline_block, "Appeal window closed"

        case.stage = STAGE_APPEALED
        self.slashing_cases[case_id] = case

        self._add_audit("slashing_appealed", gl.message.sender_address, case_id, {
            "rationale_hash": appeal_rationale_hash
        })
        return case

    # ─── AI Governance Review (Non-Deterministic LLM) ─────────────────────────

    @gl.public.write
    def ai_review_appeal(
        self,
        case_id: str,
        original_verdict_summary: str,
        appeal_arguments: str,
        new_evidence_summary: str,
        operator_track_record: str,
    ) -> SlashingRecord:
        """
        Non-deterministic: LLM reviews an appeal and may overturn or uphold the original decision.
        Uses numeric outcome scores for fuzzy consensus.
        """
        self._require_not_paused()
        assert case_id in self.slashing_cases, "Case not found"
        case = self.slashing_cases[case_id]
        assert case.stage == STAGE_APPEALED, "Case must be in appealed stage"

        prompt = f"""
You are an impartial senior arbitrator for the SlashSure decentralized network insurance and slashing platform.

Review the following appeal against a slashing decision. Your role is to determine if the original decision should be upheld, modified, or overturned.

=== ORIGINAL DECISION ===
Case ID: {case_id}
Original Fault Probability: {case.fault_probability}/100
Original Severity Score: {case.severity_score}/100
Recommended Slash Percentage: {case.recommended_slash_percentage} basis points
Recommended Slash Amount: {case.recommended_slash_amount} units
Original Summary: {original_verdict_summary}

=== APPEAL ARGUMENTS ===
{appeal_arguments}

=== NEW EVIDENCE (if any) ===
{new_evidence_summary}

=== OPERATOR TRACK RECORD ===
{operator_track_record}

=== REVIEW GUIDELINES ===
- Uphold: original decision is correct, no material new evidence
- Reduce: some mitigating factors justify lower slash amount (reduce by 20-50%)
- Overturn: original decision is clearly wrong, new evidence exonerates operator
- Score 0 = fully overturned, 100 = fully upheld, 50 = reduced by half

=== OUTPUT INSTRUCTIONS ===
Return ONLY a JSON object:

{{
  "appeal_outcome": "<uphold|reduce|overturn>",
  "revised_slash_percentage_bps": <integer 0-10000>,
  "revised_slash_amount": <integer>,
  "uphold_score": <integer 0-100>,
  "confidence_score": <integer 0-100>,
  "rationale": "<3-5 sentence rationale for the appeal decision>",
  "new_evidence_weight": <integer 0-100>
}}

uphold_score: 100 = fully uphold, 0 = fully overturn, 50 = reduce by half.
revised_slash_percentage_bps must be <= original slash_percentage_bps if reducing/overturning.
Return ONLY the JSON object.
"""

        result = gl.get_webpage(
            "https://api.genlayer.com/llm",
            task=prompt,
            eq_principle=(
                "Two appeal reviews are equivalent if: "
                "appeal_outcome string is identical, "
                "revised_slash_percentage_bps values are within 100 basis points (1%) of each other, "
                "uphold_score values are within 10 of each other, "
                "and confidence_score values are within 10 of each other."
            ),
        )

        try:
            parsed = json.loads(result.strip())
            appeal_outcome = str(parsed.get("appeal_outcome", "uphold"))
            revised_bps = max(0, min(case.recommended_slash_percentage,
                                     int(parsed.get("revised_slash_percentage_bps",
                                                     case.recommended_slash_percentage))))
            revised_amount = max(0, int(parsed.get("revised_slash_amount", case.recommended_slash_amount)))
            confidence = max(0, min(100, int(parsed.get("confidence_score", 50))))
        except Exception:
            appeal_outcome = "uphold"
            revised_bps = case.recommended_slash_percentage
            revised_amount = case.recommended_slash_amount
            confidence = 40

        valid_outcomes = ["uphold", "reduce", "overturn"]
        if appeal_outcome not in valid_outcomes:
            appeal_outcome = "uphold"

        if appeal_outcome == "overturn":
            case.stage = STAGE_REJECTED
            case.recommended_slash_percentage = 0
            case.recommended_slash_amount = 0
            case.resolved_at_block = gl.block.number
            # Restore operator status if needed
            if case.operator_address in self.operators:
                op = self.operators[case.operator_address]
                op.status = STATUS_ACTIVE
                op.last_updated = gl.block.number
                self.operators[case.operator_address] = op
        elif appeal_outcome == "reduce":
            case.recommended_slash_percentage = revised_bps
            case.recommended_slash_amount = revised_amount
            case.stage = STAGE_APPROVED
            case.appeal_deadline_block = 0
        else:
            case.stage = STAGE_APPROVED
            case.appeal_deadline_block = 0

        case.confidence_score = confidence
        self.slashing_cases[case_id] = case

        self._add_audit("appeal_reviewed", "llm", case_id, {
            "outcome": appeal_outcome, "revised_bps": revised_bps
        })
        return case

    # ─── Contract Administration ───────────────────────────────────────────────

    @gl.public.write
    def pause_contract(self) -> bool:
        self._require_owner()
        self.contract_paused = True
        self._add_audit("contract_paused", gl.message.sender_address, "contract", {})
        return True

    @gl.public.write
    def unpause_contract(self) -> bool:
        self._require_owner()
        self.contract_paused = False
        self._add_audit("contract_unpaused", gl.message.sender_address, "contract", {})
        return True

    @gl.public.write
    def transfer_ownership(self, new_owner: str) -> bool:
        self._require_owner()
        assert len(new_owner) > 0, "New owner address required"
        old_owner = self.owner
        self.owner = new_owner
        self._add_audit("ownership_transferred", old_owner, "contract", {"new_owner": new_owner})
        return True

    @gl.public.write
    def update_governance_params(
        self,
        min_confidence_slash: int,
        min_confidence_claim: int,
        appeal_window: int,
        max_slash_pct: int,
    ) -> bool:
        self._require_owner()
        assert 0 < min_confidence_slash <= 100, "Invalid confidence threshold"
        assert 0 < min_confidence_claim <= 100, "Invalid confidence threshold"
        assert appeal_window > 0, "Appeal window must be positive"
        assert 0 < max_slash_pct <= 10000, "Max slash must be 0-10000 bps"

        self.min_confidence_for_auto_slash = min_confidence_slash
        self.min_confidence_for_auto_claim = min_confidence_claim
        self.appeal_window_blocks = appeal_window
        self.max_slash_percentage = max_slash_pct

        self._add_audit("params_updated", gl.message.sender_address, "contract", {
            "min_confidence_slash": min_confidence_slash,
            "min_confidence_claim": min_confidence_claim,
            "appeal_window": appeal_window,
        })
        return True

    # ─── Analytics & Views ────────────────────────────────────────────────────

    @gl.public.view
    def get_contract_stats(self) -> dict:
        return {
            "version": self.contract_version,
            "owner": self.owner,
            "paused": self.contract_paused,
            "total_operators": self.total_operators,
            "total_incidents": self.total_incidents,
            "total_slashing_cases": self.total_slashing_cases,
            "total_insurance_claims": self.total_insurance_claims,
            "total_payouts_amount": self.total_payouts_amount,
            "audit_trail_length": len(self.audit_entries),
            "min_confidence_slash": self.min_confidence_for_auto_slash,
            "min_confidence_claim": self.min_confidence_for_auto_claim,
            "appeal_window_blocks": self.appeal_window_blocks,
            "max_slash_percentage_bps": self.max_slash_percentage,
        }

    @gl.public.view
    def get_operator_incidents(self, operator_address: str) -> list:
        if operator_address not in self.operator_incident_index:
            return []
        return list(self.operator_incident_index[operator_address])

    @gl.public.view
    def get_operator_cases(self, operator_address: str) -> list:
        if operator_address not in self.operator_case_index:
            return []
        return list(self.operator_case_index[operator_address])

    @gl.public.view
    def get_operator_claims(self, operator_address: str) -> list:
        if operator_address not in self.operator_claim_index:
            return []
        return list(self.operator_claim_index[operator_address])

    @gl.public.view
    def get_audit_trail_length(self) -> int:
        return len(self.audit_entries)

    @gl.public.view
    def get_audit_entry(self, index: int) -> str:
        assert 0 <= index < len(self.audit_entries), "Index out of range"
        return self.audit_entries[index]

    @gl.public.view
    def get_governance_proposal(self, proposal_id: str) -> GovernanceProposal:
        assert proposal_id in self.governance_proposals, "Proposal not found"
        return self.governance_proposals[proposal_id]

    @gl.public.view
    def is_operator_jailed(self, operator_address: str) -> bool:
        if operator_address not in self.operators:
            return False
        return self.operators[operator_address].status in [STATUS_JAILED, STATUS_SLASHED, STATUS_SUSPENDED]

    @gl.public.view
    def get_operator_reputation_summary(self, operator_address: str) -> dict:
        self._require_operator_exists(operator_address)
        op = self.operators[operator_address]
        return {
            "address": op.address,
            "name": op.name,
            "network": op.network,
            "status": op.status,
            "overall_reputation": op.reputation_score,
            "reliability_score": op.reliability_score,
            "security_score": op.security_score,
            "slashing_risk_score": op.slashing_risk_score,
            "insurance_premium_score": op.insurance_premium_score,
            "predicted_slash_probability": op.predicted_slash_probability,
            "slash_count": op.slash_count,
            "on_chain_hash": op.on_chain_reputation_hash,
            "last_updated_block": op.last_updated,
        }

    @gl.public.view
    def verify_evidence_integrity(self, incident_id: str, expected_merkle_root: str) -> bool:
        if incident_id not in self.evidence_packages:
            return False
        pkg = self.evidence_packages[incident_id]
        return pkg.merkle_root == expected_merkle_root

    @gl.public.view
    def get_slashing_case_summary(self, case_id: str) -> dict:
        assert case_id in self.slashing_cases, "Case not found"
        case = self.slashing_cases[case_id]
        return {
            "case_id": case.case_id,
            "operator": case.operator_address,
            "network": case.network,
            "violation": case.violation_type,
            "stage": case.stage,
            "fault_probability": case.fault_probability,
            "severity_score": case.severity_score,
            "confidence_score": case.confidence_score,
            "recommended_slash_bps": case.recommended_slash_percentage,
            "recommended_slash_amount": case.recommended_slash_amount,
            "executed_slash_amount": case.executed_slash_amount,
            "on_chain_hash": case.on_chain_record_hash,
            "appeal_deadline_block": case.appeal_deadline_block,
            "created_block": case.created_at_block,
            "resolved_block": case.resolved_at_block,
        }

    @gl.public.view
    def get_claim_summary(self, claim_id: str) -> dict:
        assert claim_id in self.insurance_claims, "Claim not found"
        claim = self.insurance_claims[claim_id]
        return {
            "claim_id": claim.claim_id,
            "organization": claim.organization,
            "incident_id": claim.incident_id,
            "status": claim.status,
            "coverage_amount": claim.coverage_amount,
            "claimed_amount": claim.claimed_amount,
            "assessed_damage": claim.assessed_damage,
            "approved_amount": claim.approved_amount,
            "ai_eligible": claim.ai_coverage_eligible,
            "ai_confidence": claim.ai_confidence_score,
            "adjudication_hash": claim.ai_adjudication_hash,
            "on_chain_hash": claim.on_chain_status_hash,
            "submitted_block": claim.submitted_at_block,
            "adjudicated_block": claim.adjudicated_at_block,
        }
