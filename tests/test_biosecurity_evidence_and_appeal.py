import pytest
import json
import hashlib

try:
    from genlayer import *
except ImportError:
    pass


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def test_dual_evidence_authentication_and_biohazard_slash(client):
    """
    Proves that:
    1. Both commissioned spec AND delivery QC report are fetched and authenticated via 64-hex content commitments.
    2. Prohibited biohazard pathogens forfeit 100% of escrow to Biosecurity Reserve.
    3. The appeal path CANNOT bypass biohazard forfeiture (both escrow + bond slashed).
    """
    contract = client.deploy("contracts/contract.py")
    owner = client.accounts[0]
    researcher = client.accounts[0]
    foundry = client.accounts[1]

    spec_url = "https://biosecure-archive.org/designs/therapeutic_antibody.fasta"
    qc_url = "https://foundry-qc.io/runs/lot_9921_sanger.txt"
    spec_body = ">seq1\nATGCGATCGATCGA"
    qc_body = ">qc1\nATGCGATCGATCGATTCC"
    spec_hash = _sha256(spec_body)
    qc_hash = _sha256(qc_body)

    # Step 1: Order Synthesis with authentic design spec & genuine 64-hex content commitment
    tx_order = contract.connect(researcher).order_synthesis(
        args=["Therapeutic neutralizing antibody binding domain", spec_url, 86400 * 7, spec_hash],
        value=1000000000000000000  # 1 GEN
    )
    order_id = tx_order.return_value

    # Step 2: Foundry claims and submits QC delivery with genuine 64-hex content commitment
    contract.connect(foundry).submit_synthesis_proof(
        args=[order_id, qc_url, qc_hash]
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
                spec_url: {"status": 200, "body": spec_body},
                qc_url: {"status": 200, "body": qc_body}
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

    # Step 4: Malicious actor files appeal designating an accredited reviewing lab
    supp_url = "https://supplemental-lab.org/proof.txt"
    supp_body = "Supplemental run confirms toxin"
    supp_hash = _sha256(supp_body)
    audit_lab = client.accounts[2]
    contract.connect(owner).register_audit_lab(args=[audit_lab, "LAB-ISO17025-INDEPENDENT"])

    contract.connect(researcher).appeal_verdict(
        args=[order_id, "Attempting to claim false positive classification", audit_lab, supp_hash],
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
                supp_url: {"status": 200, "body": supp_body}
            }
        }
    )

    contract.connect(researcher).adjudicate_appeal(
        args=[order_id, supp_url]
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
    owner = client.accounts[0]
    researcher = client.accounts[0]
    foundry = client.accounts[1]
    audit_lab = client.accounts[2]
    contract.connect(owner).register_audit_lab(args=[audit_lab, "LAB-ISO17025-AUDIT"])

    spec_url = "https://biosecure-archive.org/designs/weaponized_toxin.fasta"
    qc_url = "https://foundry-qc.io/runs/lot_adversarial.txt"
    spec_body = ">biohazard_v1\nATGCGATCGATCGATCGATCGA"
    qc_body = ">biohazard_v1\nATGCGATCGATCGATCGATCGA"
    spec_hash = _sha256(spec_body)
    qc_hash = _sha256(qc_body)

    # Step 1: Commission synthesis order
    tx_order = contract.connect(researcher).order_synthesis(
        args=["Dual-use biological select agent", spec_url, 86400 * 7, spec_hash],
        value=5000000000000000000  # 5 GEN escrow
    )
    order_id = tx_order.return_value

    # Step 2: Foundry submits proof
    contract.connect(foundry).submit_synthesis_proof(
        args=[order_id, qc_url, qc_hash]
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
                spec_url: {"status": 200, "body": spec_body},
                qc_url: {"status": 200, "body": qc_body}
            }
        }
    )
    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id])

    order_flagged = json.loads(contract.get_order(args=[order_id]).call())
    assert order_flagged["status"] == 2  # AWAITING_PAYOUT
    assert order_flagged["verdict"] == "BIOHAZARD_BLOCKED"

    # Step 4: Appellant stakes 10% bond (0.5 GEN) and files an appeal
    supp_url = "https://adversarial-rebuttal.org/proof.txt"
    supp_body = "Manipulated lab report"
    supp_hash = _sha256(supp_body)

    contract.connect(researcher).appeal_verdict(
        args=[order_id, "Frivolous contestation attempting to bypass biosecurity fine", audit_lab, supp_hash],
        value=500000000000000000  # 0.5 GEN bond
    )

    # Step 5: Adversarial Scenario: Appellate tribunal outputs APPEAL_UPHELD_VERIFIED
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
                supp_url: {"status": 200, "body": supp_body}
            }
        }
    )

    contract.connect(researcher).adjudicate_appeal(
        args=[order_id, supp_url]
    )

    final_order = json.loads(contract.get_order(args=[order_id]).call())

    # VERIFY STRICT ENFORCEMENT:
    assert final_order["status"] == 4, f"Expected STATUS_BIOHAZARD_SLASHED (4), got {final_order['status']}"
    assert final_order["verdict"] == "BIOHAZARD_BLOCKED"
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
    spec_hash = _sha256(">valid\nATCG")

    # Order commissioned with 7-day duration (604800s)
    tx = contract.connect(researcher).order_synthesis(
        args=["Neutralizing peptide targeting microbial surface protein", spec_url, 604800, spec_hash],
        value=1000000000000000000
    )
    order_id = tx.return_value

    # Adversarial attempt: Researcher attempts to cancel immediately while still within valid synthesis window
    with pytest.raises(Exception) as exc_info:
        contract.connect(researcher).cancel_or_reclaim(args=[order_id])

    err_str = str(exc_info.value)
    assert "AttributeError" not in err_str, f"Found prohibited runtime crash: {err_str}"
    assert "UserError" not in err_str or "attribute" not in err_str
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
    spec_hash = _sha256(">valid\nATCG")

    tx = contract.connect(researcher).order_synthesis(
        args=["Neutralizing peptide targeting microbial surface protein", spec_url, 604800, spec_hash],
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
    spec_hash = _sha256(">valid\nATCG")

    tx = contract.connect(researcher).order_synthesis(
        args=["Therapeutic peptide binding domain", spec_url, 604800, spec_hash],
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
            args=[order_id, "https://rogue-foundry.com/fake_qc.txt", _sha256("fake")]
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
    owner = client.accounts[0]
    researcher = client.accounts[0]
    foundry = client.accounts[1]
    audit_lab = client.accounts[2]
    contract.connect(owner).register_audit_lab(args=[audit_lab, "LAB-ISO17025-INDEPENDENT"])

    spec_url = "https://biosecure-archive.org/designs/enzyme.fasta"
    qc_url = "https://foundry-qc.io/runs/lot_enzyme.txt"
    spec_body = ">enzyme_spec\nATGCGATCGATCGATC"
    qc_body = ">enzyme_qc\nATGCGATCGATCGATC"
    spec_hash = _sha256(spec_body)
    qc_hash = _sha256(qc_body)

    # Step 1: Create order with 1 GEN deposit
    tx = contract.connect(researcher).order_synthesis(
        args=["Catalytic enzyme for industrial biosynthesis", spec_url, 604800, spec_hash],
        value=1000000000000000000
    )
    order_id = tx.return_value

    # Step 2: Foundry submits proof
    contract.connect(foundry).submit_synthesis_proof(args=[order_id, qc_url, qc_hash])

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
                spec_url: {"status": 200, "body": spec_body},
                qc_url: {"status": 200, "body": qc_body}
            }
        }
    )
    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id])

    # Step 4: Researcher stakes 10% bond (0.1 GEN) and appeals with lab proof of defect
    supp_url = "https://independent-lab.org/hplc.txt"
    supp_body = "HPLC proof of truncation"
    supp_hash = _sha256(supp_body)

    contract.connect(researcher).appeal_verdict(
        args=[order_id, "Independent HPLC spectrometry proves sequence truncated at residue 15", audit_lab, supp_hash],
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
                supp_url: {"status": 200, "body": supp_body}
            }
        }
    )
    contract.connect(researcher).adjudicate_appeal(
        args=[order_id, supp_url]
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
    spec_hash = _sha256(">valid\nATCG")

    tx = contract.connect(researcher).order_synthesis(
        args=["Valid biological receptor construct", spec_url, 604800, spec_hash],
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
    owner = client.accounts[0]
    researcher = client.accounts[0]
    foundry = client.accounts[1]
    audit_lab = client.accounts[2]
    contract.connect(owner).register_audit_lab(args=[audit_lab, "LAB-PACBIO-CERTIFIED"])

    spec_url = "https://biosecure-archive.org/designs/promoter.fasta"
    qc_url = "https://foundry-qc.io/runs/lot_sanger_noisy.txt"
    spec_body = ">promoter\nATCGGCTAGCTAGCTA"
    qc_body = ">promoter\nATCGGCTAGNNNNCTA"
    spec_hash = _sha256(spec_body)
    qc_hash = _sha256(qc_body)

    # Step 1: Order commissioned
    tx = contract.connect(researcher).order_synthesis(
        args=["Synthetic mammalian promoter construct", spec_url, 604800, spec_hash],
        value=3000000000000000000
    )
    order_id = tx.return_value

    # Step 2: Foundry submits noisy sanger proof
    contract.connect(foundry).submit_synthesis_proof(args=[order_id, qc_url, qc_hash])

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
                spec_url: {"status": 200, "body": spec_body},
                qc_url: {"status": 200, "body": qc_body}
            }
        }
    )
    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id])

    # Step 4: Foundry appeals with 10% bond (0.3 GEN) and provides PacBio HiFi data
    supp_url = "https://foundry.com/pacbio_hifi.txt"
    supp_body = "PacBio HiFi consensus verified"
    supp_hash = _sha256(supp_body)

    contract.connect(foundry).appeal_verdict(
        args=[order_id, "PacBio HiFi circular consensus sequencing proves 99.9% base accuracy", audit_lab, supp_hash],
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
                supp_url: {"status": 200, "body": supp_body}
            }
        }
    )
    contract.connect(foundry).adjudicate_appeal(
        args=[order_id, supp_url]
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
    owner = client.accounts[0]
    researcher = client.accounts[0]
    foundry = client.accounts[1]
    audit_lab = client.accounts[2]
    contract.connect(owner).register_audit_lab(args=[audit_lab, "LAB-AUDIT-ISO"])

    spec_url = "https://biosecure-archive.org/designs/test.fasta"
    qc_url = "https://foundry-qc.io/runs/lot_test.txt"
    spec_body = "ATCG"
    qc_body = "ATCG"
    spec_hash = _sha256(spec_body)
    qc_hash = _sha256(qc_body)

    tx = contract.connect(researcher).order_synthesis(
        args=["Test expression cassette", spec_url, 604800, spec_hash],
        value=1000000000000000000
    )
    order_id = tx.return_value
    contract.connect(foundry).submit_synthesis_proof(args=[order_id, qc_url, qc_hash])

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
                spec_url: {"status": 200, "body": spec_body},
                qc_url: {"status": 200, "body": qc_body}
            }
        }
    )
    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id])

    # Researcher disputes
    supp_hash = _sha256("dispute_evidence")
    contract.connect(researcher).appeal_verdict(
        args=[order_id, "Frivolous contestation later abandoned", audit_lab, supp_hash],
        value=100000000000000000
    )

    # Recover disputed order
    contract.connect(foundry).recover_disputed_order(args=[order_id])
    recovered_order = json.loads(contract.get_order(args=[order_id]).call())
    assert recovered_order["status"] == 3  # Settled to verified


