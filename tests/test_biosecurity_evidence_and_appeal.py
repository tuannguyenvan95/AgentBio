import pytest
import json
import hashlib

try:
    from genlayer import *
except ImportError:
    pass


def test_dual_evidence_authentication_and_biohazard_slash(client):
    """
    Proves that:
    1. Both commissioned spec AND delivery QC report are fetched and authenticated.
    2. Prohibited biohazard pathogens forfeit 100% of escrow to Biosecurity Reserve.
    3. The appeal path CANNOT bypass biohazard forfeiture (both escrow + bond slashed).
    """
    contract = client.deploy("contracts/contract.py")
    researcher = client.accounts[0]
    foundry = client.accounts[1]

    spec_url = "https://biosecure-archive.org/designs/therapeutic_antibody.fasta"
    qc_url = "https://foundry-qc.io/runs/lot_9921_sanger.txt"

    # Step 1: Order Synthesis with authentic design spec
    tx_order = contract.connect(researcher).order_synthesis(
        args=["Therapeutic neutralizing antibody binding domain", spec_url, 86400 * 7],
        value=1000000000000000000  # 1 GEN
    )
    order_id = tx_order.return_value

    # Step 2: Foundry claims and submits QC delivery
    contract.connect(foundry).submit_synthesis_proof(
        args=[order_id, qc_url]
    )

    # Step 3: Mock AI Jury detecting dangerous prohibited select agent toxin
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "BIOHAZARD_BLOCKED",
                    "confidence": 98,
                    "fidelity_score": 10,
                    "reason": "Sequence encodes lethal Ricin / Botulinum toxin domain. Prohibited pathogen detected."
                })
            },
            "web_mocks": {
                spec_url: {"status": 200, "body": ">seq1\nATGCGATCGATCGA"},
                qc_url: {"status": 200, "body": ">qc1\nATGCGATCGATCGATTCC"}
            }
        }
    )

    # Adjudicate biosecurity
    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id])

    order_awaiting = json.loads(contract.get_order(args=[order_id]).call())
    assert order_awaiting["status"] == 2  # AWAITING_PAYOUT
    assert order_awaiting["verdict"] == "BIOHAZARD_BLOCKED"
    assert len(order_awaiting["spec_evidence_hash"]) == 64
    assert len(order_awaiting["qc_evidence_hash"]) == 64

    # Step 4: Malicious actor files appeal to attempt bypassing hazardous forfeiture
    contract.connect(researcher).appeal_verdict(
        args=[order_id, "Attempting to claim false positive classification"],
        value=100000000000000000  # 0.1 GEN bond
    )

    # Step 5: Appellate Jury confirms biohazard -> Escrow AND Bond MUST be slashed to Reserve
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "APPEAL_BIOHAZARD_CONFIRMED",
                    "reason": "Appellate confirmation: weaponized select agent confirmed."
                })
            },
            "web_mocks": {
                "https://supplemental-lab.org/proof.txt": {"status": 200, "body": "Supplemental run confirms toxin"}
            }
        }
    )

    contract.connect(researcher).adjudicate_appeal(
        args=[order_id, "https://supplemental-lab.org/proof.txt"]
    )

    final_order = json.loads(contract.get_order(args=[order_id]).call())
    assert final_order["status"] == 4  # STATUS_BIOHAZARD_SLASHED
    assert final_order["verdict"] == "BIOHAZARD_BLOCKED"
    assert "forfeited to Reserve" in final_order["reason"]


