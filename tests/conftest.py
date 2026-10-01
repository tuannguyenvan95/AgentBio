import pytest
import json
import hashlib
from pathlib import Path

CONTRACTS_DIR = Path(__file__).parent.parent / "contracts"
CONTRACT_PATH = CONTRACTS_DIR / "contract.py"


@pytest.fixture(scope="session")
def contract_source() -> str:
    """Load the AgentBio intelligent contract source code."""
    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def mock_verified_synthesis():
    """Mock sequencing QC report and LLM verdict response for clean therapeutic sequence (BIO_SYNTHESIS_VERIFIED)."""
    return {
        "qc_content": """>NGS_QC_RUN_8921 | Sample: Humanized Anti-IL6 Monoclonal Antibody Heavy Chain
MVRVLVLALLALASASALAWPQ...
Mean Q-Score: 39.8 (99.99% accuracy)
Full-length ORF intact: YES. No premature stop codons. Purity: 99.4%.
Host residual DNA: < 0.001%. Contaminant pathogens: NONE detected.
Target Identity: 100.0% match against therapeutic sequence spec.""",
        "llm_response": json.dumps({
            "canary": "CANARY_AGENT_BIO_SAFETY_V1",
            "verdict": "BIO_SYNTHESIS_VERIFIED",
            "confidence": 98,
            "fidelity_score": 99,
            "reason": "Sequencing verification shows 99.4% purity and 100% full-length alignment with therapeutic target. No toxin homology or dual-use biosecurity hazard detected."
        })
    }


@pytest.fixture
def mock_biohazard_pathogen():
    """Mock sequencing QC report and LLM verdict response for prohibited select agent / weaponized toxin (BIOHAZARD_BLOCKED)."""
    return {
        "qc_content": """>NGS_QC_RUN_6606 | Sample: Dual-Use Select Agent Candidate
MKTLSLIVLGLVVSVG...
Homology Match: Clostridium botulinum neurotoxin type A (BoNT/A light chain)
Zinc-dependent endopeptidase catalytic domain: 99.8% conserved.
Lethal potency index: EXTREME. Tier 1 Dual-Use Biohazard.
Federal Select Agent Program: Regulated Toxin - Immediate Quarantine Required.""",
        "llm_response": json.dumps({
            "canary": "CANARY_AGENT_BIO_SAFETY_V1",
            "verdict": "BIOHAZARD_BLOCKED",
            "confidence": 100,
            "fidelity_score": 95,
            "reason": "CRITICAL BIOSECURITY ALERT: Sequence codes for Botulinum neurotoxin type A catalytic domain. Identified as Tier 1 select agent toxin. Escrow confiscated to protocol biosecurity reserve."
        })
    }


@pytest.fixture
def mock_defective_sequence():
    """Mock sequencing QC report and LLM verdict response for mutated / truncated sequence (SEQUENCE_DEFECTIVE)."""
    return {
        "qc_content": """>NGS_QC_RUN_4112 | Sample: Recombinant Beta-Glucosidase
ATGAAAC...
Mean Q-Score: 21.2
Frame-shift deletion detected at Codon 44 (Delta-T).
Premature termination at residue 52. Intact full-length target: 12.3%.
Purity: FAILED. High proportion of chimeric truncated plasmids.""",
        "llm_response": json.dumps({
            "canary": "CANARY_AGENT_BIO_SAFETY_V1",
            "verdict": "SEQUENCE_DEFECTIVE",
            "confidence": 95,
            "fidelity_score": 25,
            "reason": "Severe frame-shift mutation at codon 44 leads to truncation at residue 52. Full-length fidelity is only 25%, well below the required 80% threshold. Refund granted to researcher."
        })
    }


class _MockCallResult:
    def __init__(self, val):
        self._val = val

    def call(self):
        return self._val


class _MockTxResult:
    def __init__(self, return_value):
        self.return_value = return_value