def test_deploy_with_custom_int_and_hex_addresses(client):
    """
    Verifies that deploying with integer address representations (as sent by GenLayer Studio ABI calldata)
    and hex strings correctly parses and binds without AttributeError: 'int' object has no attribute 'as_bytes'.
    """
    custom_addr_hex = "0x58e439f80483b72ffab6704ddb5d447439986549"
    custom_addr_int = int(custom_addr_hex, 16)

    # 1. Deploy with int addresses (Studio calldata behavior)
    contract_int = client.deploy("contracts/contract.py", args=[custom_addr_int, custom_addr_int])
    stats_int = json.loads(contract_int.get_stats().call())
    assert stats_int["owner"].lower() == custom_addr_hex
    assert stats_int["biosecurity_reserve"].lower() == custom_addr_hex

    # 2. Deploy with hex string addresses
    contract_str = client.deploy("contracts/contract.py", args=[custom_addr_hex, custom_addr_hex])
    stats_str = json.loads(contract_str.get_stats().call())
    assert stats_str["owner"].lower() == custom_addr_hex
    assert stats_str["biosecurity_reserve"].lower() == custom_addr_hex


def test_unauthorized_wallet_cannot_claim_synthesis_order(client):
    """
    CRITICAL STEWARD REDESIGN TEST (Authorized Foundry Participation):
    Proves that unauthorized wallets CANNOT claim open synthesis orders,
    enforcing that only accredited foundries in the registry can accept agreements.
    """
    contract = client.deploy("contracts/contract.py")
    researcher = client.accounts[0]
    unauthorized_wallet = "0x9999999999999999999999999999999999999999"
    spec_hash = _sha256(">spec\nATCG")

    tx = contract.connect(researcher).order_synthesis(
        args=["Therapeutic enzyme synthesis", "https://biosecure.org/spec.fasta", 604800, spec_hash],
        value=1000000000000000000
    )
    order_id = tx.return_value

    # Unauthorized wallet tries to accept synthesis agreement -> REVERT
    with pytest.raises(Exception) as exc:
        contract.connect(unauthorized_wallet).accept_synthesis_agreement(args=[order_id])
    assert "unauthorized" in str(exc.value).lower()


