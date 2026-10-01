import pytest
import json
import hashlib
from pathlib import Path


# ── Static Contract Verification Tests ─────────────────────────────────

def test_contract_syntax_and_structure(contract_source):
    """Verify that contract file adheres to GenLayer python specifications."""
    assert contract_source.startswith('# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }')
    assert "class BioOrder:" in contract_source
    assert "class Contract(gl.Contract):" in contract_source
    assert "def set_biosecurity_reserve(" in contract_source
    assert "def transfer_ownership(" in contract_source
    assert "def order_synthesis(" in contract_source
    assert "def submit_synthesis_proof(" in contract_source
    assert "def adjudicate_biosecurity_and_qc(" in contract_source
    assert "def appeal_verdict(" in contract_source
    assert "def adjudicate_appeal(" in contract_source
    assert "def finalize_settlement(" in contract_source
    assert "def cancel_or_reclaim(" in contract_source
    assert "def get_order(" in contract_source
    assert "def get_order_count(" in contract_source
    assert "def get_orders_paginated(" in contract_source
    assert "def get_all_orders(" in contract_source
    assert "def get_stats(" in contract_source


def test_order_struct_attributes(contract_source):
    """Ensure BioOrder struct defines all state fields including bidirectional evidence and real timestamps."""
    expected_fields = [
        "order_id: u64",
        "researcher: Address",
        "foundry: Address",
        "dispute_initiator: Address",
        "escrow_amount: bigint",
        "dispute_bond: bigint",
        "target_protein_function: str",
        "sequence_spec_url: str",
        "spec_evidence_hash: str",
        "qc_report_url: str",
        "qc_evidence_hash: str",
        "evidence_hash: str",
        "status: u8",
        "verdict: str",
        "reason: str",
        "confidence: u8",
        "fidelity_score: u8",
        "created_at: bigint",
        "expires_at: bigint",
        "audit_completed_at: bigint",
        "cooling_off_seconds: bigint",
        "created_at_block: u256",
        "expires_at_block: u256",
        "audit_completed_block: u256",
    ]
    for field in expected_fields:
        assert field in contract_source, f"Missing field in BioOrder: {field}"


def test_canary_and_consensus_rules(contract_source):
    """Ensure security canary token is enforced and validator_fn enforces biosecurity equivalence."""
    assert 'CANARY_TOKEN = "CANARY_AGENT_BIO_SAFETY_V1"' in contract_source
    assert 'mine["verdict"] != leader["verdict"]' in contract_source
    assert 'mine.get("is_biosecure") != leader.get("is_biosecure")' in contract_source
    assert 'leader.get("evidence_hash") != mine.get("evidence_hash")' in contract_source
    assert 'abs(leader_fid - mine_fid) > 20' in contract_source
    assert 'mine["spec_evidence_hash"] != leader["spec_evidence_hash"]' in contract_source
    assert 'mine["qc_evidence_hash"] != leader["qc_evidence_hash"]' in contract_source


def test_native_transfer_calls(contract_source):
    """Ensure payouts, penalties, and refunds use gl.get_contract_at(...).emit_transfer."""
    assert "gl.get_contract_at(o.foundry).emit_transfer" in contract_source
    assert "gl.get_contract_at(self.biosecurity_reserve).emit_transfer" in contract_source
    assert "gl.get_contract_at(o.researcher).emit_transfer" in contract_source


# ── Behavioral Simulation Test Harness ─────────────────────────────────

