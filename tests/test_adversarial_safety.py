import pytest
import json
import hashlib


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def test_duplicate_finalize_settlement_reverts(contract, researcher, foundry, client):
    """
    Adversarial test: calling finalize_settlement twice on the same order.
    Second call MUST revert because status is no longer AWAITING_PAYOUT.
    Prevents duplicate payouts.
    """
    contract.connect(contract.owner).register_foundry(args=[foundry, "LAB-ADV-01"]).transact()
    contract.connect(contract.owner).set_cooling_off_seconds(args=[0]).transact()

    spec_text = ">therapeutic_protein\nATGCGATCGATCGATC"
    qc_text = ">therapeutic_protein\nATGCGATCGATCGATC"
    spec_hash = _sha256(spec_text)
    qc_hash = _sha256(qc_text)

    order_id = contract.connect(researcher).order_synthesis(
        args=["Therapeutic protein production", "https://spec.example.com/s.fasta", 604800, spec_hash]
    ).transact(value=1000000)

    contract.connect(foundry).accept_synthesis_agreement(args=[order_id]).transact()
    contract.connect(foundry).submit_synthesis_proof(
        args=[order_id, "https://qc.example.com/qc.txt", qc_hash]
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
                    "reason": "Perfect match."
                })
            },
            "web_mocks": {
                "https://spec.example.com/s.fasta": {"status": 200, "body": spec_text},
                "https://qc.example.com/qc.txt": {"status": 200, "body": qc_text}
            }
        }
    )

    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id]).transact()

    # First finalize succeeds
    contract.connect(researcher).finalize_settlement(args=[order_id]).transact()
    order_data = json.loads(contract.get_order(args=[order_id]).call())
    assert order_data["status"] == 3  # STATUS_VERIFIED_PAID
    assert order_data["escrow_amount"] == "0"  # Escrow zeroed out

    # Second finalize MUST revert
    with pytest.raises(Exception) as exc:
        contract.connect(researcher).finalize_settlement(args=[order_id]).transact()
    assert "not awaiting settlement" in str(exc.value).lower()


def test_cancel_after_settlement_reverts(contract, researcher, foundry, client):
    """
    Adversarial test: attempting cancel_or_reclaim after order has been settled.
    Must revert to prevent double-spending of escrowed funds.
    """
    contract.connect(contract.owner).register_foundry(args=[foundry, "LAB-ADV-02"]).transact()
    contract.connect(contract.owner).set_cooling_off_seconds(args=[0]).transact()

    spec_text = ">enzyme_spec\nMKTLSLIV"
    qc_text = ">enzyme_qc\nMKTLSLIV"
    spec_hash = _sha256(spec_text)
    qc_hash = _sha256(qc_text)

    order_id = contract.connect(researcher).order_synthesis(
        args=["Recombinant enzyme production", "https://spec2.example.com/s.fasta", 604800, spec_hash]
    ).transact(value=500000)

    contract.connect(foundry).accept_synthesis_agreement(args=[order_id]).transact()
    contract.connect(foundry).submit_synthesis_proof(
        args=[order_id, "https://qc2.example.com/qc.txt", qc_hash]
    ).transact()

    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "BIO_SYNTHESIS_VERIFIED",
                    "confidence": 95,
                    "fidelity_score": 92,
                    "reason": "Good match."
                })
            },
            "web_mocks": {
                "https://spec2.example.com/s.fasta": {"status": 200, "body": spec_text},
                "https://qc2.example.com/qc.txt": {"status": 200, "body": qc_text}
            }
        }
    )

    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id]).transact()
    contract.connect(researcher).finalize_settlement(args=[order_id]).transact()

    # Attempt cancel after settlement - MUST revert
    with pytest.raises(Exception) as exc:
        contract.connect(researcher).cancel_or_reclaim(args=[order_id]).transact()
    assert "cannot be cancelled" in str(exc.value).lower()