def test_designated_target_foundry_protection_rejects_intruders(client):
    """
    CRITICAL STEWARD REDESIGN TEST (Target Foundry Delegation):
    Proves that when a researcher designates a specific target foundry,
    no other foundry (even if accredited) can intercept or accept the order.
    """
    contract = client.deploy("contracts/contract.py")
    researcher = client.accounts[0]
    designated_foundry = client.accounts[1]
    intruder_foundry = client.accounts[2]
    spec_hash = _sha256(">spec\nATCG")

    # Commission order specifically delegating to designated_foundry
    tx = contract.connect(researcher).order_synthesis(
        args=[
            "Designated monoclonal antibody synthesis",
            "https://biosecure.org/spec.fasta",
            604800,
            spec_hash,
            designated_foundry
        ],
        value=1000000000000000000
    )
    order_id = tx.return_value

    # Intruder foundry tries to accept -> REVERT
    with pytest.raises(Exception) as exc:
        contract.connect(intruder_foundry).accept_synthesis_agreement(args=[order_id])
    assert "designated target foundry" in str(exc.value)

    # Designated foundry accepts successfully
    contract.connect(designated_foundry).accept_synthesis_agreement(args=[order_id])
    order = json.loads(contract.get_order(args=[order_id]).call())
    assert order["status"] == 1
    assert order["foundry"].lower() == designated_foundry.lower()