class MockAgentBioSimulator:
    """Simulates GenVM execution, storage transitions, cooling-off window, and verdict settlements."""

    def __init__(self):
        self.orders = {}
        self.order_ids = []
        self.total_bio_locked = 0
        self.total_orders_settled = 0
        self.order_counter = 0
        self.owner = "0xdeployer00000000000000000000000000000000"
        self.biosecurity_reserve = "0xreserve00000000000000000000000000000000"
        self.current_timestamp = 1700000000
        self.balances = {
            "0xresearcher": 10000,
            "0xfoundry": 2000,
            "0xappellant": 3000,
            "0xdeployer00000000000000000000000000000000": 0,
            "0xreserve00000000000000000000000000000000": 0,
            "0xnewreserve000000000000000000000000000000": 0,
        }

    def _get_current_timestamp(self) -> int:
        return self.current_timestamp

    def _get_current_block(self) -> int:
        return self.order_counter

    def set_biosecurity_reserve(self, sender: str, new_reserve: str):
        if sender.lower() != self.owner.lower():
            raise ValueError("Only protocol owner can update biosecurity reserve.")
        self.biosecurity_reserve = new_reserve.lower()

    def transfer_ownership(self, sender: str, new_owner: str):
        if sender.lower() != self.owner.lower():
            raise ValueError("Only protocol owner can transfer ownership.")
        self.owner = new_owner.lower()

    def order_synthesis(self, sender: str, target_fn: str, spec_url: str, duration_seconds: int, deposit: int) -> int:
        if deposit <= 0:
            raise ValueError("DNA synthesis escrow deposit must be greater than 0 GEN.")
        if not target_fn or len(target_fn.strip()) < 10:
            raise ValueError("Target biological function description must be at least 10 characters.")
        if not (spec_url.startswith("http://") or spec_url.startswith("https://")):
            raise ValueError("Valid public FASTA/GenBank sequence specification URL (http/https) is required.")

        self.order_counter += 1
        oid = self.order_counter
        cur_ts = self._get_current_timestamp()
        duration = duration_seconds if duration_seconds > 0 else 604800

        self.orders[oid] = {
            "order_id": oid,
            "researcher": sender.lower(),
            "foundry": "0x0000000000000000000000000000000000000000",
            "dispute_initiator": "0x0000000000000000000000000000000000000000",
            "escrow_amount": deposit,
            "dispute_bond": 0,
            "target_protein_function": target_fn.strip(),
            "sequence_spec_url": spec_url.strip(),
            "spec_evidence_hash": "",
            "qc_report_url": "",
            "qc_evidence_hash": "",
            "evidence_hash": "",
            "status": 0,  # STATUS_ORDER_OPEN
            "verdict": "PENDING",
            "reason": "Order open. Awaiting DNA synthesis foundry claim.",
            "confidence": 0,
            "fidelity_score": 0,
            "created_at": cur_ts,
            "expires_at": cur_ts + duration,
            "audit_completed_at": 0,
            "cooling_off_seconds": 3600,
            "created_at_block": self.order_counter,
            "expires_at_block": self.order_counter + 5000,
            "audit_completed_block": 0,
        }
        self.order_ids.append(oid)
        self.total_bio_locked += deposit
        self.balances[sender.lower()] -= deposit
        return oid

    def submit_synthesis_proof(self, sender: str, order_id: int, qc_url: str):
        if order_id not in self.orders:
            raise ValueError("Bio order does not exist.")
        o = self.orders[order_id]
        if o["status"] != 0:
            raise ValueError("Bio order is not open for submission.")
        if sender.lower() == o["researcher"]:
            raise ValueError("Researcher cannot fulfill and synthesize their own bio order.")
        if not (qc_url.startswith("http://") or qc_url.startswith("https://")):
            raise ValueError("Valid public sequencing QC report URL (http/https) is required.")

        self.order_counter += 1
        o["foundry"] = sender.lower()
        o["qc_report_url"] = qc_url.strip()
        o["status"] = 1  # STATUS_IN_SYNTHESIS
        o["reason"] = "Sequencing QC report submitted. On-chain AI Biosecurity and Fidelity Board convened."

    def adjudicate_biosecurity_and_qc(self, order_id: int, mock_llm_result: dict, mock_spec_content: str = "SPEC_DATA"):
        if order_id not in self.orders:
            raise ValueError("Bio order does not exist.")
        o = self.orders[order_id]
        if o["status"] != 1:
            raise ValueError("Bio order is not awaiting biosecurity and QC adjudication.")

        qc_raw = mock_llm_result.get("qc_content", "DUMMY_RAW_QC_ALIGNMENT_DATA")
        spec_hash = hashlib.sha256(mock_spec_content.encode("utf-8")).hexdigest()
        qc_hash = hashlib.sha256(qc_raw.encode("utf-8")).hexdigest()

        self.order_counter += 1
        now_ts = self._get_current_timestamp()

        o["verdict"] = mock_llm_result["verdict"]
        o["reason"] = mock_llm_result["reason"]
        o["confidence"] = mock_llm_result["confidence"]
        o["fidelity_score"] = mock_llm_result["fidelity_score"]
        o["spec_evidence_hash"] = spec_hash
        o["qc_evidence_hash"] = qc_hash
        o["evidence_hash"] = qc_hash
        o["status"] = 2  # STATUS_AWAITING_PAYOUT
        o["audit_completed_at"] = now_ts
        o["audit_completed_block"] = self.order_counter

    def appeal_verdict(self, sender: str, order_id: int, dispute_reason: str, bond: int):
        if order_id not in self.orders:
            raise ValueError("Bio order does not exist.")
        o = self.orders[order_id]
        if o["status"] != 2:
            raise ValueError("Can only dispute orders in AWAITING_PAYOUT status.")

        snd = sender.lower()
        if snd != o["researcher"] and snd != o["foundry"]:
            raise ValueError("Only the researcher or foundry can appeal this verdict.")

        now_ts = self._get_current_timestamp()
        if now_ts > (o["audit_completed_at"] + o["cooling_off_seconds"]):
            raise ValueError("Dispute cooling-off window has elapsed. Order is eligible for settlement.")

        required_bond = (o["escrow_amount"] * 10) // 100
        if bond < required_bond:
            raise ValueError(f"Dispute bond insufficient. Minimum required: 10% ({required_bond} wei).")

        if not dispute_reason or len(dispute_reason.strip()) < 10:
            raise ValueError("Substantive dispute justification (at least 10 characters) is required.")

        self.order_counter += 1
        o["status"] = 7  # STATUS_DISPUTED
        o["dispute_initiator"] = snd
        o["dispute_bond"] = bond
        o["reason"] = f"[DISPUTE by {snd[:8]}]: {dispute_reason.strip()}"
        self.total_bio_locked += bond
        self.balances[snd] -= bond

    def adjudicate_appeal(self, order_id: int, supplemental_qc_url: str, appeal_verdict: str, reason: str):
        if order_id not in self.orders:
            raise ValueError("Bio order does not exist.")
        o = self.orders[order_id]
        if o["status"] != 7:  # STATUS_DISPUTED
            raise ValueError("Order is not in DISPUTED status.")
        if not (supplemental_qc_url.startswith("http://") or supplemental_qc_url.startswith("https://")):
            raise ValueError("Valid public supplemental QC evidence URL is required.")

        appellant = o["dispute_initiator"]
        initial_verdict = o["verdict"]
        counterparty = o["foundry"] if appellant == o["researcher"] else o["researcher"]

        escrow_val = o["escrow_amount"]
        bond_val = o["dispute_bond"]
        total_settling = escrow_val + bond_val
        o["dispute_bond"] = 0

        self.total_bio_locked -= total_settling
        self.total_orders_settled += 1

        # Strict Hazardous Bioweapon Forfeiture:
        # If bioweapon confirmed or prior biohazard unproven, 100% of escrow AND bond are slashed to reserve!
        if appeal_verdict == "APPEAL_BIOHAZARD_CONFIRMED" or (initial_verdict == "BIOHAZARD_BLOCKED" and appeal_verdict != "APPEAL_UPHELD_VERIFIED"):
            o["status"] = 4  # STATUS_BIOHAZARD_SLASHED
            o["verdict"] = "BIOHAZARD_BLOCKED"
            o["reason"] = f"[APPEAL BIOHAZARD FORFEITURE] {reason}"
            self.balances[self.biosecurity_reserve] += escrow_val + bond_val
        elif appeal_verdict == "APPEAL_UPHELD_VERIFIED":
            o["status"] = 3  # STATUS_VERIFIED_PAID
            o["verdict"] = "BIO_SYNTHESIS_VERIFIED"
            o["reason"] = f"[APPEAL UPHELD] {reason}"
            self.balances[o["foundry"]] += escrow_val
            self.balances[appellant] += bond_val
        else:
            o["status"] = 5  # STATUS_DEFECTIVE_REFUNDED
            o["verdict"] = "SEQUENCE_DEFECTIVE"
            o["reason"] = f"[APPEAL DISMISSED] {reason}"
            self.balances[o["researcher"]] += escrow_val
            self.balances[counterparty] += bond_val

    def finalize_settlement(self, order_id: int):
        if order_id not in self.orders:
            raise ValueError("Bio order does not exist.")
        o = self.orders[order_id]
        if o["status"] != 2:
            raise ValueError("Bio order is not awaiting settlement payout.")

        now_ts = self._get_current_timestamp()
        if now_ts <= (o["audit_completed_at"] + o["cooling_off_seconds"]):
            raise ValueError("Dispute cooling-off window is still active.")

        self.order_counter += 1
        escrow = o["escrow_amount"]
        self.total_bio_locked -= escrow
        self.total_orders_settled += 1

        if o["verdict"] == "BIO_SYNTHESIS_VERIFIED":
            o["status"] = 3  # STATUS_VERIFIED_PAID
            self.balances[o["foundry"]] += escrow
        elif o["verdict"] == "BIOHAZARD_BLOCKED":
            o["status"] = 4  # STATUS_BIOHAZARD_SLASHED
            self.balances[self.biosecurity_reserve] += escrow
        else:
            o["status"] = 5  # STATUS_DEFECTIVE_REFUNDED
            self.balances[o["researcher"]] += escrow

    def cancel_or_reclaim(self, sender: str, order_id: int):
        if order_id not in self.orders:
            raise ValueError("Bio order does not exist.")
        o = self.orders[order_id]
        if sender.lower() != o["researcher"]:
            raise ValueError("Only the ordering researcher can cancel or reclaim.")

        now_ts = self._get_current_timestamp()
        if o["status"] == 0:
            if now_ts < o["expires_at"]:
                raise ValueError("Cannot cancel: Order duration has not yet expired.")
        elif o["status"] == 1:
            if now_ts < o["expires_at"]:
                raise ValueError("Cannot reclaim: Foundry is actively executing synthesis.")
        else:
            raise ValueError("Order is already settled, under review, or reclaimed.")

        self.order_counter += 1
        o["status"] = 6  # STATUS_CANCELLED
        o["verdict"] = "CANCELLED"
        escrow = o["escrow_amount"]
        self.total_bio_locked -= escrow
        self.balances[o["researcher"]] += escrow