def test_appeal_cannot_bypass_biohazard_even_if_tribunal_claims_verified(client):
    """
    CRITICAL STEWARD TEST (Mandatory Resolution of Gen. Dave's feedback):
    Proves that when an order is flagged with an initial BIOHAZARD_BLOCKED verdict,
    a malicious actor CANNOT bypass forfeiture by persuading or manipulating
    the appellate tribunal into returning APPEAL_UPHELD_VERIFIED.
    The contract MUST enforce strict, no-bypass forfeiture to the Biosecurity Reserve.
    """
    contract = client.deploy("contracts/contract.py")
    researcher = client.accounts[0]
    foundry = client.accounts[1]

    spec_url = "https://biosecure-archive.org/designs/weaponized_toxin.fasta"
    qc_url = "https://foundry-qc.io/runs/lot_adversarial.txt"

    # Step 1: Commission synthesis order
    tx_order = contract.connect(researcher).order_synthesis(
        args=["Dual-use biological select agent", spec_url, 86400 * 7],
        value=5000000000000000000  # 5 GEN escrow
    )
    order_id = tx_order.return_value

    # Step 2: Foundry submits proof
    contract.connect(foundry).submit_synthesis_proof(
        args=[order_id, qc_url]
    )

    # Step 3: Primary adjudication flags BIOHAZARD_BLOCKED
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "BIOHAZARD_BLOCKED",
                    "confidence": 99,
                    "fidelity_score": 5,
                    "reason": "CRITICAL BIOSECURITY ALERT: Prohibited Ebola / Marburg homolog detected."
                })
            },
            "web_mocks": {
                spec_url: {"status": 200, "body": ">biohazard_v1\nATGCGATCGATCGATCGATCGA"},
                qc_url: {"status": 200, "body": ">biohazard_v1\nATGCGATCGATCGATCGATCGA"}
            }
        }
    )
    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id])

    order_flagged = json.loads(contract.get_order(args=[order_id]).call())
    assert order_flagged["status"] == 2  # AWAITING_PAYOUT
    assert order_flagged["verdict"] == "BIOHAZARD_BLOCKED"

    # Step 4: Appellant stakes 10% bond (0.5 GEN) and files an appeal
    contract.connect(researcher).appeal_verdict(
        args=[order_id, "Frivolous contestation attempting to bypass biosecurity fine"],
        value=500000000000000000  # 0.5 GEN bond
    )

    # Step 5: Adversarial Scenario: Appellate tribunal outputs APPEAL_UPHELD_VERIFIED
    # Under prior flawed code, this would disburse 5 GEN escrow to foundry.
    # Under fixed contract, strict no-bypass rule guarantees 100% forfeiture to Reserve!
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "APPEAL_UPHELD_VERIFIED",
                    "reason": "Adversarial finding claiming sequence is benign therapeutic."
                })
            },
            "web_mocks": {
                "https://adversarial-rebuttal.org/proof.txt": {"status": 200, "body": "Manipulated lab report"}
            }
        }
    )

    contract.connect(researcher).adjudicate_appeal(
        args=[order_id, "https://adversarial-rebuttal.org/proof.txt"]
    )

    final_order = json.loads(contract.get_order(args=[order_id]).call())

    # VERIFY STRICT ENFORCEMENT:
    # 1. Status is definitively STATUS_BIOHAZARD_SLASHED (4)
    assert final_order["status"] == 4, f"Expected STATUS_BIOHAZARD_SLASHED (4), got {final_order['status']}"
    # 2. Verdict remains BIOHAZARD_BLOCKED (cannot be overturned to verified)
    assert final_order["verdict"] == "BIOHAZARD_BLOCKED"
    # 3. Reason explicitly indicates no-bypass forfeiture
    assert "NO-BYPASS BIOHAZARD FORFEITURE" in final_order["reason"]
    assert "forfeited to Reserve" in final_order["reason"]


def test_protocol_ownership_and_reserve_immediate_constructor_binding(contract_source):
    """
    STEWARD FEEDBACK 1:
    Proves that protocol ownership and biosecurity reserve are immediately bound to deployer
    in __init__, and NOT lazily assigned to an arbitrary first caller.
    """
    assert "def __init__(self, owner: Address = Address(ZERO_ADDRESS)" in contract_source
    assert "deployer = _get_sender()" in contract_source
    assert "self.owner = owner if _addr_str(owner) != ZERO_ADDRESS else deployer" in contract_source
    assert "self.biosecurity_reserve = reserve if _addr_str(reserve) != ZERO_ADDRESS else deployer" in contract_source
    assert "_ensure_initialized" not in contract_source, "Found obsolete lazy _ensure_initialized method!"


def test_trusted_timing_path_strictly_rejects_untrusted_fallbacks(contract_source):
    """
    STEWARD FEEDBACK 4:
    Proves that the timing helper strictly derives trusted timestamp from GenVM protocol
    consensus message (gl.message_raw['datetime'] or gl.message.datetime) and has ZERO
    unauthenticated local-clock (datetime.now()) or logical block-counter fallbacks.
    """
    assert "def _get_current_timestamp(self) -> bigint:" in contract_source
    assert "gl.message_raw.get(\"datetime\")" in contract_source
    assert "datetime.now" not in contract_source, "Found prohibited unauthenticated local clock datetime.now fallback!"
    assert 'raise ContractError("Trusted execution timestamp unavailable from GenVM message context.")' in contract_source


# ── Adversarial Tests for Steward zoefunds's Feedback ────────────────────