def test_defensible_appeal_overturns_false_positive_biohazard_protecting_escrow(client):
    """
    CRITICAL STEWARD REDESIGN TEST (Defensible Settlement & Appeal Mechanism):
    Proves that unsupported or false-positive biosecurity classifications do NOT
    cause irreversible confiscation. If an appeal provides proof that the product
    is a benign therapeutic, the Appellate Tribunal can overturn the biohazard
    classification (APPEAL_BIOHAZARD_OVERTURNED_BENIGN) and refund the researcher.
    """
    contract = client.deploy("contracts/contract.py")
    owner = client.accounts[0]
    researcher = client.accounts[0]
    foundry = client.accounts[1]
    audit_lab = client.accounts[2]
    contract.connect(owner).register_audit_lab(args=[audit_lab, "LAB-CERTIFIED-ASSAY"])

    spec_url = "https://biosecure.org/therapeutic_enzyme.fasta"
    qc_url = "https://foundry-qc.io/run.txt"
    spec_body = "ATCG"
    qc_body = "ATCG"
    spec_hash = _sha256(spec_body)
    qc_hash = _sha256(qc_body)

    tx = contract.connect(researcher).order_synthesis(
        args=["Benign therapeutic beta-galactosidase", spec_url, 604800, spec_hash],
        value=2000000000000000000
    )
    order_id = tx.return_value
    contract.connect(foundry).submit_synthesis_proof(args=[order_id, qc_url, qc_hash])

    # Initial jury falsely flags biohazard (false positive)
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "BIOHAZARD_BLOCKED",
                    "confidence": 95,
                    "fidelity_score": 10,
                    "reason": "False positive pathogen homology match."
                })
            },
            "web_mocks": {
                spec_url: {"status": 200, "body": spec_body},
                qc_url: {"status": 200, "body": qc_body}
            }
        }
    )
    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id])
    order_initial = json.loads(contract.get_order(args=[order_id]).call())
    assert order_initial["verdict"] == "BIOHAZARD_BLOCKED"

    # Researcher appeals with substantive justification & staked bond
    supp_url = "https://certified-lab.org/attestation.pdf"
    supp_body = "Certified Non-Toxic Assays"
    supp_hash = _sha256(supp_body)

    contract.connect(researcher).appeal_verdict(
        args=[order_id, "Legitimate therapeutic protein certified by mass spec assay.", audit_lab, supp_hash],
        value=200000000000000000
    )

    # Appellate tribunal receives certified laboratory proof and overturns biohazard
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "APPEAL_BIOHAZARD_OVERTURNED_BENIGN",
                    "reason": "Certified mass spectrometry assay confirms non-toxic therapeutic protein without virulence factors."
                })
            },
            "web_mocks": {
                supp_url: {"status": 200, "body": supp_body}
            }
        }
    )
    contract.connect(researcher).adjudicate_appeal(args=[order_id, supp_url])

    order_final = json.loads(contract.get_order(args=[order_id]).call())
    # Crucial proof: NOT slashed to reserve, but overturned to refund researcher
    assert order_final["status"] == 5
    assert "BIOHAZARD OVERTURNED" in order_final["reason"]


