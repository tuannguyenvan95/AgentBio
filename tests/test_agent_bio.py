import pytest
import json
import hashlib


def test_genuine_content_commitment_verification(contract, researcher, foundry):
    """Verifies that actual document SHA-256 hash is required and verified."""
    # 1. Register authorized foundry
    contract.connect(contract.owner).register_foundry(args=[foundry, "LAB-ACCREDITED-01"]).transact()

    # 2. Researcher places order with valid 64-hex hash
    spec_hash = "a" * 64
    order_id = contract.connect(researcher).order_synthesis(
        args=["Binding enzyme for therapeutic target", "https://example.com/spec.fasta", 604800, spec_hash]
    ).transact(value=1000)

    # 3. Invalid/missing hash is rejected with ContractError/ValueError
    with pytest.raises(Exception) as exc_info:
        contract.connect(researcher).order_synthesis(
            args=["Binding enzyme for therapeutic target", "https://example.com/spec.fasta", 604800, "invalid_short_hash"]
        ).transact(value=1000)
    assert "64-character hex" in str(exc_info.value).lower()

    # 4. Authorized foundry accepts
    contract.connect(foundry).accept_synthesis_agreement(args=[order_id]).transact()

    # 5. Verify bilateral agreement state
    order_json = json.loads(contract.get_order(args=[order_id]).call())
    assert order_json["agreement_accepted"] is True
    assert order_json["foundry"].lower() == str(foundry).lower()


def test_retrieval_failure_aborts_without_defective_penalty(contract, researcher, foundry, client):
    """Verifies retrieval failure does not mark order as defective."""
    contract.connect(contract.owner).register_foundry(args=[foundry, "LAB-ACCREDITED-01"]).transact()

    order_id = contract.connect(researcher).order_synthesis(
        args=["Therapeutic peptide target", "https://example.com/spec.fasta", 604800, "b" * 64]
    ).transact(value=1000)

    contract.connect(foundry).accept_synthesis_agreement(args=[order_id]).transact()

    # Submitting proof with unrenderable/404 URL
    qc_url = "https://404-unreachable-domain.com/qc.txt"
    qc_hash = "c" * 64
    contract.connect(foundry).submit_synthesis_proof(
        args=[order_id, qc_url, qc_hash]
    ).transact()

    # Mock unrenderable 404 URL in simulator
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "web_mocks": {
                "https://example.com/spec.fasta": {"status": 200, "body": ">spec\nATGC"},
                qc_url: {"status": 404, "body": ""}
            }
        }
    )

    # Adjudication must raise error and NOT penalize foundry to defective state
    with pytest.raises(Exception) as exc_info:
        contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id]).transact()
    assert "retrieval failed" in str(exc_info.value).lower()

    # Verify status is still IN_SYNTHESIS (1), NOT SEQUENCE_DEFECTIVE
    order_json = json.loads(contract.get_order(args=[order_id]).call())
    assert order_json["status"] == 1
    assert order_json["verdict"] != "SEQUENCE_DEFECTIVE"