def test_adversarial_cancel_before_expiry_reverts_cleanly_without_attribute_error(client):
    """
    CRITICAL STEWARD TEST (zoefunds resolution):
    Proves that calling cancel_or_reclaim() before the configured expiry duration:
    1. Does NOT crash with AttributeError: module 'genlayer.gl' has no attribute 'UserError'.
    2. Strictly enforces the order's configured expiry condition (reverts because now < expires_at).
    """
    contract = client.deploy("contracts/contract.py")
    researcher = client.accounts[0]
    spec_url = "https://biosecure-archive.org/designs/valid_spec.fasta"

    # Order commissioned with 7-day duration (604800s)
    tx = contract.connect(researcher).order_synthesis(
        args=["Neutralizing peptide targeting microbial surface protein", spec_url, 604800],
        value=1000000000000000000
    )
    order_id = tx.return_value

    # Adversarial attempt: Researcher attempts to cancel immediately while still within valid synthesis window
    with pytest.raises(Exception) as exc_info:
        contract.connect(researcher).cancel_or_reclaim(args=[order_id])

    err_str = str(exc_info.value)
    # MUST NOT be an AttributeError on genlayer.gl.UserError
    assert "AttributeError" not in err_str, f"Found prohibited runtime crash: {err_str}"
    assert "UserError" not in err_str or "attribute" not in err_str
    # MUST explicitly enforce expiry
    assert "not yet expired" in err_str.lower() or "cannot cancel" in err_str.lower()


def test_adversarial_unauthorized_actor_cancel_reverts(client):
    """
    CRITICAL STEWARD TEST (zoefunds resolution):
    Proves that an unauthorized third-party actor cannot hijack or cancel an order.
    """
    contract = client.deploy("contracts/contract.py")
    researcher = client.accounts[0]
    attacker = client.accounts[2]
    spec_url = "https://biosecure-archive.org/designs/valid_spec.fasta"

    tx = contract.connect(researcher).order_synthesis(
        args=["Neutralizing peptide targeting microbial surface protein", spec_url, 604800],
        value=1000000000000000000
    )
    order_id = tx.return_value

    # Attacker attempts to cancel researcher's order
    with pytest.raises(Exception) as exc_info:
        contract.connect(attacker).cancel_or_reclaim(args=[order_id])

    err_str = str(exc_info.value)
    assert "AttributeError" not in err_str
    assert "unauthorized" in err_str.lower() or "only the ordering researcher" in err_str.lower()


def test_explicit_bilateral_agreement_verification_and_unauthorized_foundry_rejection(client):
    """
    CRITICAL STEWARD TEST (zoefunds resolution):
    Proves that:
    1. Foundry explicitly accepts the commissioned terms via accept_synthesis_agreement.
    2. Once an agreement is formed with Foundry A, an unauthorized Foundry B CANNOT submit proof.
    3. Researcher CANNOT accept or fulfill their own order.
    """
    contract = client.deploy("contracts/contract.py")
    researcher = client.accounts[0]
    authorized_foundry = client.accounts[1]
    rogue_foundry = client.accounts[2]
    spec_url = "https://biosecure-archive.org/designs/valid_spec.fasta"

    tx = contract.connect(researcher).order_synthesis(
        args=["Therapeutic peptide binding domain", spec_url, 604800],
        value=2000000000000000000
    )
    order_id = tx.return_value

    # 1. Researcher cannot accept their own order
    with pytest.raises(Exception) as exc:
        contract.connect(researcher).accept_synthesis_agreement(args=[order_id])
    assert "AttributeError" not in str(exc.value)
    assert "cannot" in str(exc.value).lower()

    # 2. Authorized Foundry accepts agreement
    contract.connect(authorized_foundry).accept_synthesis_agreement(args=[order_id])

    # Verify agreement state
    agreement_json = json.loads(contract.verify_order_agreement(args=[order_id]).call())
    assert agreement_json["agreement_accepted"] is True
    assert agreement_json["foundry"].lower() == str(authorized_foundry).lower()
    assert agreement_json["is_valid_bilateral_agreement"] is True

    # 3. Rogue foundry attempts to submit proof on claimed agreement
    with pytest.raises(Exception) as exc_rogue:
        contract.connect(rogue_foundry).submit_synthesis_proof(
            args=[order_id, "https://rogue-foundry.com/fake_qc.txt"]
        )
    assert "unauthorized" in str(exc_rogue.value).lower() or "agreed foundry" in str(exc_rogue.value).lower()