# ── Behavioral End-to-End Test Cases ───────────────────────────────────

def test_full_lifecycle_verified_synthesis(mock_verified_synthesis):
    """Test standard successful DNA synthesis and settlement to Foundry."""
    sim = MockAgentBioSimulator()
    res = "0xresearcher"
    fnd = "0xfoundry"

    oid = sim.order_synthesis(res, "Engineered PETase enzyme for plastic degradation", "https://spec.com/petase.fasta", 3600, 1000)
    assert sim.orders[oid]["status"] == 0
    assert sim.total_bio_locked == 1000

    sim.submit_synthesis_proof(fnd, oid, "https://foundry.com/petase_qc.txt")
    assert sim.orders[oid]["status"] == 1
    assert sim.orders[oid]["foundry"] == fnd

    mock_data = json.loads(mock_verified_synthesis["llm_response"])
    mock_data["qc_content"] = mock_verified_synthesis["qc_content"]
    sim.adjudicate_biosecurity_and_qc(oid, mock_data, mock_spec_content="ATGGTACTG...")

    assert sim.orders[oid]["status"] == 2
    assert sim.orders[oid]["verdict"] == "BIO_SYNTHESIS_VERIFIED"
    assert sim.orders[oid]["fidelity_score"] >= 80
    assert len(sim.orders[oid]["spec_evidence_hash"]) == 64
    assert len(sim.orders[oid]["qc_evidence_hash"]) == 64

    # Advance time beyond cooling-off window (3600 seconds)
    sim.current_timestamp += 3601
    fnd_bal_before = sim.balances[fnd]
    sim.finalize_settlement(oid)

    assert sim.orders[oid]["status"] == 3
    assert sim.balances[fnd] == fnd_bal_before + 1000
    assert sim.total_bio_locked == 0
    assert sim.total_orders_settled == 1


