# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
from dataclasses import dataclass
import json

CANARY_TOKEN = "CANARY_AGENT_BIO_SAFETY_V1"
DEFAULT_COOLING_OFF_SECONDS = bigint(3600)        # 1 hour cooling-off window
DEFAULT_SYNTHESIS_EXPIRY_SECONDS = bigint(604800) # 7 days

# Biosecurity Order Statuses
STATUS_ORDER_OPEN = u8(0)           # Awaiting DNA synthesis foundry agreement/claim
STATUS_IN_SYNTHESIS = u8(1)         # Bilateral agreement bound: foundry synthesizing & sequencing
STATUS_AWAITING_PAYOUT = u8(2)      # Biosecurity & QC verdict rendered, cooling-off active
STATUS_VERIFIED_PAID = u8(3)        # Settled: Synthesis verified & released to Foundry
STATUS_BIOHAZARD_SLASHED = u8(4)    # Settled: Prohibited bioweapon/pathogen detected, funds slashed to reserve
STATUS_DEFECTIVE_REFUNDED = u8(5)   # Settled: Sequence mutated/defective, refunded to researcher
STATUS_CANCELLED = u8(6)            # Cancelled after expiry / unclaimed
STATUS_DISPUTED = u8(7)             # Disputed during cooling-off window


class ContractError(Exception):
    """Domain-specific error for AgentBio protocol rule violations and reverts."""
    pass


def _addr_str(addr) -> str:
    """Safely format an Address instance into a lowercase hex string."""
    try:
        return addr.as_hex.lower()
    except Exception:
        return str(addr).lower()


def _get_sender() -> Address:
    """Safely obtain transaction sender across GenVM runtime versions."""
    try:
        return gl.message.sender_address
    except Exception:
        raise ContractError("Cannot resolve sender address.")


def _is_valid_sha256(h: str) -> bool:
    """Validate that a string is a genuine 64-character lowercase hex SHA-256 hash."""
    if not isinstance(h, str):
        return False
    h_clean = h.strip().lower()
    return len(h_clean) == 64 and all(c in "0123456789abcdef" for c in h_clean)


@allow_storage
@dataclass
class BioOrder:
    order_id: u64
    researcher: Address
    foundry: Address
    target_foundry: Address
    has_target_foundry: bool
    dispute_initiator: Address
    escrow_amount: bigint
    dispute_bond: bigint
    target_protein_function: str
    sequence_spec_url: str
    spec_evidence_hash: str
    qc_report_url: str
    qc_evidence_hash: str
    evidence_hash: str
    lab_attestation_id: str
    status: u8
    verdict: str
    reason: str
    confidence: u8
    fidelity_score: u8
    created_at: bigint
    expires_at: bigint
    audit_completed_at: bigint
    cooling_off_seconds: bigint
    created_at_block: u256
    expires_at_block: u256
    audit_completed_block: u256
    terms_hash: str
    agreement_accepted: bool
    agreement_timestamp: bigint
    appeal_certifying_lab: Address
    supplemental_evidence_hash: str