def test_zero_escrow_transfer_prevention(contract, researcher, foundry, client):
    """
    Adversarial test: verifying that when escrow_amount is already 0,
    no transfer is emitted (safe no-op for financial operations).
    """
    contract.connect(contract.owner).register_foundry(args=[foundry, "LAB-ADV-03"]).transact()
    contract.connect(contract.owner).set_cooling_off_seconds(args=[0]).transact()

    spec_text = ">protein_spec\nATGCGATCGATC"
    qc_text = ">protein_qc_defective\nATGC----GATC"
    spec_hash = _sha256(spec_text)
    qc_hash = _sha256(qc_text)

    # Create order with 0 value to test zero-escrow edge case
    order_id = contract.connect(researcher).order_synthesis(
        args=["Zero-value test synthesis order", "https://spec3.example.com/s.fasta", 604800, spec_hash]
    ).transact(value=0)

    contract.connect(foundry).accept_synthesis_agreement(args=[order_id]).transact()
    contract.connect(foundry).submit_synthesis_proof(
        args=[order_id, "https://qc3.example.com/qc.txt", qc_hash]
    ).transact()

    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "SEQUENCE_DEFECTIVE",
                    "confidence": 90,
                    "fidelity_score": 30,
                    "reason": "Severe truncation detected."
                })
            },
            "web_mocks": {
                "https://spec3.example.com/s.fasta": {"status": 200, "body": spec_text},
                "https://qc3.example.com/qc.txt": {"status": 200, "body": qc_text}
            }
        }
    )

    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id]).transact()

    # Finalize with zero escrow - should succeed without error
    contract.connect(researcher).finalize_settlement(args=[order_id]).transact()
    order_data = json.loads(contract.get_order(args=[order_id]).call())
    assert order_data["status"] == 5  # STATUS_DEFECTIVE_REFUNDED
    assert order_data["escrow_amount"] == "0"


def test_appeal_without_lab_attestation_reverts(contract, researcher, foundry, audit_lab, client):
    """
    Adversarial test: attempting to file an appeal without the certifying lab
    having called attest_appeal_evidence() first. Must revert.
    """
    contract.connect(contract.owner).register_foundry(args=[foundry, "LAB-ADV-04"]).transact()
    contract.connect(contract.owner).register_audit_lab(args=[audit_lab, "LAB-CERTIFIER-01"]).transact()
    contract.connect(contract.owner).set_cooling_off_seconds(args=[9999]).transact()

    spec_text = ">spec_appeal_test\nATGCGATCGATCGATCGATC"
    qc_text = ">qc_appeal_test\nATGCGATCGATCGATC"
    spec_hash = _sha256(spec_text)
    qc_hash = _sha256(qc_text)

    order_id = contract.connect(researcher).order_synthesis(
        args=["Appeal attestation test protein", "https://spec4.example.com/s.fasta", 604800, spec_hash]
    ).transact(value=100000)

    contract.connect(foundry).accept_synthesis_agreement(args=[order_id]).transact()
    contract.connect(foundry).submit_synthesis_proof(
        args=[order_id, "https://qc4.example.com/qc.txt", qc_hash]
    ).transact()

    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "SEQUENCE_DEFECTIVE",
                    "confidence": 88,
                    "fidelity_score": 45,
                    "reason": "Low fidelity sequence."
                })
            },
            "web_mocks": {
                "https://spec4.example.com/s.fasta": {"status": 200, "body": spec_text},
                "https://qc4.example.com/qc.txt": {"status": 200, "body": qc_text}
            }
        }
    )

    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id]).transact()

    # Verify order is in AWAITING_PAYOUT
    order_data = json.loads(contract.get_order(args=[order_id]).call())
    assert order_data["status"] == 2

    # Attempt appeal WITHOUT lab attestation - should fail
    supp_hash = "a" * 64
    with pytest.raises(Exception) as exc:
        contract.connect(researcher).appeal_verdict(
            args=[order_id, "Researcher disputes low fidelity score", audit_lab, supp_hash],
            value=10000
        ).transact()
    assert "attest" in str(exc.value).lower()


def test_inconclusive_excerpt_truncation_safety(contract, researcher, foundry, client):
    """
    Requirement 1: Excerpt truncation safety.
    When rendered evidence exceeds the comprehensive assessment limit (12,000 chars),
    the arbiter returns EVIDENCE_INSUFFICIENT and aborts without penalizing foundry.
    """
    contract.connect(contract.owner).register_foundry(args=[foundry, "LAB-ADV-05"]).transact()

    # Spec sequence > 12,000 characters
    long_spec = ">huge_construct\n" + ("ATGC" * 3100)
    qc_text = ">qc_run\nATGC"
    spec_hash = _sha256(long_spec)
    qc_hash = _sha256(qc_text)

    order_id = contract.connect(researcher).order_synthesis(
        args=["Oversized plasmid synthesis", "https://spec-huge.org/s.fasta", 604800, spec_hash]
    ).transact(value=1000)

    contract.connect(foundry).accept_synthesis_agreement(args=[order_id]).transact()
    contract.connect(foundry).submit_synthesis_proof(
        args=[order_id, "https://qc-short.org/qc.txt", qc_hash]
    ).transact()

    client.provider.make_request(
        method="sim_installMocks",
        params={
            "web_mocks": {
                "https://spec-huge.org/s.fasta": {"status": 200, "body": long_spec},
                "https://qc-short.org/qc.txt": {"status": 200, "body": qc_text}
            }
        }
    )

    with pytest.raises(Exception) as exc:
        contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id]).transact()

    assert "insufficient" in str(exc.value).lower() or "limit" in str(exc.value).lower()
    order_data = json.loads(contract.get_order(args=[order_id]).call())
    assert order_data["status"] == 1  # IN_SYNTHESIS: no penalty applied