def test_full_lifecycle_biohazard_slashed(mock_biohazard_pathogen):
    """Test detection of dangerous pathogen and forfeiture to Biosecurity Reserve."""
    sim = MockAgentBioSimulator()
    res = "0xresearcher"
    fnd = "0xfoundry"

    oid = sim.order_synthesis(res, "Disguised Botulinum toxin precursor plasmid", "https://spec.com/toxin.fasta", 3600, 2500)
    sim.submit_synthesis_proof(fnd, oid, "https://foundry.com/toxin_qc.txt")

    mock_data = json.loads(mock_biohazard_pathogen["llm_response"])
    mock_data["qc_content"] = mock_biohazard_pathogen["qc_content"]
    sim.adjudicate_biosecurity_and_qc(oid, mock_data)

    assert sim.orders[oid]["status"] == 2
    assert sim.orders[oid]["verdict"] == "BIOHAZARD_BLOCKED"

    sim.current_timestamp += 3601
    reserve_bal_before = sim.balances[sim.biosecurity_reserve]
    sim.finalize_settlement(oid)

    assert sim.orders[oid]["status"] == 4
    assert sim.balances[sim.biosecurity_reserve] == reserve_bal_before + 2500
    assert sim.balances[res] == 10000 - 2500
    assert sim.total_bio_locked == 0
    assert sim.total_orders_settled == 1