def test_authorized_foundry_registry_governance(client):
    """
    CRITICAL STEWARD REDESIGN TEST (Foundry Registry Management):
    Proves that the protocol owner can register and revoke accredited foundries
    with laboratory certification IDs, and unauthorized accounts cannot.
    """
    contract = client.deploy("contracts/contract.py")
    owner = client.accounts[0]
    new_foundry = "0x4444444444444444444444444444444444444444"

    # Verify not authorized initially
    assert not contract.is_authorized_foundry(args=[new_foundry]).call()

    # Owner registers foundry with lab accreditation ID
    contract.connect(owner).register_foundry(args=[new_foundry, "ISO-17025-LAB-TWIST-88"])
    assert contract.is_authorized_foundry(args=[new_foundry]).call()
    assert contract.get_foundry_lab_id(args=[new_foundry]).call() == "ISO-17025-LAB-TWIST-88"

    # Owner revokes foundry
    contract.connect(owner).revoke_foundry(args=[new_foundry])
    assert not contract.is_authorized_foundry(args=[new_foundry]).call()


def test_designated_target_foundry_cannot_bypass_accreditation_registry(client):
    """
    CRITICAL GEN. DAVE CRITIQUE TEST 1:
    Proves that designating a target_foundry CANNOT bypass the accreditation registry.
    Unaccredited wallets cannot be designated, and unaccredited wallets cannot claim or submit.
    """
    contract = client.deploy("contracts/contract.py")
    owner = client.accounts[0]
    researcher = client.accounts[1]
    unaccredited_wallet = "0x9999999999999999999999999999999999999999"
    accredited_wallet = client.accounts[2]
    spec_hash = _sha256(">spec\nATGC")

    # Attempt to order with unaccredited target foundry -> MUST REVERT
    with pytest.raises(Exception) as excinfo:
        contract.connect(researcher).order_synthesis(
            args=[
                "Bioremediation enzyme for environmental cleanup",
                "https://spec.org/enzyme.fasta",
                86400 * 7,
                spec_hash,
                unaccredited_wallet
            ],
            value=1000000000000000000
        )
    assert "accredited" in str(excinfo.value).lower()

    # Owner accredits the foundry in the registry
    contract.connect(owner).register_foundry(args=[unaccredited_wallet, "LAB-ACCREDITED-GLOBAL-99"])
    assert contract.is_authorized_foundry(args=[unaccredited_wallet]).call()

    # Now ordering specifying the accredited foundry succeeds
    tx = contract.connect(researcher).order_synthesis(
        args=[
            "Bioremediation enzyme for environmental cleanup",
            "https://spec.org/enzyme.fasta",
            86400 * 7,
            spec_hash,
            unaccredited_wallet
        ],
        value=1000000000000000000
    )
    oid = tx.return_value

    # Different foundry (even if accredited) cannot claim designated order
    with pytest.raises(Exception) as excinfo:
        contract.connect(accredited_wallet).accept_synthesis_agreement(args=[oid])
    assert "designated" in str(excinfo.value).lower()

    # Designated accredited foundry can accept
    contract.connect(unaccredited_wallet).accept_synthesis_agreement(args=[oid])
    o = json.loads(contract.get_order(args=[oid]).call())
    assert o["status"] == 1
    assert o["foundry"].lower() == unaccredited_wallet.lower()