def test_laboratory_attestation_binding_rejection(contract, researcher, foundry, audit_lab, client):
    """
    Requirement 2: Supplemental appeal document must bind to order_id and accredited lab.
    Unbound reports are rejected with UNAUTHORIZED_ATTESTATION.
    """
    contract.connect(contract.owner).register_foundry(args=[foundry, "LAB-ADV-06"]).transact()
    contract.connect(contract.owner).register_audit_lab(args=[audit_lab, "LAB-CERTIFIER-02"]).transact()

    spec_text = ">spec_bind\nATGCATGC"
    qc_text = ">qc_bind\nATGCATGC"
    spec_hash = _sha256(spec_text)
    qc_hash = _sha256(qc_text)

    order_id = contract.connect(researcher).order_synthesis(
        args=["Attestation binding target", "https://spec-bind.org/s.fasta", 604800, spec_hash]
    ).transact(value=1000)

    contract.connect(foundry).accept_synthesis_agreement(args=[order_id]).transact()
    contract.connect(foundry).submit_synthesis_proof(
        args=[order_id, "https://qc-bind.org/qc.txt", qc_hash]
    ).transact()

    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "SEQUENCE_DEFECTIVE",
                    "confidence": 90,
                    "fidelity_score": 50,
                    "reason": "Defective."
                })
            },
            "web_mocks": {
                "https://spec-bind.org/s.fasta": {"status": 200, "body": spec_text},
                "https://qc-bind.org/qc.txt": {"status": 200, "body": qc_text}
            }
        }
    )

    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id]).transact()

    # Create supplemental report that LACKS ORDER_REF or lab binding
    unbound_supp = "Independent re-sequencing analysis showing 99% fidelity across entire cassette."
    supp_hash = _sha256(unbound_supp)

    # Accredited lab attests on-chain
    contract.connect(audit_lab).attest_appeal_evidence(args=[order_id, supp_hash]).transact()

    # Researcher appeals
    contract.connect(researcher).appeal_verdict(
        args=[order_id, "Appealing with lab re-sequencing report", audit_lab, supp_hash],
        value=100
    ).transact()

    client.provider.make_request(
        method="sim_installMocks",
        params={
            "web_mocks": {
                "https://supp-unbound.org/report.txt": {"status": 200, "body": unbound_supp}
            }
        }
    )

    # Adjudication must reject because report lacks ORDER_REF and lab binding
    with pytest.raises(Exception) as exc:
        contract.connect(researcher).adjudicate_appeal(args=[order_id, "https://supp-unbound.org/report.txt"]).transact()

    assert "attestation" in str(exc.value).lower() or "binding" in str(exc.value).lower()