class Contract(gl.Contract):
    """
    AgentBio: Autonomous Synthetic Biology Protocol & DNA Sequence Safety Escrow
    Target Network: GenLayer studionet (Chain ID: 61999)
    """
    orders: TreeMap[u64, BioOrder]
    order_ids: DynArray[u64]
    total_bio_locked: bigint
    total_orders_settled: u32
    order_counter: u64
    owner: Address
    biosecurity_reserve: Address
    default_cooling_off_seconds: bigint
    authorized_foundries: TreeMap[Address, bool]
    foundry_lab_ids: TreeMap[Address, str]
    appeal_attestations: TreeMap[u64, str]  # order_id -> lab-signed attestation hash
    claimable_balances: TreeMap[Address, bigint]  # recipient -> pending withdrawal (safe recovery)

    def __init__(self):
        deployer = _get_sender()
        self.owner = deployer
        self.biosecurity_reserve = deployer
        self.default_cooling_off_seconds = bigint(120)  # 2 minutes for testing & fast settlement
        self.total_bio_locked = bigint(0)
        self.total_orders_settled = u32(0)
        self.order_counter = u64(0)
        self.authorized_foundries[deployer] = True
        self.foundry_lab_ids[deployer] = "LAB-GENLAYER-DELEGATE-01"

    def _safe_transfer(self, recipient: Address, amount: bigint) -> bool:
        """
        Executes outbound native transfer with safe recovery pattern.
        If outbound transfer succeeds, returns True.
        If outbound transfer fails, reverts, or is ambiguous, safely credits
        the exact entitlement to claimable_balances[recipient] so funds are never lost,
        and can be withdrawn safely via claim_payout().
        """
        if amount <= bigint(0):
            return True
        try:
            gl.get_contract_at(recipient).emit_transfer(value=u256(amount))
            return True
        except Exception:
            current_claimable = self.claimable_balances.get(recipient, bigint(0))
            self.claimable_balances[recipient] = current_claimable + amount
            return False

    def _get_current_timestamp(self) -> bigint:
        import calendar
        from datetime import datetime, timezone
        try:
            if hasattr(gl, "message_raw") and isinstance(gl.message_raw, dict):
                raw_val = gl.message_raw.get("datetime")
                if raw_val:
                    dt_str = str(raw_val).strip().replace("Z", "+00:00")
                    dt = datetime.fromisoformat(dt_str)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    ts = calendar.timegm(dt.utctimetuple())
                    if ts > 0:
                        return bigint(ts)
        except Exception:
            pass
        raise ContractError("Authoritative timestamp unavailable. Transaction aborted for safety.")

    # ── Protocol Governance & Registry ────────────────────────────────

    @gl.public.write
    def set_biosecurity_reserve(self, new_reserve: Address) -> None:
        if _addr_str(_get_sender()) != _addr_str(self.owner):
            raise ContractError("Only protocol owner can update biosecurity reserve.")
        self.biosecurity_reserve = new_reserve

    @gl.public.write
    def set_cooling_off_seconds(self, new_seconds: u64) -> None:
        if _addr_str(_get_sender()) != _addr_str(self.owner):
            raise ContractError("Only protocol owner can update cooling off period.")
        self.default_cooling_off_seconds = bigint(int(new_seconds))

    @gl.public.write
    def set_order_cooling_off(self, order_id: u64, new_seconds: u64) -> None:
        if _addr_str(_get_sender()) != _addr_str(self.owner):
            raise ContractError("Only protocol owner can configure order cooling off window.")
        if order_id not in self.orders:
            raise ContractError(f"Bio order {int(order_id)} does not exist.")
        self.orders[order_id].cooling_off_seconds = bigint(int(new_seconds))

    @gl.public.write
    def transfer_ownership(self, new_owner: Address) -> None:
        if _addr_str(_get_sender()) != _addr_str(self.owner):
            raise ContractError("Only protocol owner can transfer ownership.")
        self.owner = new_owner

    @gl.public.write
    def register_foundry(self, foundry: Address, lab_id: str) -> None:
        if _addr_str(_get_sender()) != _addr_str(self.owner):
            raise ContractError("Only protocol owner can register authorized foundries.")
        clean_lab = str(lab_id).strip()
        if not clean_lab:
            raise ContractError("Valid laboratory accreditation ID is required.")
        self.authorized_foundries[foundry] = True
        self.foundry_lab_ids[foundry] = clean_lab

    @gl.public.write
    def register_audit_lab(self, lab_address: Address, lab_id: str) -> None:
        self.register_foundry(lab_address, lab_id)

    @gl.public.write
    def attest_appeal_evidence(self, order_id: u64, evidence_hash: str) -> None:
        """Certifying lab binds supplemental evidence to a specific order before appeal."""
        sender = _get_sender()
        if not self.authorized_foundries.get(sender, False):
            raise ContractError("Only registered accredited laboratories can attest evidence.")
        if order_id not in self.orders:
            raise ContractError(f"Bio order {int(order_id)} does not exist.")
        o = self.orders[order_id]
        if o.status != STATUS_AWAITING_PAYOUT and o.status != STATUS_DISPUTED:
            raise ContractError("Order must be in AWAITING_PAYOUT or DISPUTED status for attestation.")
        clean_hash = str(evidence_hash).strip().lower()
        if not _is_valid_sha256(clean_hash):
            raise ContractError("Valid 64-character hex SHA-256 evidence hash is required.")
        import hashlib
        lab_id = self.foundry_lab_ids.get(sender, "")
        attestation_binding = hashlib.sha256(
            f"{int(order_id)}:{_addr_str(sender)}:{lab_id}:{clean_hash}".encode("utf-8")
        ).hexdigest()
        self.appeal_attestations[order_id] = attestation_binding

    @gl.public.write
    def revoke_foundry(self, foundry: Address) -> None:
        if _addr_str(_get_sender()) != _addr_str(self.owner):
            raise ContractError("Only protocol owner can revoke foundries.")
        self.authorized_foundries[foundry] = False

    @gl.public.view
    def is_authorized_foundry(self, foundry: Address) -> bool:
        return bool(self.authorized_foundries.get(foundry, False))

    @gl.public.view
    def get_foundry_lab_id(self, foundry: Address) -> str:
        return self.foundry_lab_ids.get(foundry, "")

    # ── Core Escrow Lifecycle ─────────────────────────────────────────

    @gl.public.write.payable
    def order_synthesis(
        self,
        target_protein_function: str,
        sequence_spec_url: str,
        duration_seconds: u64,
        spec_evidence_hash: str
    ) -> u64:
        import hashlib
        bounty = bigint(gl.message.value)
        if bounty <= bigint(0):
            raise ContractError("DNA synthesis escrow deposit must be greater than 0 GEN.")

        clean_fn = str(target_protein_function).strip()
        if len(clean_fn) < 10:
            raise ContractError("Target biological function description must be at least 10 characters.")

        clean_spec = str(sequence_spec_url).strip()
        if not (clean_spec.startswith("http://") or clean_spec.startswith("https://")):
            raise ContractError("Valid public FASTA sequence specification URL is required.")

        clean_spec_hash = str(spec_evidence_hash).strip().lower()
        if not _is_valid_sha256(clean_spec_hash):
            raise ContractError("Valid 64-character hex SHA-256 specification content commitment is required.")

        now = self._get_current_timestamp()
        dur = bigint(int(duration_seconds)) if int(duration_seconds) > 0 else DEFAULT_SYNTHESIS_EXPIRY_SECONDS
        expires_at = now + dur

        self.order_counter = self.order_counter + u64(1)
        order_id = self.order_counter
        sender = _get_sender()

        terms_hash = hashlib.sha256(
            f"{clean_fn}:{clean_spec}:{clean_spec_hash}:{int(bounty)}:{int(expires_at)}".encode("utf-8")
        ).hexdigest()

        new_order = BioOrder(
            order_id=order_id,
            researcher=sender,
            foundry=sender,
            target_foundry=sender,
            has_target_foundry=False,
            dispute_initiator=sender,
            escrow_amount=bounty,
            dispute_bond=bigint(0),
            target_protein_function=clean_fn,
            sequence_spec_url=clean_spec,
            spec_evidence_hash=clean_spec_hash,
            qc_report_url="",
            qc_evidence_hash="",
            evidence_hash=clean_spec_hash,
            lab_attestation_id="",
            status=STATUS_ORDER_OPEN,
            verdict="PENDING",
            reason="Order open. Awaiting authorized bio-foundry agreement.",
            confidence=u8(0),
            fidelity_score=u8(0),
            created_at=now,
            expires_at=expires_at,
            audit_completed_at=bigint(0),
            cooling_off_seconds=self.default_cooling_off_seconds,
            created_at_block=u256(0),
            expires_at_block=u256(5000),
            audit_completed_block=u256(0),
            terms_hash=terms_hash,
            agreement_accepted=False,
            agreement_timestamp=bigint(0),
            appeal_certifying_lab=sender,
            supplemental_evidence_hash="",
        )

        self.orders[order_id] = new_order
        self.order_ids.append(order_id)
        self.total_bio_locked = self.total_bio_locked + bounty
        return order_id

    @gl.public.write.payable
    def order_synthesis_designated(
        self,
        target_protein_function: str,
        sequence_spec_url: str,
        duration_seconds: u64,
        spec_evidence_hash: str,
        target_foundry: Address
    ) -> u64:
        if not self.authorized_foundries.get(target_foundry, False):
            raise ContractError("Designated target foundry must be registered in the authorized registry.")

        order_id = self.order_synthesis(target_protein_function, sequence_spec_url, duration_seconds, spec_evidence_hash)
        o = self.orders[order_id]
        o.target_foundry = target_foundry
        o.has_target_foundry = True
        return order_id

    @gl.public.write
    def accept_synthesis_agreement(self, order_id: u64) -> None:
        if order_id not in self.orders:
            raise ContractError(f"Bio order {int(order_id)} does not exist.")

        o = self.orders[order_id]
        if o.status != STATUS_ORDER_OPEN:
            raise ContractError("Bio order is not open for acceptance.")

        sender = _get_sender()
        if _addr_str(sender) == _addr_str(o.researcher):
            raise ContractError("Researcher cannot fulfill their own bio order.")

        if not self.authorized_foundries.get(sender, False):
            raise ContractError("Unauthorized: Only accredited foundries can accept synthesis orders.")

        if o.has_target_foundry and (_addr_str(sender) != _addr_str(o.target_foundry)):
            raise ContractError("Unauthorized: Only the designated accredited foundry can accept this order.")

        now = self._get_current_timestamp()
        if now >= o.expires_at:
            raise ContractError("Cannot accept agreement: Order has expired.")

        o.foundry = sender
        o.agreement_accepted = True
        o.agreement_timestamp = now
        o.status = STATUS_IN_SYNTHESIS
        lab_id = self.foundry_lab_ids.get(sender, f"LAB-ISO17025-{_addr_str(sender)[:8].upper()}")
        o.lab_attestation_id = lab_id
        o.reason = f"Bilateral synthesis agreement accepted by accredited foundry ({lab_id})."

    @gl.public.write
    def submit_synthesis_proof(
        self,
        order_id: u64,
        qc_report_url: str,
        qc_evidence_hash: str
    ) -> None:
        if order_id not in self.orders:
            raise ContractError(f"Bio order {int(order_id)} does not exist.")

        o = self.orders[order_id]
        sender = _get_sender()
        now = self._get_current_timestamp()

        if not self.authorized_foundries.get(sender, False):
            raise ContractError("Unauthorized: Only accredited foundries can submit synthesis proof.")

        if o.status == STATUS_IN_SYNTHESIS:
            if _addr_str(sender) != _addr_str(o.foundry):
                raise ContractError("Unauthorized: Only the assigned foundry can submit synthesis proof.")
            if now >= o.expires_at:
                raise ContractError("Cannot submit proof: Synthesis deadline has passed.")
        elif o.status == STATUS_ORDER_OPEN:
            if _addr_str(sender) == _addr_str(o.researcher):
                raise ContractError("Researcher cannot fulfill their own bio order.")
            if o.has_target_foundry and (_addr_str(sender) != _addr_str(o.target_foundry)):
                raise ContractError("Unauthorized: Only the designated foundry can submit proof.")
            if now >= o.expires_at:
                raise ContractError("Cannot submit proof: Order has expired.")
            o.foundry = sender
            o.agreement_accepted = True
            o.agreement_timestamp = now
            o.status = STATUS_IN_SYNTHESIS
        else:
            raise ContractError("Bio order is not awaiting QC submission.")

        clean_url = str(qc_report_url).strip()
        if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
            raise ContractError("Valid public sequencing QC report URL is required.")

        clean_qc_hash = str(qc_evidence_hash).strip().lower()
        if not _is_valid_sha256(clean_qc_hash):
            raise ContractError("Valid 64-character hex SHA-256 QC report content commitment is required.")

        registered_lab = self.foundry_lab_ids.get(sender, f"LAB-ISO17025-{_addr_str(sender)[:8].upper()}")
        o.qc_report_url = clean_url
        o.qc_evidence_hash = clean_qc_hash
        o.lab_attestation_id = registered_lab
        o.reason = f"Sequencing QC report submitted by accredited laboratory ({registered_lab}). Ready for AI adjudication."

    @gl.public.write
    def adjudicate_biosecurity_and_qc(self, order_id: u64) -> None:
        if order_id not in self.orders:
            raise ContractError(f"Bio order {int(order_id)} does not exist.")

        o = self.orders[order_id]
        if o.status != STATUS_IN_SYNTHESIS:
            raise ContractError("Bio order is not awaiting biosecurity and QC adjudication.")

        # Read storage variables OUTSIDE nondet block
        spec_url = o.sequence_spec_url
        qc_url = o.qc_report_url
        target_fn = o.target_protein_function
        lab_id = o.lab_attestation_id
        expected_spec_hash = o.spec_evidence_hash
        expected_qc_hash = o.qc_evidence_hash

        def leader_fn():
            import hashlib
            raw_spec = ""
            spec_fetch_err = False
            try:
                raw_spec = gl.nondet.web.render(spec_url, mode="text")
            except Exception:
                spec_fetch_err = True

            raw_qc = ""
            qc_fetch_err = False
            try:
                raw_qc = gl.nondet.web.render(qc_url, mode="text")
            except Exception:
                qc_fetch_err = True

            # Separate retrieval failures (aborts without penalizing foundry)
            if spec_fetch_err or not raw_spec or qc_fetch_err or not raw_qc:
                return {
                    "canary": CANARY_TOKEN,
                    "verdict": "RETRIEVAL_FAILED",
                    "reason": "Evidence retrieval failure: Webpage was unreachable or returned empty payload.",
                    "fidelity_score": 0,
                    "confidence": 0,
                    "computed_spec_hash": "",
                    "computed_qc_hash": "",
                }

            spec_hash = hashlib.sha256(raw_spec.encode("utf-8")).hexdigest()
            qc_hash = hashlib.sha256(raw_qc.encode("utf-8")).hexdigest()

            # Verify genuine content commitments against retrieved evidence (zero URL fallback)
            if spec_hash != expected_spec_hash:
                return {
                    "canary": CANARY_TOKEN,
                    "verdict": "COMMITMENT_VERIFICATION_FAILED",
                    "reason": f"Specification hash mismatch. Expected {expected_spec_hash[:12]}..., got {spec_hash[:12]}...",
                    "fidelity_score": 0,
                    "confidence": 100,
                    "computed_spec_hash": spec_hash,
                    "computed_qc_hash": qc_hash,
                }

            if qc_hash != expected_qc_hash:
                return {
                    "canary": CANARY_TOKEN,
                    "verdict": "COMMITMENT_VERIFICATION_FAILED",
                    "reason": f"Delivered QC hash mismatch. Expected {expected_qc_hash[:12]}..., got {qc_hash[:12]}...",
                    "fidelity_score": 0,
                    "confidence": 100,
                    "computed_spec_hash": spec_hash,
                    "computed_qc_hash": qc_hash,
                }

            MAX_COMPREHENSIVE_EVIDENCE_CHARS = 12000
            spec_len = len(raw_spec)
            qc_len = len(raw_qc)

            if spec_len > MAX_COMPREHENSIVE_EVIDENCE_CHARS or qc_len > MAX_COMPREHENSIVE_EVIDENCE_CHARS:
                return {
                    "canary": CANARY_TOKEN,
                    "verdict": "EVIDENCE_INSUFFICIENT",
                    "reason": f"Evidence payload (Spec: {spec_len}, QC: {qc_len}) exceeds comprehensive assessment limit ({MAX_COMPREHENSIVE_EVIDENCE_CHARS} chars). Aborted as inconclusive to prevent missing critical sequence details.",
                    "fidelity_score": 0,
                    "confidence": 0,
                    "computed_spec_hash": spec_hash,
                    "computed_qc_hash": qc_hash,
                }

            prompt = f"""You are the Chief Biosecurity & Molecular Quality Arbiter on GenLayer.
Evaluate the synthetic biology order comparing commissioned target specification against delivered synthesis QC report.

ACCREDITED LAB: {lab_id}
INTENDED FUNCTION: {target_fn}

COMMISSIONED SPECIFICATION ({spec_len} chars):
{raw_spec}

DELIVERED SEQUENCING QC REPORT ({qc_len} chars):
{raw_qc}

EVALUATION CRITERIA:
1. Biosecurity Screening: If dual-use toxins or prohibited pathogens are detected -> Output 'BIOHAZARD_BLOCKED'.
2. Alignment Fidelity: If safe and fidelity >= 80% -> Output 'BIO_SYNTHESIS_VERIFIED'. If fidelity < 80% -> Output 'SEQUENCE_DEFECTIVE'.

SECURITY CANARY: Include "canary": "{CANARY_TOKEN}" in JSON.
Respond ONLY with valid JSON:
{{
  "canary": "{CANARY_TOKEN}",
  "verdict": "BIO_SYNTHESIS_VERIFIED"|"BIOHAZARD_BLOCKED"|"SEQUENCE_DEFECTIVE",
  "confidence": <0-100>,
  "fidelity_score": <0-100>,
  "reason": "<critique summary under 200 chars>"
}}"""

            res = gl.nondet.exec_prompt(prompt, response_format="json")
            parsed = None
            if isinstance(res, dict):
                parsed = res
            elif isinstance(res, str):
                try:
                    parsed = json.loads(res.replace("```json", "").replace("```", "").strip())
                except Exception:
                    pass

            if not parsed or str(parsed.get("canary", "")) != CANARY_TOKEN:
                return {
                    "canary": CANARY_TOKEN,
                    "verdict": "SEQUENCE_DEFECTIVE",
                    "reason": "Validator peer-review parsing failure.",
                    "fidelity_score": 0,
                    "confidence": 0,
                    "computed_spec_hash": spec_hash,
                    "computed_qc_hash": qc_hash,
                }

            v_str = str(parsed.get("verdict", "SEQUENCE_DEFECTIVE")).upper().strip()
            if v_str not in {"BIO_SYNTHESIS_VERIFIED", "BIOHAZARD_BLOCKED", "SEQUENCE_DEFECTIVE", "EVIDENCE_INSUFFICIENT"}:
                v_str = "SEQUENCE_DEFECTIVE"

            fid = int(parsed.get("fidelity_score", 0))
            if v_str == "BIO_SYNTHESIS_VERIFIED" and fid < 80:
                v_str = "SEQUENCE_DEFECTIVE"

            return {
                "canary": CANARY_TOKEN,
                "verdict": v_str,
                "confidence": max(0, min(100, int(parsed.get("confidence", 85)))),
                "fidelity_score": max(0, min(100, fid)),
                "reason": str(parsed.get("reason", "QC audit completed."))[:200],
                "computed_spec_hash": spec_hash,
                "computed_qc_hash": qc_hash,
                "spec_evidence_hash": spec_hash,
                "qc_evidence_hash": qc_hash,
                "evidence_hash": qc_hash,
                "is_biosecure": bool(v_str != "BIOHAZARD_BLOCKED"),
            }

        def validator_fn(leader_res) -> bool:
            if not isinstance(leader_res, gl.vm.Return):
                return False
            leader = leader_res.calldata
            if not isinstance(leader, dict) or "verdict" not in leader:
                return False
            if leader.get("canary") != CANARY_TOKEN:
                return False

            mine = leader_fn()

            # Retrieval failures or commitment mismatches must match
            if leader.get("verdict") in {"RETRIEVAL_FAILED", "COMMITMENT_VERIFICATION_FAILED", "EVIDENCE_INSUFFICIENT"}:
                return mine.get("verdict") == leader.get("verdict")

            if mine["verdict"] != leader["verdict"]:
                return False

            if mine.get("is_biosecure") != leader.get("is_biosecure"):
                return False

            if leader.get("evidence_hash") != mine.get("evidence_hash"):
                return False

            if mine["spec_evidence_hash"] != leader["spec_evidence_hash"]:
                return False

            if mine["qc_evidence_hash"] != leader["qc_evidence_hash"]:
                return False

            # Independently enforce 80% fidelity threshold across consensus
            leader_fid = leader.get("fidelity_score", 0)
            mine_fid = mine.get("fidelity_score", 0)
            if leader["verdict"] == "BIO_SYNTHESIS_VERIFIED":
                if leader_fid < 80 or mine_fid < 80:
                    return False

            if abs(leader_fid - mine_fid) > 20:
                return False

            return True

        adjudication_res = gl.vm.run_nondet(leader_fn, validator_fn)

        if adjudication_res.get("verdict") == "RETRIEVAL_FAILED":
            raise ContractError("Evidence retrieval failed: Webpage unreachable. Adjudication aborted without penalty.")

        if adjudication_res.get("verdict") == "COMMITMENT_VERIFICATION_FAILED":
            raise ContractError(f"Commitment verification failed: {adjudication_res.get('reason')}")

        if adjudication_res.get("verdict") == "EVIDENCE_INSUFFICIENT":
            raise ContractError("Evidence excerpt insufficient for confident determination. Provide complete evidence and retry.")

        final_verdict = adjudication_res["verdict"]
        final_fid = u8(adjudication_res["fidelity_score"])
        final_reason = adjudication_res["reason"]

        if final_verdict == "BIO_SYNTHESIS_VERIFIED" and int(final_fid) < 80:
            final_verdict = "SEQUENCE_DEFECTIVE"
            final_reason = f"[INDEPENDENT ENFORCEMENT] Fidelity ({final_fid}%) below 80% threshold: {final_reason}"

        now = self._get_current_timestamp()
        o.verdict = final_verdict
        o.confidence = u8(adjudication_res["confidence"])
        o.fidelity_score = final_fid
        o.reason = final_reason
        o.status = STATUS_AWAITING_PAYOUT
        o.audit_completed_at = now

    @gl.public.write.payable
    def appeal_verdict(
        self,
        order_id: u64,
        dispute_reason: str,
        certifying_lab: Address,
        supplemental_evidence_hash: str
    ) -> None:
        if order_id not in self.orders:
            raise ContractError(f"Bio order {int(order_id)} does not exist.")

        o = self.orders[order_id]
        if o.status != STATUS_AWAITING_PAYOUT:
            raise ContractError("Can only dispute orders in AWAITING_PAYOUT status.")

        sender = _get_sender()
        if _addr_str(sender) != _addr_str(o.researcher) and _addr_str(sender) != _addr_str(o.foundry):
            raise ContractError("Unauthorized: Only researcher or foundry can appeal.")

        now = self._get_current_timestamp()
        if now > (o.audit_completed_at + o.cooling_off_seconds):
            raise ContractError("Dispute cooling-off window has elapsed.")

        required_bond = (o.escrow_amount * bigint(10)) // bigint(100)
        if required_bond == bigint(0):
            required_bond = bigint(1)

        staked = bigint(gl.message.value)
        if staked < required_bond:
            raise ContractError(f"Dispute bond insufficient. Minimum required: 10% ({required_bond} wei).")

        clean_reason = str(dispute_reason).strip()
        if len(clean_reason) < 10:
            raise ContractError("Substantive dispute justification (>= 10 chars) is required.")

        # Require authenticated reviewing laboratory
        if not self.authorized_foundries.get(certifying_lab, False):
            raise ContractError("Certifying reviewing laboratory must be registered in the accreditation registry.")

        clean_supp_hash = str(supplemental_evidence_hash).strip().lower()
        if not _is_valid_sha256(clean_supp_hash):
            raise ContractError("Valid 64-character hex SHA-256 supplemental evidence commitment is required.")

        o.status = STATUS_DISPUTED
        o.dispute_initiator = sender
        o.dispute_bond = staked
        o.appeal_certifying_lab = certifying_lab
        o.supplemental_evidence_hash = clean_supp_hash
        # Verify lab has attested this evidence for this specific order
        stored_attestation = self.appeal_attestations.get(order_id, "")
        if not stored_attestation:
            raise ContractError("Certifying lab must call attest_appeal_evidence() before appeal can proceed.")
        import hashlib
        c_lab_id = self.foundry_lab_ids.get(certifying_lab, "")
        expected_attestation = hashlib.sha256(
            f"{int(order_id)}:{_addr_str(certifying_lab)}:{c_lab_id}:{clean_supp_hash}".encode("utf-8")
        ).hexdigest()
        if stored_attestation != expected_attestation:
            raise ContractError("Lab attestation does not match the supplemental evidence hash and order binding.")
        o.reason = f"[DISPUTE by {_addr_str(sender)[:8]}]: {clean_reason} | Prior: {o.reason}"
        self.total_bio_locked = self.total_bio_locked + staked

    @gl.public.write
    def adjudicate_appeal(
        self,
        order_id: u64,
        supplemental_qc_url: str
    ) -> None:
        if order_id not in self.orders:
            raise ContractError(f"Bio order {int(order_id)} does not exist.")

        o = self.orders[order_id]
        if o.status != STATUS_DISPUTED:
            raise ContractError("Order is not in DISPUTED status.")

        clean_url = str(supplemental_qc_url).strip()
        if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
            raise ContractError("Valid public supplemental QC evidence URL is required.")

        # Read storage variables outside nondet block
        c_lab = o.appeal_certifying_lab
        if not self.authorized_foundries.get(c_lab, False):
            raise ContractError("Appeal certifying lab is not authorized in registry.")

        lab_id = self.foundry_lab_ids.get(c_lab, "LAB-ACCREDITED-AUDITOR")
        expected_supp_hash = o.supplemental_evidence_hash
        appellant = o.dispute_initiator
        initial_verdict = o.verdict
        target_fn = o.target_protein_function
        spec_url = o.sequence_spec_url
        is_researcher = (_addr_str(appellant) == _addr_str(o.researcher))

        def leader_fn():
            import hashlib
            raw_supp = ""
            supp_fetch_err = False
            try:
                raw_supp = gl.nondet.web.render(clean_url, mode="text")
            except Exception:
                supp_fetch_err = True

            raw_spec = ""
            try:
                raw_spec = gl.nondet.web.render(spec_url, mode="text")
            except Exception:
                pass

            if supp_fetch_err or not raw_supp:
                return {
                    "canary": CANARY_TOKEN,
                    "verdict": "RETRIEVAL_FAILED",
                    "reason": "Supplemental laboratory evidence URL unreachable.",
                }

            computed_hash = hashlib.sha256(raw_supp.encode("utf-8")).hexdigest()
            if computed_hash != expected_supp_hash:
                return {
                    "canary": CANARY_TOKEN,
                    "verdict": "APPEAL_DISMISSED",
                    "reason": f"Supplemental evidence hash mismatch (expected {expected_supp_hash[:12]}..., got {computed_hash[:12]}...).",
                }

            supp_len = len(raw_supp)
            MAX_COMPREHENSIVE_EVIDENCE_CHARS = 12000
            if supp_len > MAX_COMPREHENSIVE_EVIDENCE_CHARS:
                return {
                    "canary": CANARY_TOKEN,
                    "verdict": "EXCERPT_INSUFFICIENT",
                    "reason": f"Supplemental evidence ({supp_len} chars) exceeds comprehensive assessment limit ({MAX_COMPREHENSIVE_EVIDENCE_CHARS} chars). Aborted as inconclusive.",
                }

            # Laboratory-authorized attestation binding verification
            lab_id_str = str(lab_id).strip()
            lab_addr_str = _addr_str(c_lab)
            order_marker = f"ORDER_REF: {int(order_id)}"
            order_marker_json = f'"order_id": {int(order_id)}'
            order_marker_txt = f"Order #{int(order_id)}"

            has_order_ref = (order_marker in raw_supp) or (order_marker_json in raw_supp) or (order_marker_txt in raw_supp)
            has_lab_ref = (lab_id_str in raw_supp) or (lab_addr_str in raw_supp.lower())

            if not (has_order_ref and has_lab_ref):
                return {
                    "canary": CANARY_TOKEN,
                    "verdict": "UNAUTHORIZED_ATTESTATION",
                    "reason": f"Supplemental report lacks authentic laboratory attestation binding to Order #{int(order_id)} and accredited laboratory {lab_id_str}.",
                }

            prompt = f"""You are the Supreme Appellate Biosecurity Court on GenLayer.
Re-examine the contested biological order with authenticated supplemental laboratory evidence.

ACCREDITED AUDITOR LAB: {lab_id}
INTENDED FUNCTION: {target_fn}
PRIOR VERDICT: {initial_verdict}
APPELLANT ROLE: {"RESEARCHER" if is_researcher else "FOUNDRY"}

SUPPLEMENTAL AUDIT EVIDENCE ({supp_len} chars):
{raw_supp}

DECISION CRITERIA:
- If prior was BIOHAZARD_BLOCKED and sequence is proven benign therapeutic -> 'APPEAL_BIOHAZARD_OVERTURNED_BENIGN'.
- If prohibited pathogen confirmed -> 'APPEAL_BIOHAZARD_CONFIRMED'.
- If Foundry appealed and delivery authentic (fidelity >= 80%) -> 'APPEAL_UPHELD_VERIFIED'.
- If Researcher appealed and delivery proven defective -> 'APPEAL_OVERTURNED_DEFECTIVE'.
- Otherwise -> 'APPEAL_DISMISSED'.

SECURITY CANARY: Include "canary": "{CANARY_TOKEN}" in JSON.
Respond ONLY with valid JSON:
{{"canary": "{CANARY_TOKEN}", "verdict": "APPEAL_UPHELD_VERIFIED"|"APPEAL_OVERTURNED_DEFECTIVE"|"APPEAL_BIOHAZARD_OVERTURNED_BENIGN"|"APPEAL_BIOHAZARD_CONFIRMED"|"APPEAL_DISMISSED", "reason": "<rationale>"}}"""

            res = gl.nondet.exec_prompt(prompt, response_format="json")
            parsed = None
            if isinstance(res, dict):
                parsed = res
            elif isinstance(res, str):
                try:
                    parsed = json.loads(res.replace("```json", "").replace("```", "").strip())
                except Exception:
                    pass

            if not parsed or str(parsed.get("canary", "")) != CANARY_TOKEN:
                return {
                    "canary": CANARY_TOKEN,
                    "verdict": "INCONCLUSIVE_TRIBUNAL_ERROR",
                    "reason": "Appellate tribunal response was malformed or failed canary validation.",
                }

            v_str = str(parsed.get("verdict", "")).upper().strip()
            if v_str not in {"APPEAL_UPHELD_VERIFIED", "APPEAL_OVERTURNED_DEFECTIVE", "APPEAL_BIOHAZARD_OVERTURNED_BENIGN", "APPEAL_BIOHAZARD_CONFIRMED", "APPEAL_DISMISSED"}:
                return {
                    "canary": CANARY_TOKEN,
                    "verdict": "INCONCLUSIVE_TRIBUNAL_ERROR",
                    "reason": f"Unrecognized appellate verdict '{v_str}'. Aborting without altering state.",
                }

            return {
                "canary": CANARY_TOKEN,
                "verdict": v_str,
                "reason": str(parsed.get("reason", "Appellate review complete."))[:200]
            }

        def validator_fn(leader_res) -> bool:
            if not isinstance(leader_res, gl.vm.Return):
                return False
            leader = leader_res.calldata
            if not isinstance(leader, dict) or "verdict" not in leader:
                return False
            if leader.get("canary") != CANARY_TOKEN:
                return False
            mine = leader_fn()
            return mine["verdict"] == leader["verdict"]

        appeal_res = gl.vm.run_nondet(leader_fn, validator_fn)

        if appeal_res.get("verdict") == "RETRIEVAL_FAILED":
            raise ContractError("Supplemental evidence retrieval failed. Adjudication aborted without penalty.")

        if appeal_res.get("verdict") == "EXCERPT_INSUFFICIENT":
            raise ContractError("Supplemental evidence exceeds comprehensive assessment limit. Appellate adjudication aborted as inconclusive without penalty.")

        if appeal_res.get("verdict") == "UNAUTHORIZED_ATTESTATION":
            raise ContractError(f"Supplemental appeal document rejected: {appeal_res.get('reason')}")

        if appeal_res.get("verdict") == "INCONCLUSIVE_TRIBUNAL_ERROR":
            raise ContractError(f"Appellate tribunal inconclusive: {appeal_res.get('reason')}. Transaction aborted without altering order state or confirming biohazard.")

        app_verdict = appeal_res["verdict"]
        app_reason = appeal_res["reason"]

        escrow_val = o.escrow_amount
        bond_val = o.dispute_bond
        total_settling = escrow_val + bond_val
        o.dispute_bond = bigint(0)
        o.escrow_amount = bigint(0)
        self.total_bio_locked = self.total_bio_locked - total_settling
        self.total_orders_settled = self.total_orders_settled + u32(1)

        counterparty = o.foundry if is_researcher else o.researcher

        if app_verdict == "APPEAL_BIOHAZARD_OVERTURNED_BENIGN":
            o.status = STATUS_DEFECTIVE_REFUNDED
            o.verdict = "SEQUENCE_DEFECTIVE"
            o.reason = f"[BIOHAZARD OVERTURNED] Proven benign: {app_reason}"
            if escrow_val > bigint(0):
                self._safe_transfer(o.researcher, escrow_val)
            if bond_val > bigint(0):
                self._safe_transfer(appellant, bond_val)

        elif app_verdict == "APPEAL_BIOHAZARD_CONFIRMED" or (initial_verdict == "BIOHAZARD_BLOCKED" and app_verdict != "APPEAL_BIOHAZARD_OVERTURNED_BENIGN"):
            o.status = STATUS_BIOHAZARD_SLASHED
            o.verdict = "BIOHAZARD_BLOCKED"
            o.reason = f"[PATHOGEN FORFEITURE] Confirmed biohazard: {app_reason}"
            if escrow_val > bigint(0):
                self._safe_transfer(self.biosecurity_reserve, escrow_val)
            if bond_val > bigint(0):
                self._safe_transfer(self.biosecurity_reserve, bond_val)

        elif app_verdict == "APPEAL_UPHELD_VERIFIED":
            o.status = STATUS_VERIFIED_PAID
            o.verdict = "BIO_SYNTHESIS_VERIFIED"
            o.reason = f"[APPEAL UPHELD] Synthesis verified: {app_reason}"
            if escrow_val > bigint(0):
                self._safe_transfer(o.foundry, escrow_val)
            if bond_val > bigint(0):
                self._safe_transfer(appellant, bond_val)

        elif app_verdict == "APPEAL_OVERTURNED_DEFECTIVE":
            o.status = STATUS_DEFECTIVE_REFUNDED
            o.verdict = "SEQUENCE_DEFECTIVE"
            o.reason = f"[APPEAL UPHELD] Delivery defective: {app_reason}"
            if escrow_val > bigint(0):
                self._safe_transfer(o.researcher, escrow_val)
            if bond_val > bigint(0):
                self._safe_transfer(appellant, bond_val)

        else:
            if initial_verdict == "BIO_SYNTHESIS_VERIFIED":
                o.status = STATUS_VERIFIED_PAID
                o.verdict = "BIO_SYNTHESIS_VERIFIED"
                o.reason = f"[APPEAL DISMISSED] Upheld verified: {app_reason}"
                if escrow_val > bigint(0):
                    self._safe_transfer(o.foundry, escrow_val)
                if bond_val > bigint(0):
                    self._safe_transfer(counterparty, bond_val)
            else:
                o.status = STATUS_DEFECTIVE_REFUNDED
                o.verdict = "SEQUENCE_DEFECTIVE"
                o.reason = f"[APPEAL DISMISSED] Upheld defective: {app_reason}"
                if escrow_val > bigint(0):
                    self._safe_transfer(o.researcher, escrow_val)
                if bond_val > bigint(0):
                    self._safe_transfer(counterparty, bond_val)
    @gl.public.write
    def recover_disputed_order(self, order_id: u64) -> None:
        if order_id not in self.orders:
            raise ContractError(f"Bio order {int(order_id)} does not exist.")

        o = self.orders[order_id]
        if o.status != STATUS_DISPUTED:
            raise ContractError("Bio order is not in DISPUTED status.")

        now = self._get_current_timestamp()
        timeout = o.audit_completed_at + (o.cooling_off_seconds * bigint(7))
        if now < timeout:
            raise ContractError("Dispute resolution window is still active.")

        escrow_val = o.escrow_amount
        bond_val = o.dispute_bond
        total_settling = escrow_val + bond_val
        o.dispute_bond = bigint(0)
        o.escrow_amount = bigint(0)
        self.total_bio_locked = self.total_bio_locked - total_settling
        self.total_orders_settled = self.total_orders_settled + u32(1)

        appellant = o.dispute_initiator
        counterparty = o.foundry if _addr_str(appellant) == _addr_str(o.researcher) else o.researcher

        if o.verdict == "BIOHAZARD_BLOCKED":
            o.status = STATUS_BIOHAZARD_SLASHED
            o.reason = "[DISPUTE TIMEOUT] Confiscated to reserve."
            if escrow_val > bigint(0):
                self._safe_transfer(self.biosecurity_reserve, escrow_val)
            if bond_val > bigint(0):
                self._safe_transfer(self.biosecurity_reserve, bond_val)
        elif o.verdict == "BIO_SYNTHESIS_VERIFIED":
            o.status = STATUS_VERIFIED_PAID
            o.reason = "[DISPUTE TIMEOUT] Initial verified verdict upheld."
            if escrow_val > bigint(0):
                self._safe_transfer(o.foundry, escrow_val)
            if bond_val > bigint(0):
                self._safe_transfer(counterparty, bond_val)
        else:
            o.status = STATUS_DEFECTIVE_REFUNDED
            o.reason = "[DISPUTE TIMEOUT] Initial defective verdict upheld."
            if escrow_val > bigint(0):
                self._safe_transfer(o.researcher, escrow_val)
            if bond_val > bigint(0):
                self._safe_transfer(counterparty, bond_val)

    @gl.public.write
    def finalize_settlement(self, order_id: u64) -> None:
        if order_id not in self.orders:
            raise ContractError(f"Bio order {int(order_id)} does not exist.")

        o = self.orders[order_id]
        if o.status != STATUS_AWAITING_PAYOUT:
            raise ContractError("Bio order is not awaiting settlement payout.")

        now = self._get_current_timestamp()
        if now <= (o.audit_completed_at + o.cooling_off_seconds):
            raise ContractError("Dispute cooling-off window is still active.")

        escrow_val = o.escrow_amount
        o.escrow_amount = bigint(0)
        self.total_bio_locked = self.total_bio_locked - escrow_val
        self.total_orders_settled = self.total_orders_settled + u32(1)

        if o.verdict == "BIO_SYNTHESIS_VERIFIED":
            o.status = STATUS_VERIFIED_PAID
            if escrow_val > bigint(0):
                self._safe_transfer(o.foundry, escrow_val)
        elif o.verdict == "BIOHAZARD_BLOCKED":
            o.status = STATUS_BIOHAZARD_SLASHED
            if escrow_val > bigint(0):
                self._safe_transfer(self.biosecurity_reserve, escrow_val)
        else:
            o.status = STATUS_DEFECTIVE_REFUNDED
            if escrow_val > bigint(0):
                self._safe_transfer(o.researcher, escrow_val)

    @gl.public.write
    def cancel_or_reclaim(self, order_id: u64) -> None:
        if order_id not in self.orders:
            raise ContractError(f"Bio order {int(order_id)} does not exist.")

        o = self.orders[order_id]
        sender = _get_sender()
        if _addr_str(sender) != _addr_str(o.researcher):
            raise ContractError("Unauthorized: Only the ordering researcher can cancel or reclaim.")

        now = self._get_current_timestamp()
        if o.status == STATUS_ORDER_OPEN:
            if now < o.expires_at:
                raise ContractError("Cannot cancel: Order duration has not expired.")
        elif o.status == STATUS_IN_SYNTHESIS:
            if now < o.expires_at:
                raise ContractError("Cannot reclaim: Synthesis deadline has not elapsed.")
        else:
            raise ContractError("Order cannot be cancelled in current status.")

        o.status = STATUS_CANCELLED
        o.verdict = "CANCELLED"
        o.reason = "Order expired and escrow reclaimed by researcher."

        escrow_val = o.escrow_amount
        o.escrow_amount = bigint(0)
        self.total_bio_locked = self.total_bio_locked - escrow_val
        self.total_orders_settled = self.total_orders_settled + u32(1)

        if escrow_val > bigint(0):
            self._safe_transfer(o.researcher, escrow_val)

    @gl.public.write
    def claim_payout(self) -> None:
        """
        Pull-payment safe recovery mechanism.
        Enables recipients to withdraw pending claimable balances safely if
        prior automated outbound push-transfers failed or were deferred.
        Guarantees zero lost entitlements and zero duplicate payouts.
        """
        sender = _get_sender()
        balance = self.claimable_balances.get(sender, bigint(0))
        if balance <= bigint(0):
            raise ContractError("No claimable balance available for withdrawal.")

        self.claimable_balances[sender] = bigint(0)
        try:
            gl.get_contract_at(sender).emit_transfer(value=u256(balance))
        except Exception:
            self.claimable_balances[sender] = balance
            raise ContractError("Outbound transfer failed during payout claim. Balance preserved.")

    @gl.public.view
    def get_claimable_balance(self, account: Address) -> str:
        """Returns the pending claimable balance for an account."""
        return str(self.claimable_balances.get(account, bigint(0)))

    # ── Read-only Views ───────────────────────────────────────────────

    @gl.public.view
    def get_order(self, order_id: u64) -> str:
        if order_id not in self.orders:
            raise ContractError(f"Bio order {int(order_id)} does not exist.")

        o = self.orders[order_id]
        has_foundry = bool(o.agreement_accepted)
        data = {
            "order_id": int(o.order_id),
            "researcher": _addr_str(o.researcher),
            "foundry": _addr_str(o.foundry) if has_foundry else "0x0000000000000000000000000000000000000000",
            "target_foundry": _addr_str(o.target_foundry) if o.has_target_foundry else "0x0000000000000000000000000000000000000000",
            "has_target_foundry": bool(o.has_target_foundry),
            "is_authorized_foundry": bool(self.authorized_foundries.get(o.foundry, False)) if has_foundry else False,
            "lab_attestation_id": o.lab_attestation_id,
            "dispute_initiator": _addr_str(o.dispute_initiator),
            "escrow_amount": str(o.escrow_amount),
            "dispute_bond": str(o.dispute_bond),
            "target_protein_function": o.target_protein_function,
            "sequence_spec_url": o.sequence_spec_url,
            "spec_evidence_hash": o.spec_evidence_hash,
            "qc_report_url": o.qc_report_url,
            "qc_evidence_hash": o.qc_evidence_hash,
            "evidence_hash": o.qc_evidence_hash,
            "status": int(o.status),
            "verdict": o.verdict,
            "reason": o.reason,
            "confidence": int(o.confidence),
            "fidelity_score": int(o.fidelity_score),
            "created_at": str(o.created_at),
            "expires_at": str(o.expires_at),
            "audit_completed_at": str(o.audit_completed_at),
            "cooling_off_seconds": str(o.cooling_off_seconds),
            "terms_hash": str(o.terms_hash),
            "agreement_accepted": bool(o.agreement_accepted),
            "agreement_timestamp": str(o.agreement_timestamp),
            "appeal_certifying_lab": _addr_str(o.appeal_certifying_lab),
            "supplemental_evidence_hash": o.supplemental_evidence_hash,
        }
        return json.dumps(data)

    @gl.public.view
    def get_order_count(self) -> u64:
        return u64(len(self.order_ids))

    @gl.public.view
    def get_orders_paginated(self, offset: u64, limit: u64) -> str:
        orders = []
        start = int(offset)
        end = min(start + int(limit), len(self.order_ids))
        for i in range(start, end):
            oid = self.order_ids[i]
            orders.append(json.loads(self.get_order(oid)))
        return json.dumps(orders)

    @gl.public.view
    def get_all_orders(self) -> str:
        all_o = []
        for oid in self.order_ids:
            all_o.append(json.loads(self.get_order(oid)))
        return json.dumps(all_o)

    @gl.public.view
    def get_stats(self) -> str:
        metrics = {
            "total_orders": len(self.order_ids),
            "total_bio_locked": str(self.total_bio_locked),
            "total_orders_settled": int(self.total_orders_settled),
            "owner": _addr_str(self.owner),
            "biosecurity_reserve": _addr_str(self.biosecurity_reserve),
        }
        return json.dumps(metrics)