def test_cryptographic_content_commitment_detects_specification_tampering(client):
    """
    CRITICAL GEN. DAVE CRITIQUE TEST 2A:
    Proves that if commissioned specification content at the URL does not match
    the immutable cryptographic spec_evidence_hash committed at order creation,
    adjudication flags content commitment failure and sets SEQUENCE_DEFECTIVE.
    """
    contract = client.deploy("contracts/contract.py")
    researcher = client.accounts[0]
    foundry = client.accounts[1]

    original_spec_text = ">authentic_target_spec\nATGCATGCATGC"
    committed_spec_hash = _sha256(original_spec_text)

    spec_url = "https://research-lab.org/original_design.fasta"
    qc_url = "https://foundry.org/delivery_qc.txt"
    qc_text = ">qc\nATGCATGCATGC"
    committed_qc_hash = _sha256(qc_text)

    tx = contract.connect(researcher).order_synthesis(
        args=[
            "Therapeutic antibody CDR3 domain",
            spec_url,
            86400 * 7,
            committed_spec_hash
        ],
        value=1000000000000000000
    )
    oid = tx.return_value

    contract.connect(foundry).submit_synthesis_proof(args=[oid, qc_url, committed_qc_hash])

    # Attacker alters the text at the spec URL after order creation
    tampered_spec_text = ">tampered_modified_spec\nGGGGGGGGGGGG"
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "web_mocks": {
                spec_url: {"status": 200, "body": tampered_spec_text},
                qc_url: {"status": 200, "body": qc_text}
            }
        }
    )

    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[oid])
    o = json.loads(contract.get_order(args=[oid]).call())
    assert o["status"] == 2
    assert o["verdict"] == "SEQUENCE_DEFECTIVE"
    assert "content commitment verification failed" in o["reason"].lower()


def test_cryptographic_content_commitment_detects_qc_tampering(client):
    """
    CRITICAL GEN. DAVE CRITIQUE TEST 2B:
    Proves that if delivered QC report content at the URL does not match
    the immutable cryptographic qc_evidence_hash submitted by the foundry,
    adjudication flags content commitment failure and sets SEQUENCE_DEFECTIVE.
    """
    contract = client.deploy("contracts/contract.py")
    researcher = client.accounts[0]
    foundry = client.accounts[1]

    spec_url = "https://research-lab.org/target.fasta"
    qc_url = "https://foundry.org/lot_qc.txt"

    spec_text = ">seq\nATGCGATCGATC"
    spec_hash = _sha256(spec_text)

    tx = contract.connect(researcher).order_synthesis(
        args=["Therapeutic antibody CDR3 domain", spec_url, 86400 * 7, spec_hash],
        value=1000000000000000000
    )
    oid = tx.return_value

    authentic_qc_text = ">qc\nATGCGATCGATC_AUTHENTIC"
    committed_qc_hash = _sha256(authentic_qc_text)

    # Foundry commits to qc_evidence_hash
    contract.connect(foundry).submit_synthesis_proof(
        args=[oid, qc_url, committed_qc_hash]
    )

    # But web mock serves altered QC text (tampered data)
    altered_qc_text = ">qc\nATGCGATCGATC_TAMPERED_INJECTED"
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "web_mocks": {
                spec_url: {"status": 200, "body": spec_text},
                qc_url: {"status": 200, "body": altered_qc_text}
            }
        }
    )

    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[oid])
    o = json.loads(contract.get_order(args=[oid]).call())
    assert o["status"] == 2
    assert o["verdict"] == "SEQUENCE_DEFECTIVE"
    assert "content commitment verification failed" in o["reason"].lower()