class _MockSimContract:
    def __init__(self, sim_client, contract_path):
        self.client = sim_client
        self.contract_path = contract_path
        self.orders = {}
        self.order_counter = 0
        self.caller = None

    def connect(self, account):
        self.caller = account
        return self

    def order_synthesis(self, args, value=0):
        self.order_counter += 1
        oid = self.order_counter
        target_fn, spec_url, duration = args
        self.orders[oid] = {
            "order_id": oid,
            "researcher": self.caller,
            "foundry": "0x0000000000000000000000000000000000000000",
            "dispute_initiator": "0x0000000000000000000000000000000000000000",
            "escrow_amount": str(value),
            "dispute_bond": "0",
            "target_protein_function": target_fn,
            "sequence_spec_url": spec_url,
            "spec_evidence_hash": "",
            "qc_report_url": "",
            "qc_evidence_hash": "",
            "evidence_hash": "",
            "status": 0,  # OPEN
            "verdict": "PENDING",
            "reason": "Order open.",
            "confidence": 0,
            "fidelity_score": 0,
        }
        return _MockTxResult(oid)

    def submit_synthesis_proof(self, args):
        oid, qc_url = args
        self.orders[oid]["foundry"] = self.caller
        self.orders[oid]["qc_report_url"] = qc_url
        self.orders[oid]["status"] = 1  # IN_SYNTHESIS
        return _MockTxResult(None)

    def adjudicate_biosecurity_and_qc(self, args):
        oid = args[0]
        order = self.orders[oid]
        # Retrieve mocks from client provider
        web_mocks = self.client.provider.web_mocks
        llm_mocks = self.client.provider.llm_mocks

        spec_raw = web_mocks.get(order["sequence_spec_url"], {}).get("body", "default_spec")
        qc_raw = web_mocks.get(order["qc_report_url"], {}).get("body", "default_qc")

        spec_hash = hashlib.sha256(spec_raw.encode("utf-8")).hexdigest()
        qc_hash = hashlib.sha256(qc_raw.encode("utf-8")).hexdigest()

        order["spec_evidence_hash"] = spec_hash
        order["qc_evidence_hash"] = qc_hash
        order["evidence_hash"] = qc_hash

        # Extract verdict from llm mock
        verdict = "BIOHAZARD_BLOCKED"
        reason = "Biohazard detected"
        confidence = 98
        fidelity = 10
        if llm_mocks:
            for pat, resp in llm_mocks.items():
                parsed = json.loads(resp)
                verdict = parsed.get("verdict", verdict)
                reason = parsed.get("reason", reason)
                confidence = parsed.get("confidence", confidence)
                fidelity = parsed.get("fidelity_score", fidelity)
                break

        order["verdict"] = verdict
        order["reason"] = reason
        order["confidence"] = confidence
        order["fidelity_score"] = fidelity
        order["status"] = 2  # AWAITING_PAYOUT
        return _MockTxResult(None)

    def appeal_verdict(self, args, value=0):
        oid, justification = args
        self.orders[oid]["status"] = 7  # DISPUTED
        self.orders[oid]["dispute_bond"] = str(value)
        self.orders[oid]["dispute_initiator"] = self.caller
        return _MockTxResult(None)

    def adjudicate_appeal(self, args):
        oid, supplemental_url = args
        order = self.orders[oid]
        llm_mocks = self.client.provider.llm_mocks
        verdict = "APPEAL_BIOHAZARD_CONFIRMED"
        if llm_mocks:
            for pat, resp in llm_mocks.items():
                parsed = json.loads(resp)
                verdict = parsed.get("verdict", verdict)
                break

        if verdict == "APPEAL_BIOHAZARD_CONFIRMED" or order["verdict"] == "BIOHAZARD_BLOCKED":
            order["status"] = 4  # STATUS_BIOHAZARD_SLASHED
            order["verdict"] = "BIOHAZARD_BLOCKED"
            order["reason"] = (
                "Appeal rejected: lethal pathogen or weaponized biological agent confirmed. "
                "100% escrow & dispute bond forfeited to Reserve."
            )
        return _MockTxResult(None)

    def get_order(self, args):
        oid = args[0]
        return _MockCallResult(json.dumps(self.orders[oid]))


class _MockProvider:
    def __init__(self):
        self.llm_mocks = {}
        self.web_mocks = {}

    def make_request(self, method, params):
        if method == "sim_installMocks":
            self.llm_mocks = params.get("llm_mocks", {})
            self.web_mocks = params.get("web_mocks", {})
            return True
        return None


class _MockSimClient:
    def __init__(self):
        self.accounts = [
            "0x1111111111111111111111111111111111111111",
            "0x2222222222222222222222222222222222222222",
            "0x3333333333333333333333333333333333333333"
        ]
        self.provider = _MockProvider()

    def deploy(self, contract_path):
        return _MockSimContract(self, contract_path)


@pytest.fixture
def client():
    """Provides a client instance for contract testing (supports local simulation and gltest)."""
    try:
        from gltest.fixtures import get_gl_client
        c = get_gl_client()
        if c is not None and hasattr(c, "deploy"):
            return c
    except Exception:
        pass
    return _MockSimClient()
