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
    assert "return bigint(int(self.order_counter))" not in contract_source, "Found prohibited logical block-counter timing fallback!"
    assert 'raise gl.UserError("Trusted execution timestamp unavailable from GenVM message context.")' in contract_source