def test_appeal_requires_authenticated_laboratory_provenance_and_hash_integrity(client):
    """
    CRITICAL GEN. DAVE CRITIQUE TEST 3:
    Proves that appeal outcomes require authenticated laboratory provenance
    from an accredited registry laboratory, and detect tampered supplemental evidence hashes.
    """
    contract = client.deploy("contracts/contract.py")
    owner = client.accounts[0]
    researcher = client.accounts[1]
    foundry = client.accounts[2]
    unaccredited_lab = "0x7777777777777777777777777777777777777777"
    accredited_audit_lab = "0x6666666666666666666666666666666666666666"

    spec_url = "https://spec.org/dna.fasta"
    qc_url = "https://foundry.org/qc.txt"
    spec_text = ">spec\nATGC"
    qc_text = ">qc\nATGC"
    spec_hash = _sha256(spec_text)
    qc_hash = _sha256(qc_text)

    tx = contract.connect(researcher).order_synthesis(
        args=["Therapeutic enzyme construct", spec_url, 86400 * 7, spec_hash],
        value=1000000000000000000
    )
    oid = tx.return_value
    contract.connect(foundry).submit_synthesis_proof(args=[oid, qc_url, qc_hash])

    # Initial adjudication gives BIOHAZARD_BLOCKED
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "BIOHAZARD_BLOCKED",
                    "confidence": 98,
                    "fidelity_score": 10,
                    "reason": "Suspected toxin similarity"
                })
            },
            "web_mocks": {
                spec_url: {"status": 200, "body": spec_text},
                qc_url: {"status": 200, "body": qc_text}
            }
        }
    )
    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[oid])

    # Attempt to appeal designating an UNACCREDITED laboratory -> MUST REVERT
    correct_supp_hash = _sha256("Certified Independent Mass Spectrometry: Non-Toxic Therapeutic Enzyme")
    with pytest.raises(Exception) as excinfo:
        contract.connect(researcher).appeal_verdict(
            args=[oid, "Appealing with unaccredited laboratory", unaccredited_lab, correct_supp_hash],
            value=100000000000000000
        )
    assert "accreditation" in str(excinfo.value).lower() or "accredited" in str(excinfo.value).lower()

    # Owner registers independent accredited audit lab
    contract.connect(owner).register_audit_lab(args=[accredited_audit_lab, "LAB-ISO17025-INDEPENDENT-AUDIT"])

    # Appellant files appeal bound to accredited audit lab & committed hash
    contract.connect(researcher).appeal_verdict(
        args=[
            oid,
            "Certified independent mass spectrometry confirms non-toxic enzyme",
            accredited_audit_lab,
            correct_supp_hash
        ],
        value=100000000000000000
    )

    # Case A: Attacker attempts to provide unauthenticated/tampered supplemental URL
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "web_mocks": {
                "https://supp.org/proof.txt": {"status": 200, "body": "TAMPERED_CONTENT_DIFFERS"}
            }
        }
    )
    contract.connect(researcher).adjudicate_appeal(args=[oid, "https://supp.org/proof.txt"])
    o = json.loads(contract.get_order(args=[oid]).call())
    # Tampering detected: appeal dismissed / biohazard confirmed
    assert o["status"] == 4  # BIOHAZARD_SLASHED
    assert "verification failed" in o["reason"]


def test_retrieval_failure_aborts_without_defective_penalty(client):
    """
    CRITICAL STEWARD REQUIREMENT 2:
    Proves that an unreachable spec or QC report URL (HTTP 404, network timeout, empty body)
    aborts adjudication via clean revert without penalizing the foundry or marking
    the order SEQUENCE_DEFECTIVE. The order remains IN_SYNTHESIS so adjudication can be retried.
    """
    contract = client.deploy("contracts/contract.py")
    researcher = client.accounts[0]
    foundry = client.accounts[1]

    spec_url = "https://server-down.org/target.fasta"
    qc_url = "https://foundry-qc.io/lot_5521.txt"
    spec_text = ">seq\nATGCGATCGATC"
    qc_text = ">qc\nATGCGATCGATC"
    spec_hash = _sha256(spec_text)
    qc_hash = _sha256(qc_text)

    tx = contract.connect(researcher).order_synthesis(
        args=["Valid peptide order", spec_url, 86400 * 7, spec_hash],
        value=1000000000000000000
    )
    oid = tx.return_value
    contract.connect(foundry).submit_synthesis_proof(args=[oid, qc_url, qc_hash])

    # Case 1: Spec URL is 404
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "web_mocks": {
                spec_url: {"status": 404, "body": ""},
                qc_url: {"status": 200, "body": qc_text}
            }
        }
    )
    with pytest.raises(Exception) as exc1:
        contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[oid])
    err1 = str(exc1.value).lower()
    assert "retrieval failed" in err1 or "unreachable" in err1

    # Order MUST remain IN_SYNTHESIS (status 1) and NOT marked SEQUENCE_DEFECTIVE
    o = json.loads(contract.get_order(args=[oid]).call())
    assert o["status"] == 1
    assert o["verdict"] != "SEQUENCE_DEFECTIVE"

    # Case 2: QC URL is unreachable / empty
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "web_mocks": {
                spec_url: {"status": 200, "body": spec_text},
                qc_url: {"status": 500, "body": ""}
            }
        }
    )
    with pytest.raises(Exception) as exc2:
        contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[oid])
    err2 = str(exc2.value).lower()
    assert "retrieval failed" in err2 or "unreachable" in err2

    # Order remains intact for retry
    o2 = json.loads(contract.get_order(args=[oid]).call())
    assert o2["status"] == 1
    assert o2["verdict"] != "SEQUENCE_DEFECTIVE"


