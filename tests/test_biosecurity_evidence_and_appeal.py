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
    assert "100% escrow & dispute bond forfeited to Reserve" in final_order["reason"]