def test_independent_80_percent_fidelity_threshold(contract, researcher, foundry, client):
    """Verifies contract enforces >= 80% fidelity for payout."""
    contract.connect(contract.owner).register_foundry(args=[foundry, "LAB-ACCREDITED-01"]).transact()

    spec_text = ">target_enzyme\nATGCGATCGATC"
    qc_text = ">target_enzyme\nATGCGATCGATC"
    spec_hash = hashlib.sha256(spec_text.encode("utf-8")).hexdigest()
    qc_hash = hashlib.sha256(qc_text.encode("utf-8")).hexdigest()

    order_id = contract.connect(researcher).order_synthesis(
        args=["Therapeutic enzyme construct", "https://example.com/target.fasta", 604800, spec_hash]
    ).transact(value=1000)

    contract.connect(foundry).accept_synthesis_agreement(args=[order_id]).transact()
    contract.connect(foundry).submit_synthesis_proof(
        args=[order_id, "https://example.com/qc.txt", qc_hash]
    ).transact()

    # Compromised or hallucinating LLM tries to claim BIO_SYNTHESIS_VERIFIED with 65% fidelity (< 80%)
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "BIO_SYNTHESIS_VERIFIED",
                    "confidence": 90,
                    "fidelity_score": 65,
                    "reason": "Compromised prompt claiming verified despite low fidelity."
                })
            },
            "web_mocks": {
                "https://example.com/target.fasta": {"status": 200, "body": spec_text},
                "https://example.com/qc.txt": {"status": 200, "body": qc_text}
            }
        }
    )

    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id]).transact()

    # The contract state machine MUST independently override the verdict to SEQUENCE_DEFECTIVE
    order_json = json.loads(contract.get_order(args=[order_id]).call())
    assert order_json["verdict"] == "SEQUENCE_DEFECTIVE"
    assert order_json["fidelity_score"] == 65
    assert "80% threshold" in order_json["reason"] or "80% fidelity" in order_json["reason"]


def test_appeal_requires_accredited_lab_and_hash_commitment(contract, researcher, foundry, audit_lab, stranger, client):
    """Verifies appeal cannot be lodged by unauthorized lab or with invalid hash."""
    contract.connect(contract.owner).register_foundry(args=[foundry, "LAB-ACCREDITED-01"]).transact()

    spec_text = ">target\nATCG"
    qc_text = ">target\nATCG"
    spec_hash = hashlib.sha256(spec_text.encode("utf-8")).hexdigest()
    qc_hash = hashlib.sha256(qc_text.encode("utf-8")).hexdigest()

    order_id = contract.connect(researcher).order_synthesis(
        args=["Therapeutic antibody candidate", "https://example.com/spec.fasta", 604800, spec_hash]
    ).transact(value=1000)

    contract.connect(foundry).accept_synthesis_agreement(args=[order_id]).transact()
    contract.connect(foundry).submit_synthesis_proof(
        args=[order_id, "https://example.com/qc.txt", qc_hash]
    ).transact()

    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "BIOHAZARD_BLOCKED",
                    "confidence": 99,
                    "fidelity_score": 10,
                    "reason": "Pathogen detected."
                })
            },
            "web_mocks": {
                "https://example.com/spec.fasta": {"status": 200, "body": spec_text},
                "https://example.com/qc.txt": {"status": 200, "body": qc_text}
            }
        }
    )
    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id]).transact()

    # 1. Appealing with UNACCREDITED lab -> REVERTS
    with pytest.raises(Exception) as exc1:
        contract.connect(researcher).appeal_verdict(
            args=[order_id, "Dispute claim with unaccredited lab", stranger, "d" * 64]
        ).transact(value=100)
    assert "accreditation" in str(exc1.value).lower() or "accredited" in str(exc1.value).lower()

    # 2. Register accredited reviewing lab
    contract.connect(contract.owner).register_audit_lab(args=[audit_lab, "LAB-ISO17025-AUDITOR"]).transact()

    # 3. Appealing with invalid 64-hex hash -> REVERTS
    with pytest.raises(Exception) as exc2:
        contract.connect(researcher).appeal_verdict(
            args=[order_id, "Dispute claim with invalid hash", audit_lab, "short_hash"]
        ).transact(value=100)
    assert "64-character hex" in str(exc2.value).lower()

    # 4. Valid appeal with accredited lab & genuine 64-hex hash succeeds
    contract.connect(audit_lab).attest_appeal_evidence(args=[order_id, "d" * 64]).transact()
    contract.connect(researcher).appeal_verdict(
        args=[order_id, "Substantive independent mass spec proves benign construct", audit_lab, "d" * 64]
    ).transact(value=100)

    order_json = json.loads(contract.get_order(args=[order_id]).call())
    assert order_json["status"] == 7  # DISPUTED
    assert order_json["appeal_certifying_lab"].lower() == str(audit_lab).lower()
