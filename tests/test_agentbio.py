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
    assert "def order_synthesis(" in contract_source
    assert "def submit_synthesis_proof(" in contract_source
    assert "def adjudicate_biosecurity_and_qc(" in contract_source
    assert "def appeal_verdict(" in contract_source
    assert "def finalize_settlement(" in contract_source
    assert "def cancel_or_reclaim(" in contract_source
    assert "def get_order(" in contract_source
    assert "def get_order_count(" in contract_source
    assert "def get_orders_paginated(" in contract_source
    assert "def get_all_orders(" in contract_source
    assert "def get_stats(" in contract_source


def test_order_struct_attributes(contract_source):
    """Ensure BioOrder struct defines all state fields according to biosecurity escrow design."""
    expected_fields = [
        "order_id: u64",
        "researcher: Address",
        "foundry: Address",
        "dispute_initiator: Address",
        "escrow_amount: bigint",
        "dispute_bond: bigint",
        "target_protein_function: str",
        "sequence_spec_url: str",
        "qc_report_url: str",
        "evidence_hash: str",
        "status: u8",
        "verdict: str",
        "reason: str",
        "confidence: u8",
        "fidelity_score: u8",
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
        self.biosecurity_reserve = "0xreserve00000000000000000000000000000000"
        self.balances = {
            "0xresearcher": 10000,
            "0xfoundry": 2000,
            "0xappellant": 3000,
            "0xreserve00000000000000000000000000000000": 0,
        }

    def _get_current_block(self) -> int:
        return self.order_counter

    def order_synthesis(self, sender: str, target_fn: str, spec_url: str, duration_blocks: int, deposit: int) -> int:
        if deposit <= 0:
            raise ValueError("DNA synthesis escrow deposit must be greater than 0 GEN.")
        if not target_fn or len(target_fn.strip()) < 10:
            raise ValueError("Target biological function description must be at least 10 characters.")
        if not (spec_url.startswith("http://") or spec_url.startswith("https://")):
            raise ValueError("Valid public FASTA/GenBank sequence specification URL (http/https) is required.")

        self.order_counter += 1
        oid = self.order_counter
        cur = self._get_current_block()
        duration = duration_blocks if duration_blocks > 0 else 5000

        self.orders[oid] = {
            "order_id": oid,
            "researcher": sender.lower(),
            "foundry": "0x0000000000000000000000000000000000000000",
            "dispute_initiator": "0x0000000000000000000000000000000000000000",
            "escrow_amount": deposit,
            "dispute_bond": 0,
            "target_protein_function": target_fn.strip(),
            "sequence_spec_url": spec_url.strip(),
            "qc_report_url": "",
            "evidence_hash": "",
            "status": 0,  # STATUS_ORDER_OPEN
            "verdict": "PENDING",
            "reason": "Order open. Awaiting DNA synthesis foundry claim.",
            "confidence": 0,
            "fidelity_score": 0,
            "created_at_block": cur,
            "expires_at_block": cur + duration,
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
            raise ValueError("Valid public sequencing QC report URL is required.")

        self.order_counter += 1
        o["foundry"] = sender.lower()
        o["qc_report_url"] = qc_url.strip()
        o["status"] = 1  # STATUS_IN_SYNTHESIS
        o["reason"] = "Sequencing QC report submitted."

    def adjudicate_biosecurity_and_qc(self, order_id: int, mock_result: dict):
        if order_id not in self.orders:
            raise ValueError("Bio order does not exist.")
        o = self.orders[order_id]
        if o["status"] != 1:
            raise ValueError("Bio order is not awaiting biosecurity and QC adjudication.")

        verdict = mock_result["verdict"]
        conf = mock_result["confidence"]
        fid = mock_result["fidelity_score"]
        reason = mock_result["reason"]
        ev_hash = hashlib.sha256(mock_result.get("qc_content", "").encode("utf-8")).hexdigest()

        o["verdict"] = verdict
        o["confidence"] = conf
        o["fidelity_score"] = fid
        o["reason"] = reason
        o["evidence_hash"] = ev_hash

        self.order_counter += 1
        o["status"] = 2  # STATUS_AWAITING_PAYOUT
        o["audit_completed_block"] = self._get_current_block()

    def appeal_verdict(self, sender: str, order_id: int, dispute_reason: str, bond: int):
        if order_id not in self.orders:
            raise ValueError("Bio order does not exist.")
        o = self.orders[order_id]
        if o["status"] != 2:
            raise ValueError("Can only dispute orders in AWAITING_PAYOUT status.")
        if sender.lower() != o["researcher"] and sender.lower() != o["foundry"]:
            raise ValueError("Only researcher or foundry can appeal.")

        self.order_counter += 1
        cur = self._get_current_block()
        if cur > (o["audit_completed_block"] + 24):
            raise ValueError("Dispute cooling-off window has elapsed.")

        req_bond = max(1, (o["escrow_amount"] * 10) // 100)
        if bond < req_bond:
            raise ValueError("Dispute bond insufficient.")
        if len(dispute_reason.strip()) < 10:
            raise ValueError("Substantive dispute justification required.")

        o["status"] = 7  # STATUS_DISPUTED
        o["dispute_initiator"] = sender.lower()
        o["dispute_bond"] = bond
        o["reason"] = f"[DISPUTE]: {dispute_reason.strip()}"
        self.total_bio_locked += bond
        self.balances[sender.lower()] -= bond

    def finalize_settlement(self, order_id: int):
        if order_id not in self.orders:
            raise ValueError("Bio order does not exist.")
        o = self.orders[order_id]
        if o["status"] != 2:
            raise ValueError("Bio order is not awaiting settlement payout.")

        self.order_counter += 1
        cur = self._get_current_block()
        if cur <= (o["audit_completed_block"] + 24):
            raise ValueError("Dispute cooling-off window (24 blocks) is still active.")

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

        self.order_counter += 1
        cur = self._get_current_block()
        if o["status"] == 0:
            if cur < o["expires_at_block"]:
                raise ValueError("Cannot cancel: Order duration has not yet expired.")
        elif o["status"] == 1:
            if cur < (o["created_at_block"] + 100):
                raise ValueError("Cannot reclaim: Foundry is actively executing synthesis.")
        else:
            raise ValueError("Order is already settled, under review, or reclaimed.")

        o["status"] = 6  # STATUS_CANCELLED
        o["verdict"] = "CANCELLED"
        escrow = o["escrow_amount"]
        self.total_bio_locked -= escrow
        self.balances[o["researcher"]] += escrow


# ── Behavioral Test Cases ───────────────────────────────────────────────

def test_full_lifecycle_verified_synthesis(mock_verified_synthesis):
    """Test full cycle where sequence passes biosecurity and fidelity: 100% payment released to foundry."""
    sim = MockAgentBioSimulator()
    res = "0xresearcher"
    fnd = "0xfoundry"

    # 1. Researcher locks 500 GEN escrow
    oid = sim.order_synthesis(
        sender=res,
        target_fn="Humanized Monoclonal Antibody heavy chain for therapeutic immunotherapy",
        spec_url="https://ncbi.nlm.nih.gov/nuccore/AH002931.2?report=fasta",
        duration_blocks=1000,
        deposit=500
    )
    assert oid == 1
    assert sim.orders[oid]["status"] == 0
    assert sim.total_bio_locked == 500

    # 2. Foundry claims and submits NGS sequencing QC URL
    sim.submit_synthesis_proof(
        sender=fnd,
        order_id=oid,
        qc_url="https://biofoundry.example.com/qc_runs/run_8921.fasta"
    )
    assert sim.orders[oid]["status"] == 1
    assert sim.orders[oid]["foundry"] == fnd

    # 3. Adjudicate: BIO_SYNTHESIS_VERIFIED
    mock_data = json.loads(mock_verified_synthesis["llm_response"])
    mock_data["qc_content"] = mock_verified_synthesis["qc_content"]
    sim.adjudicate_biosecurity_and_qc(oid, mock_data)
    assert sim.orders[oid]["status"] == 2
    assert sim.orders[oid]["verdict"] == "BIO_SYNTHESIS_VERIFIED"
    assert sim.orders[oid]["fidelity_score"] >= 80

    # 4. Attempt premature settlement during cooling-off window (should fail)
    with pytest.raises(ValueError, match="still active"):
        sim.finalize_settlement(oid)

    # 5. Advance block counter past 24 blocks cooling-off window
    sim.order_counter += 25

    # 6. Settle escrow: Foundry receives payment
    fnd_bal_before = sim.balances[fnd]
    sim.finalize_settlement(oid)
    assert sim.orders[oid]["status"] == 3  # STATUS_VERIFIED_PAID
    assert sim.balances[fnd] == fnd_bal_before + 500
    assert sim.total_bio_locked == 0
    assert sim.total_orders_settled == 1


def test_full_lifecycle_biohazard_slashed(mock_biohazard_pathogen):
    """Test prohibited pathogen or weaponized toxin detection: funds confiscated to biosecurity reserve."""
    sim = MockAgentBioSimulator()
    res = "0xresearcher"
    fnd = "0xfoundry"

    # Researcher attempts to secretly synthesize Botulinum neurotoxin
    oid = sim.order_synthesis(
        sender=res,
        target_fn="Novel enzymatic catalyst with high zinc binding affinity",
        spec_url="https://ncbi.nlm.nih.gov/nuccore/AF012345.1?report=fasta",
        duration_blocks=1000,
        deposit=1000
    )

    sim.submit_synthesis_proof(fnd, oid, "https://biofoundry.example.com/qc_runs/run_6606.fasta")

    # Adjudication flags Tier 1 Select Agent Toxin
    mock_data = json.loads(mock_biohazard_pathogen["llm_response"])
    mock_data["qc_content"] = mock_biohazard_pathogen["qc_content"]
    sim.adjudicate_biosecurity_and_qc(oid, mock_data)
    assert sim.orders[oid]["status"] == 2
    assert sim.orders[oid]["verdict"] == "BIOHAZARD_BLOCKED"

    # Advance past cooling-off
    sim.order_counter += 25

    # Finalize: Escrow slashed to biosecurity reserve pool
    reserve_addr = sim.biosecurity_reserve
    res_before = sim.balances[reserve_addr]
    sim.finalize_settlement(oid)

    assert sim.orders[oid]["status"] == 4  # STATUS_BIOHAZARD_SLASHED
    assert sim.balances[reserve_addr] == res_before + 1000
    assert sim.balances[fnd] == 2000  # Foundry did not receive payout


def test_full_lifecycle_defective_sequence_refund(mock_defective_sequence):
    """Test frame-shift mutation / low purity: 100% escrow refunded to researcher."""
    sim = MockAgentBioSimulator()
    res = "0xresearcher"
    fnd = "0xfoundry"

    oid = sim.order_synthesis(
        sender=res,
        target_fn="Industrial Beta-Glucosidase enzyme for biomass degradation",
        spec_url="https://ncbi.nlm.nih.gov/nuccore/BG0099.1?report=fasta",
        duration_blocks=1000,
        deposit=300
    )

    sim.submit_synthesis_proof(fnd, oid, "https://biofoundry.example.com/qc_runs/run_4112.fasta")

    mock_data = json.loads(mock_defective_sequence["llm_response"])
    mock_data["qc_content"] = mock_defective_sequence["qc_content"]
    sim.adjudicate_biosecurity_and_qc(oid, mock_data)
    assert sim.orders[oid]["status"] == 2
    assert sim.orders[oid]["verdict"] == "SEQUENCE_DEFECTIVE"
    assert sim.orders[oid]["fidelity_score"] < 80

    sim.order_counter += 25

    res_bal_before = sim.balances[res]
    sim.finalize_settlement(oid)

    assert sim.orders[oid]["status"] == 5  # STATUS_DEFECTIVE_REFUNDED
    assert sim.balances[res] == res_bal_before + 300


def test_cooling_off_dispute_appeal(mock_defective_sequence):
    """Test dispute appeal during cooling-off window with 10% bond requirement."""
    sim = MockAgentBioSimulator()
    res = "0xresearcher"
    fnd = "0xfoundry"

    oid = sim.order_synthesis(res, "Therapeutic enzyme for rare pediatric disorder", "https://spec.com/seq", 1000, 1000)
    sim.submit_synthesis_proof(fnd, oid, "https://foundry.com/qc.txt")

    mock_data = json.loads(mock_defective_sequence["llm_response"])
    mock_data["qc_content"] = mock_defective_sequence["qc_content"]
    sim.adjudicate_biosecurity_and_qc(oid, mock_data)

    # 1. Non-party cannot dispute
    with pytest.raises(ValueError, match="Only researcher or foundry"):
        sim.appeal_verdict("0xstranger", oid, "I disagree with this assessment", 100)

    # 2. Insufficient bond (< 10% of 1000 = 100)
    with pytest.raises(ValueError, match="insufficient"):
        sim.appeal_verdict(fnd, oid, "Re-sequencing with PacBio HiFi shows 99% accuracy", 50)

    # 3. Successful dispute with 100 bond (10%)
    sim.appeal_verdict(fnd, oid, "Re-sequencing with PacBio HiFi shows 99% accuracy", 100)
    assert sim.orders[oid]["status"] == 7  # STATUS_DISPUTED
    assert sim.orders[oid]["dispute_initiator"] == fnd
    assert sim.orders[oid]["dispute_bond"] == 100
    assert sim.total_bio_locked == 1100  # 1000 escrow + 100 bond


def test_researcher_cannot_fulfill_own_order():
    """Verify Sybil defense: Researcher is prohibited from claiming their own bio order."""
    sim = MockAgentBioSimulator()
    res = "0xresearcher"
    oid = sim.order_synthesis(res, "Novel synthetic promoter for mammalian vectors", "https://spec.com/seq", 1000, 200)

    with pytest.raises(ValueError, match="cannot fulfill and synthesize their own"):
        sim.submit_synthesis_proof(res, oid, "https://qc.com/report")


def test_cancel_or_reclaim_rules():
    """Verify cancellation permissions and expiration safeguards."""
    sim = MockAgentBioSimulator()
    res = "0xresearcher"
    oid = sim.order_synthesis(res, "Enzymatic biosensor for heavy metal detection", "https://spec.com/seq", 50, 400)

    # Cannot cancel before expiration
    with pytest.raises(ValueError, match="has not yet expired"):
        sim.cancel_or_reclaim(res, oid)

    # Advance beyond expiration block
    sim.order_counter += 60
    bal_before = sim.balances[res]
    sim.cancel_or_reclaim(res, oid)

    assert sim.orders[oid]["status"] == 6  # STATUS_CANCELLED
    assert sim.balances[res] == bal_before + 400
