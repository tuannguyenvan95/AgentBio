import pytest
import json
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