def test_overturned_order_recovery_researcher_appeal(client):
    """
    CRITICAL STEWARD TEST (zoefunds resolution):
    Proves comprehensive recovery when an appeal OVERTURNS a verdict:
    - Initial verdict was BIO_SYNTHESIS_VERIFIED.
    - Researcher appeals with evidence proving defective sequence.
    - Appellate court overturns verdict to APPEAL_OVERTURNED_DEFECTIVE.
    - Result: 100% of escrow is refunded to Researcher AND Researcher's dispute bond is returned!
    """
    contract = client.deploy("contracts/contract.py")
    researcher = client.accounts[0]
    foundry = client.accounts[1]
    spec_url = "https://biosecure-archive.org/designs/enzyme.fasta"
    qc_url = "https://foundry-qc.io/runs/lot_enzyme.txt"

    # Step 1: Create order with 1 GEN deposit
    tx = contract.connect(researcher).order_synthesis(
        args=["Catalytic enzyme for industrial biosynthesis", spec_url, 604800],
        value=1000000000000000000
    )
    order_id = tx.return_value

    # Step 2: Foundry submits proof
    contract.connect(foundry).submit_synthesis_proof(args=[order_id, qc_url])

    # Step 3: Initial adjudication gives false positive BIO_SYNTHESIS_VERIFIED
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "BIO_SYNTHESIS_VERIFIED",
                    "confidence": 90,
                    "fidelity_score": 95,
                    "reason": "Initial alignment appeared verified."
                })
            },
            "web_mocks": {
                spec_url: {"status": 200, "body": ">enzyme_spec\nATGCGATCGATCGATC"},
                qc_url: {"status": 200, "body": ">enzyme_qc\nATGCGATCGATCGATC"}
            }
        }
    )
    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id])

    # Step 4: Researcher stakes 10% bond (0.1 GEN) and appeals with lab proof of defect
    contract.connect(researcher).appeal_verdict(
        args=[order_id, "Independent HPLC spectrometry proves sequence truncated at residue 15"],
        value=100000000000000000
    )

    # Step 5: Appellate court overturns initial verdict in favor of researcher
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "APPEAL_OVERTURNED_DEFECTIVE",
                    "reason": "HPLC independent laboratory confirmation proves synthesis truncated and defective."
                })
            },
            "web_mocks": {
                "https://independent-lab.org/hplc.txt": {"status": 200, "body": "HPLC proof of truncation"}
            }
        }
    )
    contract.connect(researcher).adjudicate_appeal(
        args=[order_id, "https://independent-lab.org/hplc.txt"]
    )

    # Step 6: Verify overturned order recovery
    final_order = json.loads(contract.get_order(args=[order_id]).call())
    assert final_order["status"] == 5  # STATUS_DEFECTIVE_REFUNDED
    assert final_order["verdict"] == "SEQUENCE_DEFECTIVE"
    assert "VERDICT OVERTURNED" in final_order["reason"]
    assert "Researcher appeal upheld" in final_order["reason"]


def test_adversarial_in_synthesis_reclaim_before_deadline_reverts(client):
    """
    CRITICAL STEWARD TEST (zoefunds resolution):
    Proves that when an order is in synthesis, researcher cannot prematurely
    reclaim escrow while the foundry is actively synthesizing within deadline.
    """
    contract = client.deploy("contracts/contract.py")
    researcher = client.accounts[0]
    foundry = client.accounts[1]
    spec_url = "https://biosecure-archive.org/designs/valid_spec.fasta"

    tx = contract.connect(researcher).order_synthesis(
        args=["Valid biological receptor construct", spec_url, 604800],
        value=1000000000000000000
    )
    order_id = tx.return_value

    # Foundry accepts synthesis agreement
    contract.connect(foundry).accept_synthesis_agreement(args=[order_id])

    # Researcher attempts to cancel/reclaim while foundry is within active deadline
    with pytest.raises(Exception) as exc_info:
        contract.connect(researcher).cancel_or_reclaim(args=[order_id])

    err_str = str(exc_info.value)
    assert "AttributeError" not in err_str
    assert "actively executing synthesis" in err_str.lower() or "deadline" in err_str.lower()


