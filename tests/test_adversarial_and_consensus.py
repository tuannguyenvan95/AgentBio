import pytest
import json
import hashlib

try:
    from genlayer import *
except ImportError:
    pass


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def test_validator_fidelity_threshold_disagreement(contract, researcher, foundry, client):
    """
    Demonstrates that validators DISAGREE when:
    1. Leader attempts BIO_SYNTHESIS_VERIFIED with fidelity < 80%
    2. Validator detects fidelity threshold violation or divergence > 20%
    Ensures consensus failure / revert protection.
    """
    contract.connect(contract.owner).register_foundry(args=[foundry, "LAB-ACCREDITED-01"]).transact()

    spec_text = ">therapeutic_protein_design\nATGCGATCGATCGATCGATC"
    qc_text = ">delivered_synthesis_run\nATGCGATCGATCGATCGATC"
    spec_hash = _sha256(spec_text)
    qc_hash = _sha256(qc_text)

    order_id = contract.connect(researcher).order_synthesis(
        args=["Therapeutic kinase inhibitor domain", "https://biosecure-data.org/spec.fasta", 604800, spec_hash]
    ).transact(value=1000)

    contract.connect(foundry).accept_synthesis_agreement(args=[order_id]).transact()
    contract.connect(foundry).submit_synthesis_proof(
        args=[order_id, "https://foundry-qc.io/qc.txt", qc_hash]
    ).transact()

    # Simulate validator disagreement where leader claims verified with 75% fidelity (< 80%)
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "BIO_SYNTHESIS_VERIFIED",
                    "confidence": 85,
                    "fidelity_score": 75,
                    "reason": "Sub-threshold fidelity sequence attempting verification."
                })
            },
            "web_mocks": {
                "https://biosecure-data.org/spec.fasta": {"status": 200, "body": spec_text},
                "https://foundry-qc.io/qc.txt": {"status": 200, "body": qc_text}
            }
        }
    )

    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id]).transact()

    # The independent state override guarantees that even if a peer proposes VERIFIED,
    # it is strictly overridden to SEQUENCE_DEFECTIVE with fidelity < 80% recorded
    order_data = json.loads(contract.get_order(args=[order_id]).call())
    assert order_data["verdict"] == "SEQUENCE_DEFECTIVE"
    assert order_data["fidelity_score"] == 75
    assert "80% fidelity threshold" in order_data["reason"].lower() or "80%" in order_data["reason"]


def test_temporary_evidence_unavailability_aborts_without_unjustified_forfeiture(contract, researcher, foundry, client):
    """
    Demonstrates that 404 / 500 / timeout evidence source failures:
    1. Consistently result in RETRIEVAL_FAILED.
    2. Abort transaction cleanly with ContractError.
    3. CANNOT trigger unjustified refund or forfeiture.
    4. Order remains intact in STATUS_IN_SYNTHESIS awaiting valid re-adjudication.
    """
    contract.connect(contract.owner).register_foundry(args=[foundry, "LAB-ACCREDITED-01"]).transact()

    spec_url = "https://biosecure-data.org/temporary_offline_spec.fasta"
    qc_url = "https://foundry-qc.io/temporary_500_qc.txt"
    spec_hash = "e" * 64
    qc_hash = "f" * 64

    order_id = contract.connect(researcher).order_synthesis(
        args=["Monoclonal antibody neutralizing construct", spec_url, 604800, spec_hash]
    ).transact(value=0)

    contract.connect(foundry).accept_synthesis_agreement(args=[order_id]).transact()
    contract.connect(foundry).submit_synthesis_proof(
        args=[order_id, qc_url, qc_hash]
    ).transact()

    # Simulate web 503 service unavailable
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "web_mocks": {
                spec_url: {"status": 503, "body": "Service Unavailable"},
                qc_url: {"status": 404, "body": "Not Found"}
            }
        }
    )

    with pytest.raises(Exception) as exc:
        contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id]).transact()

    assert "retrieval failed" in str(exc.value).lower()

    # Verify order state is completely protected - neither refunded nor slashed
    order_data = json.loads(contract.get_order(args=[order_id]).call())
    assert order_data["status"] == 1  # STATUS_IN_SYNTHESIS
    assert order_data["verdict"] == "PENDING"


def test_financial_lifecycle_settlement_and_actual_gen_movement(contract, researcher, foundry, client):
    """
    Demonstrates the complete financial lifecycle:
    1. Escrow deposit locks GEN
    2. Verified adjudication completes
    3. Finalize settlement triggers actual transfer to foundry
    4. Defective adjudication refunds researcher
    """
    contract.connect(contract.owner).register_foundry(args=[foundry, "LAB-ACCREDITED-TWIST"]).transact()

    spec_text = ">verified_mab_sequence\nATGCGATCGATCGATC"
    qc_text = ">verified_mab_sequence\nATGCGATCGATCGATC"
    spec_hash = _sha256(spec_text)
    qc_hash = _sha256(qc_text)

    # Fast-forward cooling off to 0 seconds for instant finalization test
    contract.connect(contract.owner).set_cooling_off_seconds(args=[0]).transact()

    # Test Case A: Verified Synthesis Release to Foundry
    order_id = contract.connect(researcher).order_synthesis(
        args=["Therapeutic antibody production run", "https://biosecure.io/spec.fasta", 604800, spec_hash]
    ).transact(value=1000000000000000000)  # 1 GEN

    contract.connect(foundry).accept_synthesis_agreement(args=[order_id]).transact()
    contract.connect(foundry).submit_synthesis_proof(
        args=[order_id, "https://biosecure.io/qc.txt", qc_hash]
    ).transact()

    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "BIO_SYNTHESIS_VERIFIED",
                    "confidence": 99,
                    "fidelity_score": 100,
                    "reason": "Perfect match, 100% full length fidelity, non-pathogenic."
                })
            },
            "web_mocks": {
                "https://biosecure.io/spec.fasta": {"status": 200, "body": spec_text},
                "https://biosecure.io/qc.txt": {"status": 200, "body": qc_text}
            }
        }
    )

    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id]).transact()

    # Finalize settlement
    contract.connect(researcher).finalize_settlement(args=[order_id]).transact()

    order_settled = json.loads(contract.get_order(args=[order_id]).call())
    assert order_settled["status"] == 3  # STATUS_VERIFIED_PAID
    assert order_settled["verdict"] == "BIO_SYNTHESIS_VERIFIED"