def test_malformed_appellate_response_cannot_confirm_biohazard(contract, researcher, foundry, audit_lab, client):
    """
    Requirement 3: Malformed appellate response safety.
    Corrupted JSON or invalid canary from appellate tribunal CANNOT confirm biohazard
    or cause forfeiture. Must abort with INCONCLUSIVE_TRIBUNAL_ERROR.
    """
    contract.connect(contract.owner).register_foundry(args=[foundry, "LAB-ADV-07"]).transact()
    contract.connect(contract.owner).register_audit_lab(args=[audit_lab, "LAB-CERTIFIER-03"]).transact()

    spec_text = ">spec_toxin\nMKTLSLIV"
    qc_text = ">qc_toxin\nMKTLSLIV"
    spec_hash = _sha256(spec_text)
    qc_hash = _sha256(qc_text)

    order_id = contract.connect(researcher).order_synthesis(
        args=["Toxin appeal review", "https://spec-tox.org/s.fasta", 604800, spec_hash]
    ).transact(value=1000)

    contract.connect(foundry).accept_synthesis_agreement(args=[order_id]).transact()
    contract.connect(foundry).submit_synthesis_proof(
        args=[order_id, "https://qc-tox.org/qc.txt", qc_hash]
    ).transact()

    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "BIOHAZARD_BLOCKED",
                    "confidence": 99,
                    "fidelity_score": 100,
                    "reason": "Toxin match detected."
                })
            },
            "web_mocks": {
                "https://spec-tox.org/s.fasta": {"status": 200, "body": spec_text},
                "https://qc-tox.org/qc.txt": {"status": 200, "body": qc_text}
            }
        }
    )

    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id]).transact()

    bound_supp = f"ORDER_REF: {order_id}\nCertified by: LAB-CERTIFIER-03\nVerified non-toxic analog."
    supp_hash = _sha256(bound_supp)
    contract.connect(audit_lab).attest_appeal_evidence(args=[order_id, supp_hash]).transact()
    contract.connect(researcher).appeal_verdict(
        args=[order_id, "Demonstrating sequence is benign analog", audit_lab, supp_hash],
        value=100
    ).transact()

    # Appellate LLM returns corrupted response
    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": "INTERNAL SERVER ERROR 500: MALFORMED OUTPUT"
            },
            "web_mocks": {
                "https://supp-bound.org/report.txt": {"status": 200, "body": bound_supp}
            }
        }
    )

    with pytest.raises(Exception) as exc:
        contract.connect(researcher).adjudicate_appeal(args=[order_id, "https://supp-bound.org/report.txt"]).transact()

    assert "inconclusive" in str(exc.value).lower() or "malformed" in str(exc.value).lower()

    # Verify order is STILL in STATUS_DISPUTED (7) and NOT slashed (4)
    order_data = json.loads(contract.get_order(args=[order_id]).call())
    assert order_data["status"] == 7  # STATUS_DISPUTED preserved


def test_timestamp_failure_aborts_transaction(contract_source):
    """
    Requirement 4: Timestamp helper fixed fallback removal.
    The contract must strictly raise ContractError on timestamp unavailability
    and never fall back to 1760000000.
    """
    assert "1760000000" not in contract_source
    assert 'raise ContractError("Authoritative timestamp unavailable.' in contract_source


def test_failed_outbound_transfer_safe_recovery(contract, researcher, foundry, client):
    """
    Requirement 5: Safe recovery mechanism.
    Induces a failed outbound transfer during settlement (e.g. smart contract recipient
    rejection or network failure). Verifies that _safe_transfer catches the failure,
    dynamically credits claimable_balances, marks the order settled, and allows the recipient
    to recover funds safely via claim_payout() while preventing duplicate payouts.
    """
    contract.connect(contract.owner).register_foundry(args=[foundry, "LAB-SAFE-RECOVER-01"]).transact()
    contract.connect(contract.owner).set_cooling_off_seconds(args=[0]).transact()

    spec_text = ">monoclonal_antibody_spec\nATGCGATCGATCGATC"
    qc_text = ">defective_delivery_qc\nATGCGATCGTTTTTTT"
    spec_hash = _sha256(spec_text)
    qc_hash = _sha256(qc_text)
    escrow_amount = 500000

    # 1. Researcher places synthesis order with 500,000 wei escrow
    order_id = contract.connect(researcher).order_synthesis(
        args=["Monoclonal antibody IgG1 sequence", "https://biosecure.io/spec_def.fasta", 604800, spec_hash]
    ).transact(value=escrow_amount)

    # 2. Foundry accepts and submits defective sequencing QC proof
    contract.connect(foundry).accept_synthesis_agreement(args=[order_id]).transact()
    contract.connect(foundry).submit_synthesis_proof(
        args=[order_id, "https://biosecure.io/qc_def.txt", qc_hash]
    ).transact()

    client.provider.make_request(
        method="sim_installMocks",
        params={
            "llm_mocks": {
                ".*": json.dumps({
                    "canary": "CANARY_AGENT_BIO_SAFETY_V1",
                    "verdict": "SEQUENCE_DEFECTIVE",
                    "confidence": 95,
                    "fidelity_score": 40,
                    "reason": "Truncation and frameshift mutations detected."
                })
            },
            "web_mocks": {
                "https://biosecure.io/spec_def.fasta": {"status": 200, "body": spec_text},
                "https://biosecure.io/qc_def.txt": {"status": 200, "body": qc_text}
            }
        }
    )

    # 3. Adjudicate order to STATUS_AWAITING_PAYOUT (verdict: SEQUENCE_DEFECTIVE)
    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id]).transact()
    order_data = json.loads(contract.get_order(args=[order_id]).call())
    assert order_data["status"] == 2  # STATUS_AWAITING_PAYOUT
    assert order_data["verdict"] == "SEQUENCE_DEFECTIVE"

    # Prior to settlement, claimable balance is 0
    assert int(contract.get_claimable_balance(args=[researcher]).call()) == 0

    # 4. INDUCE OUTBOUND TRANSFER FAILURE:
    # Mark researcher as failing outbound transfers (simulating unpayable recipient contract / network drop)
    contract.simulate_transfer_failure(researcher)

    # 5. Execute finalize_settlement
    # The transaction MUST succeed without reverting; _safe_transfer catches failure and credits claimable_balances
    contract.connect(researcher).finalize_settlement(args=[order_id]).transact()

    # Order must be cleanly settled (status STATUS_DEFECTIVE_REFUNDED, escrow zeroed)
    settled_order = json.loads(contract.get_order(args=[order_id]).call())
    assert settled_order["status"] == 5  # STATUS_DEFECTIVE_REFUNDED
    assert int(settled_order["escrow_amount"]) == 0

    # 6. Verify that claimable_balances was dynamically credited by _safe_transfer
    claimable = int(contract.get_claimable_balance(args=[researcher]).call())
    assert claimable == escrow_amount, f"Expected {escrow_amount} in claimable balance, got {claimable}"

    # 7. Recipient safely pulls payment via claim_payout()
    contract.connect(researcher).claim_payout().transact()

    # Balance is now zeroed
    assert int(contract.get_claimable_balance(args=[researcher]).call()) == 0

    # 8. Second claim must revert (prevents duplicate payouts)
    with pytest.raises(Exception) as exc:
        contract.connect(researcher).claim_payout().transact()
    assert "no claimable balance" in str(exc.value).lower()