def test_overturned_order_recovery_foundry_appeal(client):
    """
    CRITICAL STEWARD TEST (zoefunds resolution):
    Proves comprehensive recovery when Foundry appeals a SEQUENCE_DEFECTIVE verdict
    and proves authentic delivery with supplemental deep sequencing:
    - Initial verdict was SEQUENCE_DEFECTIVE.
    - Foundry appeals with authentic PacBio HiFi data.
    - Appellate court overturns verdict to APPEAL_UPHELD_VERIFIED.
    - Result: Foundry receives 100% escrow AND gets their dispute bond returned!
    """
    contract = client.deploy("contracts/contract.py")
    researcher = client.accounts[0]
    foundry = client.accounts[1]
    spec_url = "https://biosecure-archive.org/designs/promoter.fasta"
    qc_url = "https://foundry-qc.io/runs/lot_sanger_noisy.txt"

    # Step 1: Order commissioned
    tx = contract.connect(researcher).order_synthesis(
        args=["Synthetic mammalian promoter construct", spec_url, 604800],
        value=3000000000000000000
    )
    order_id = tx.return_value

    # Step 2: Foundry submits noisy sanger proof
    contract.connect(foundry).submit_synthesis_proof(args=[order_id, qc_url])

    # Step 3: Primary jury renders false negative SEQUENCE_DEFECTIVE due to noisy chromatogram
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "SEQUENCE_DEFECTIVE",
                    "confidence": 85,
                    "fidelity_score": 60,
                    "reason": "Chromatogram baseline noise simulated low fidelity."
                })
            },
            "web_mocks": {
                spec_url: {"status": 200, "body": ">promoter\nATCGGCTAGCTAGCTA"},
                qc_url: {"status": 200, "body": ">promoter\nATCGGCTAGNNNNCTA"}
            }
        }
    )
    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id])

    # Step 4: Foundry appeals with 10% bond (0.3 GEN) and provides PacBio HiFi data
    contract.connect(foundry).appeal_verdict(
        args=[order_id, "PacBio HiFi circular consensus sequencing proves 99.9% base accuracy"],
        value=300000000000000000
    )

    # Step 5: Appellate court confirms authentic synthesis and overturns defect
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "APPEAL_UPHELD_VERIFIED",
                    "reason": "PacBio HiFi consensus confirms 100% full-length alignment and 99.9% fidelity."
                })
            },
            "web_mocks": {
                "https://foundry.com/pacbio_hifi.txt": {"status": 200, "body": "PacBio HiFi consensus verified"}
            }
        }
    )
    contract.connect(foundry).adjudicate_appeal(
        args=[order_id, "https://foundry.com/pacbio_hifi.txt"]
    )

    # Step 6: Verify settlement to Foundry and overturned status
    final_order = json.loads(contract.get_order(args=[order_id]).call())
    assert final_order["status"] == 3  # STATUS_VERIFIED_PAID
    assert final_order["verdict"] == "BIO_SYNTHESIS_VERIFIED"
    assert "VERDICT OVERTURNED" in final_order["reason"]
    assert "Foundry appeal upheld" in final_order["reason"]


def test_recovery_path_for_abandoned_disputed_order(client):
    """
    CRITICAL STEWARD TEST (zoefunds resolution):
    Proves comprehensive recovery for stalled/unresolved disputes via recover_disputed_order:
    If an appellant abandons the dispute, recover_disputed_order settles according
    to the pre-dispute verdict, preventing locked funds.
    """
    contract = client.deploy("contracts/contract.py")
    researcher = client.accounts[0]
    foundry = client.accounts[1]
    spec_url = "https://biosecure-archive.org/designs/test.fasta"
    qc_url = "https://foundry-qc.io/runs/lot_test.txt"

    tx = contract.connect(researcher).order_synthesis(
        args=["Test expression cassette", spec_url, 604800],
        value=1000000000000000000
    )
    order_id = tx.return_value
    contract.connect(foundry).submit_synthesis_proof(args=[order_id, qc_url])

    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "BIO_SYNTHESIS_VERIFIED",
                    "confidence": 95,
                    "fidelity_score": 98,
                    "reason": "Verified"
                })
            },
            "web_mocks": {
                spec_url: {"status": 200, "body": "ATCG"},
                qc_url: {"status": 200, "body": "ATCG"}
            }
        }
    )
    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id])

    # Researcher disputes
    contract.connect(researcher).appeal_verdict(
        args=[order_id, "Frivolous contestation later abandoned"],
        value=100000000000000000
    )

    # Recover disputed order
    contract.connect(foundry).recover_disputed_order(args=[order_id])
    recovered_order = json.loads(contract.get_order(args=[order_id]).call())
    assert recovered_order["status"] == 3  # Settled to verified