def test_hazardous_appeal_forfeiture_strictly_enforced(mock_biohazard_pathogen):
    """Verify that an appeal on a BIOHAZARD_BLOCKED order CANNOT bypass forfeiture: 100% escrow AND bond are slashed to Reserve."""
    sim = MockAgentBioSimulator()
    res = "0xresearcher"
    fnd = "0xfoundry"

    oid = sim.order_synthesis(res, "Disguised weaponized biological agent", "https://spec.com/hazard.fasta", 3600, 2000)
    sim.submit_synthesis_proof(fnd, oid, "https://foundry.com/qc_hazard.txt")

    mock_data = json.loads(mock_biohazard_pathogen["llm_response"])
    mock_data["qc_content"] = mock_biohazard_pathogen["qc_content"]
    sim.adjudicate_biosecurity_and_qc(oid, mock_data)

    # Malicious researcher appeals attempting to recover funds
    sim.appeal_verdict(res, oid, "Claiming false positive select agent identification", 200)
    assert sim.orders[oid]["status"] == 7  # STATUS_DISPUTED
    assert sim.total_bio_locked == 2000 + 200

    reserve_bal_before = sim.balances[sim.biosecurity_reserve]
    res_bal_before = sim.balances[res]

    # Appellate tribunal dismisses appeal / confirms biohazard
    sim.adjudicate_appeal(
        order_id=oid,
        supplemental_qc_url="https://evidence.org/lab_rerun.fasta",
        appeal_verdict="APPEAL_BIOHAZARD_CONFIRMED",
        reason="Secondary alignment confirms active Tier 1 botulinum neurotoxin catalytic domain."
    )

    # Verified: 100% escrow (2000) AND 10% dispute bond (200) are slashed to reserve!
    assert sim.orders[oid]["status"] == 4  # STATUS_BIOHAZARD_SLASHED
    assert sim.orders[oid]["verdict"] == "BIOHAZARD_BLOCKED"
    assert sim.balances[sim.biosecurity_reserve] == reserve_bal_before + 2000 + 200
    assert sim.balances[res] == res_bal_before  # Researcher receives 0 GEN back!
    assert sim.total_bio_locked == 0
    assert sim.total_orders_settled == 1


def test_reserve_ownership_and_governance():
    """Verify that only the protocol owner can update the biosecurity reserve address."""
    sim = MockAgentBioSimulator()
    owner = "0xdeployer00000000000000000000000000000000"
    attacker = "0xresearcher"
    new_res = "0xnewreserve000000000000000000000000000000"

    # Attacker attempts to hijack biosecurity reserve
    with pytest.raises(ValueError, match="Only protocol owner can update biosecurity reserve"):
        sim.set_biosecurity_reserve(attacker, new_res)

    # Protocol owner successfully updates reserve
    sim.set_biosecurity_reserve(owner, new_res)
    assert sim.biosecurity_reserve == new_res.lower()

    # Transfer ownership
    sim.transfer_ownership(owner, attacker)
    assert sim.owner == attacker.lower()

    # Old owner can no longer set reserve
    with pytest.raises(ValueError, match="Only protocol owner can update biosecurity reserve"):
        sim.set_biosecurity_reserve(owner, new_res)


def test_cooling_off_dispute_appeal(mock_defective_sequence):
    """Verify 1-hour cooling-off window timing and dispute bond requirements."""
    sim = MockAgentBioSimulator()
    res = "0xresearcher"
    fnd = "0xfoundry"

    oid = sim.order_synthesis(res, "Therapeutic enzyme for rare disease", "https://spec.com/seq", 3600, 1000)
    sim.submit_synthesis_proof(fnd, oid, "https://foundry.com/qc.txt")

    mock_data = json.loads(mock_defective_sequence["llm_response"])
    mock_data["qc_content"] = mock_defective_sequence["qc_content"]
    sim.adjudicate_biosecurity_and_qc(oid, mock_data)

    # Insufficient bond (<10% of 1000 = 100)
    with pytest.raises(ValueError, match="Dispute bond insufficient"):
        sim.appeal_verdict(fnd, oid, "Filing appeal with low bond", 50)

    # Successful appeal within cooling-off window
    sim.appeal_verdict(fnd, oid, "Contesting alignment mutation in locus 14", 100)
    assert sim.orders[oid]["status"] == 7
    assert sim.orders[oid]["dispute_bond"] == 100
    assert sim.total_bio_locked == 1100