def test_failed_outbound_transfer_foundry_payout_safe_recovery(contract, researcher, foundry, client):
    """
    Requirement 5: Safe recovery mechanism for Foundry payouts.
    Induces a failed outbound transfer during verified settlement release to Foundry.
    Verifies that _safe_transfer catches the failure, credits claimable_balances[foundry],
    and allows Foundry to claim funds cleanly without double-spending.
    """
    contract.connect(contract.owner).register_foundry(args=[foundry, "LAB-SAFE-FOUNDRY-01"]).transact()
    contract.connect(contract.owner).set_cooling_off_seconds(args=[0]).transact()

    spec_text = ">verified_monoclonal_antibody\nATGCGATCGATCGATC"
    qc_text = ">verified_monoclonal_antibody\nATGCGATCGATCGATC"
    spec_hash = _sha256(spec_text)
    qc_hash = _sha256(qc_text)
    escrow_amount = 750000

    order_id = contract.connect(researcher).order_synthesis(
        args=["Therapeutic IgG1 construct", "https://biosecure.io/spec_ver.fasta", 604800, spec_hash]
    ).transact(value=escrow_amount)

    contract.connect(foundry).accept_synthesis_agreement(args=[order_id]).transact()
    contract.connect(foundry).submit_synthesis_proof(
        args=[order_id, "https://biosecure.io/qc_ver.txt", qc_hash]
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
                    "reason": "100% full-length match verified."
                })
            },
            "web_mocks": {
                "https://biosecure.io/spec_ver.fasta": {"status": 200, "body": spec_text},
                "https://biosecure.io/qc_ver.txt": {"status": 200, "body": qc_text}
            }
        }
    )

    contract.connect(researcher).adjudicate_biosecurity_and_qc(args=[order_id]).transact()

    # Induce outbound transfer failure for Foundry
    contract.simulate_transfer_failure(foundry)

    # Finalize settlement
    contract.connect(researcher).finalize_settlement(args=[order_id]).transact()

    settled_order = json.loads(contract.get_order(args=[order_id]).call())
    assert settled_order["status"] == 3  # STATUS_VERIFIED_PAID
    assert int(settled_order["escrow_amount"]) == 0

    # Verify claimable balance credited to foundry
    claimable = int(contract.get_claimable_balance(args=[foundry]).call())
    assert claimable == escrow_amount

    # Foundry claims payout
    contract.connect(foundry).claim_payout().transact()
    assert int(contract.get_claimable_balance(args=[foundry]).call()) == 0

    # Second claim must revert
    with pytest.raises(Exception) as exc:
        contract.connect(foundry).claim_payout().transact()
    assert "no claimable balance" in str(exc.value).lower()