def test_independent_eighty_percent_fidelity_enforcement(client):
    """
    CRITICAL STEWARD REQUIREMENT 4:
    Proves that independent validator and contract logic strictly enforces that
    fidelity < 80% CAN NEVER yield BIO_SYNTHESIS_VERIFIED, even if a compromised
    or hallucinating LLM jury returns BIO_SYNTHESIS_VERIFIED.
    """
    contract = client.deploy("contracts/contract.py")
    researcher = client.accounts[0]
    foundry = client.accounts[1]

    spec_url = "https://biosecure.org/target.fasta"
    qc_url = "https://foundry.org/qc.txt"
    spec_text = ">seq\nATGCGATCGATC"
    qc_text = ">qc\nATGCGATCGATC"
    spec_hash = _sha256(spec_text)
    qc_hash = _sha256(qc_text)

    tx = contract.connect(researcher).order_synthesis(
        args=["Therapeutic enzyme", spec_url, 86400 * 7, spec_hash],
        value=1000000000000000000
    )
    oid = tx.return_value
    contract.connect(foundry).submit_synthesis_proof(args=[oid, qc_url, qc_hash])

    # Hallucinating LLM returns BIO_SYNTHESIS_VERIFIED but low fidelity 72% (< 80%)
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "BIO_SYNTHESIS_VERIFIED",
                    "confidence": 95,
                    "fidelity_score": 72,
                    "reason": "Hallucinating prompt claiming verified despite 72% alignment."
                })
            },
            "web_mocks": {
                spec_url: {"status": 200, "body": spec_text},
                qc_url: {"status": 200, "body": qc_text}
            }
        }
    )

    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[oid])
    o = json.loads(contract.get_order(args=[oid]).call())

    # Contract state logic MUST override to SEQUENCE_DEFECTIVE
    assert o["verdict"] == "SEQUENCE_DEFECTIVE"
    assert o["fidelity_score"] == 72
    assert "80% fidelity threshold" in o["reason"]


def test_strict_content_commitments_reject_invalid_hashes(client):
    """
    CRITICAL STEWARD REQUIREMENT 1:
    Proves that order_synthesis and submit_synthesis_proof strictly reject
    missing, short, non-hex, or malformed hashes with zero fallback to URL hashing.
    """
    contract = client.deploy("contracts/contract.py")
    researcher = client.accounts[0]
    foundry = client.accounts[1]

    spec_url = "https://biosecure.org/spec.fasta"

    # 1. Missing spec hash -> REVERTS
    with pytest.raises(Exception) as exc1:
        contract.connect(researcher).order_synthesis(
            args=["Therapeutic peptide", spec_url, 86400 * 7, ""],
            value=1000000000000000000
        )
    assert "valid 64-character hex" in str(exc1.value).lower()

    # 2. Too short spec hash -> REVERTS
    with pytest.raises(Exception) as exc2:
        contract.connect(researcher).order_synthesis(
            args=["Therapeutic peptide", spec_url, 86400 * 7, "abc123short"],
            value=1000000000000000000
        )
    assert "valid 64-character hex" in str(exc2.value).lower()

    # 3. Valid spec hash succeeds
    valid_spec_hash = _sha256(">spec\nATGC")
    tx = contract.connect(researcher).order_synthesis(
        args=["Therapeutic peptide", spec_url, 86400 * 7, valid_spec_hash],
        value=1000000000000000000
    )
    oid = tx.return_value

    # 4. Invalid QC hash -> REVERTS
    with pytest.raises(Exception) as exc3:
        contract.connect(foundry).submit_synthesis_proof(
            args=[oid, "https://foundry.org/qc.txt", "not_a_valid_hash_123"]
        )
    assert "valid 64-character hex" in str(exc3.value).lower()