def test_adjudicate_appeal_upheld_settlement(mock_defective_sequence):
    """Test adjudication of appeal when appeal is upheld: foundry receives payment and returned bond."""
    sim = MockAgentBioSimulator()
    res = "0xresearcher"
    fnd = "0xfoundry"

    oid = sim.order_synthesis(res, "Industrial degradation enzyme", "https://spec.com/seq", 3600, 1000)
    sim.submit_synthesis_proof(fnd, oid, "https://foundry.com/qc.txt")

    mock_data = json.loads(mock_defective_sequence["llm_response"])
    mock_data["qc_content"] = mock_defective_sequence["qc_content"]
    sim.adjudicate_biosecurity_and_qc(oid, mock_data)

    sim.appeal_verdict(fnd, oid, "Contesting alignment error with supplemental PacBio read", 100)
    fnd_bal_before = sim.balances[fnd]

    # Appellate court upholds appeal: 1000 escrow + 100 bond returned to foundry
    sim.adjudicate_appeal(
        order_id=oid,
        supplemental_qc_url="https://evidence.org/pacbio_hifi.fasta",
        appeal_verdict="APPEAL_UPHELD_VERIFIED",
        reason="Supplemental PacBio HiFi sequencing demonstrates 99.4% purity and 0 frame-shift mutations."
    )

    assert sim.orders[oid]["status"] == 3  # STATUS_VERIFIED_PAID
    assert sim.orders[oid]["verdict"] == "BIO_SYNTHESIS_VERIFIED"
    assert sim.balances[fnd] == fnd_bal_before + 1000 + 100
    assert sim.total_bio_locked == 0
    assert sim.total_orders_settled == 1


def test_adjudicate_appeal_dismissed_settlement(mock_defective_sequence):
    """Test adjudication of appeal when appeal is rejected: bond forfeited to counterparty."""
    sim = MockAgentBioSimulator()
    res = "0xresearcher"
    fnd = "0xfoundry"

    oid = sim.order_synthesis(res, "Industrial degradation enzyme", "https://spec.com/seq", 3600, 1000)
    sim.submit_synthesis_proof(fnd, oid, "https://foundry.com/qc.txt")

    mock_data = json.loads(mock_defective_sequence["llm_response"])
    mock_data["qc_content"] = mock_defective_sequence["qc_content"]
    sim.adjudicate_biosecurity_and_qc(oid, mock_data)

    sim.appeal_verdict(fnd, oid, "Contesting alignment error in codon 44", 100)
    assert sim.orders[oid]["status"] == 7

    res_bal_before = sim.balances[res]

    # Appellate court dismisses appeal: 1000 escrow refunded to researcher, 100 bond awarded to researcher
    sim.adjudicate_appeal(
        order_id=oid,
        supplemental_qc_url="https://evidence.org/re-run.fasta",
        appeal_verdict="APPEAL_DISMISSED_DEFECTIVE",
        reason="Supplemental evidence confirms unresolvable premature stop codon."
    )

    assert sim.orders[oid]["status"] == 5  # STATUS_DEFECTIVE_REFUNDED
    assert sim.orders[oid]["verdict"] == "SEQUENCE_DEFECTIVE"
    assert sim.balances[res] == res_bal_before + 1000 + 100  # Escrow refunded + counterparty received bond
    assert sim.total_bio_locked == 0
    assert sim.total_orders_settled == 1


def test_researcher_cannot_fulfill_own_order():
    """Verify Sybil defense: Researcher is prohibited from claiming their own bio order."""
    sim = MockAgentBioSimulator()
    res = "0xresearcher"
    oid = sim.order_synthesis(res, "Novel synthetic promoter for mammalian vectors", "https://spec.com/seq", 3600, 200)

    with pytest.raises(ValueError, match="cannot fulfill and synthesize their own"):
        sim.submit_synthesis_proof(res, oid, "https://qc.com/report")


def test_cancel_or_reclaim_rules():
    """Verify cancellation permissions and expiration safeguards."""
    sim = MockAgentBioSimulator()
    res = "0xresearcher"
    oid = sim.order_synthesis(res, "Enzymatic biosensor for heavy metal detection", "https://spec.com/seq", 3600, 400)

    with pytest.raises(ValueError, match="has not yet expired"):
        sim.cancel_or_reclaim(res, oid)

    # Advance timestamp beyond 3600 seconds
    sim.current_timestamp += 3601
    bal_before = sim.balances[res]
    sim.cancel_or_reclaim(res, oid)

    assert sim.orders[oid]["status"] == 6  # STATUS_CANCELLED
    assert sim.balances[res] == bal_before + 400
