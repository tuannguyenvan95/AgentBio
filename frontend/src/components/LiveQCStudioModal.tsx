import React, { useState } from 'react';
import { 
  Sparkles, 
  Dna, 
  ShieldAlert, 
  ShieldCheck, 
  AlertTriangle, 
  Cpu, 
  Play, 
  Loader2, 
  ArrowRight,
  Terminal,
  FileText
} from 'lucide-react';

interface LiveQCStudioModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const LiveQCStudioModal: React.FC<LiveQCStudioModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [selectedPreset, setSelectedPreset] = useState<number>(0);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simResult, setSimResult] = useState<{
    verdict: string;
    fidelity: number;
    confidence: number;
    canary: string;
    reason: string;
    isSafe: boolean;
    hash: string;
  } | null>(null);

  if (!isOpen) return null;

  const presets = [
    {
      title: 'Humanized Anti-IL6 Monoclonal Antibody (Therapeutic)',
      category: 'Therapeutic Protein',
      intended: 'Immunotherapy targeting human Interleukin-6 for cytokine storm mitigation in severe autoimmune syndromes.',
      sampleFasta: `>MAB_IL6_HC_VERIFIED | Homo sapiens therapeutic IgG1 heavy chain
EVQLVESGGGLVQPGGSLRLSCAASGFTFSDYYMSWVRQAPGKGLEWVGFIRNKANGYTTEYSASVKGRFTISRDNSKNTLYLQMNSLRAEDTAVYYCARDSGYDFDYWGQGTLVTVSS
Mean Q-Score: 39.8 | Alignment Fidelity: 99.4% | ORF Intact: YES
Purity: High | Pathogen Homology: 0.0%`,
      expectedVerdict: 'BIO_SYNTHESIS_VERIFIED',
      expectedFidelity: 99,
      expectedReason: 'Clean 99.4% full-length alignment matching therapeutic monoclonal antibody heavy chain. Zero toxin homology or prohibited select agent detected.',
      isSafe: true,
      hash: '3a1f89c02d8471e98bb4f2c5d18e904b7321e847c21059f14d89a2bc31e780a1',
    },
    {
      title: 'Prohibited Botulinum Neurotoxin Homolog (Dual-Use Pathogen)',
      category: 'Prohibited Pathogen',
      intended: 'Sub-cloning enzymatic domain for putative zinc metalloprotease biochemical characterization.',
      sampleFasta: `>SELECT_AGENT_HOMOLOGY_ALERT | Dual-Use Biological Vector
MKTLSLIVLGLVVSVGAASAPQNTISNDNIIYNSKDSNFSKIFQSLYDLIKNNGVKPGFGYNSLVNNFKN
Homology Match: Clostridium botulinum type A catalytic light chain (BoNT/A)
Potency: EXTREME. Tier 1 Dual-Use Toxin. Mandatory Quarantine Enforced.`,
      expectedVerdict: 'BIOHAZARD_BLOCKED',
      expectedFidelity: 96,
      expectedReason: 'CRITICAL BIOSECURITY INTERCEPTION: Codons match BoNT/A zinc-endopeptidase catalytic domain. Prohibited Tier 1 select agent toxin. Escrow slashed to Biosecurity Reserve.',
      isSafe: false,
      hash: '9f81a7bc5210984de2a3b11029c78a4f913d80b4e287c4f1a2380de591b72a44',
    },
    {
      title: 'Industrial Beta-Glucosidase (Frame-Shift Defective Mutant)',
      category: 'Defective Sequence',
      intended: 'High-temperature industrial enzyme for circular biomass lignocellulose degradation.',
      sampleFasta: `>BETA_GLUC_MUT_FAIL | Sample batch 4112
ATGAAACTGGCCTCG---GCCCTGGCCCTGTCCTCCGCCCTGGCC
Frame-shift deletion detected at Codon 44 (Delta-T). Premature stop codon TAA at residue 52.
Intact full-length target: 21.4%. Purity: FAILED.`,
      expectedVerdict: 'SEQUENCE_DEFECTIVE',
      expectedFidelity: 24,
      expectedReason: 'Severe frame-shift deletion at residue 44 causing premature termination. Fidelity score is 24% (well below the required 80% threshold). Refund granted.',
      isSafe: true,
      hash: 'e812d4a02c918bf024a56b7c89f1345d2091ea45c8297b41e0391abf81e74012',
    }
  ];

  const handleRunSimulation = () => {
    setIsSimulating(true);
    setSimResult(null);

    const active = presets[selectedPreset];
    setTimeout(() => {
      setSimResult({
        verdict: active.expectedVerdict,
        fidelity: active.expectedFidelity,
        confidence: 98,
        canary: 'CANARY_AGENT_BIO_SAFETY_V1',
        reason: active.expectedReason,
        isSafe: active.isSafe,
        hash: active.hash,
      });
      setIsSimulating(false);
    }, 1200);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fadeIn overflow-y-auto">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-2xl w-full p-6 sm:p-8 my-8 text-slate-900">
        
        {/* Header */}
        <div className="flex items-start justify-between pb-5 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center shadow-inner">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-slate-900">
                  GenVM Biosecurity & QC Simulation Studio
                </h3>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200">
                  Interactive Simulator
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Test how GenLayer subjective consensus juries evaluate live sequence reads
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 font-semibold p-1"
          >
            ✕
          </button>
        </div>

        {/* Vector Selection */}
        <div className="mt-5">
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
            Select Test Sample Vector
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            {presets.map((p, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setSelectedPreset(idx);
                  setSimResult(null);
                }}
                className={`p-3 rounded-2xl text-left border transition-all text-xs ${
                  selectedPreset === idx
                    ? 'border-emerald-500 bg-emerald-50/60 ring-2 ring-emerald-500/20'
                    : 'border-slate-200 bg-slate-50 hover:bg-slate-100'
                }`}
              >
                <div className="font-bold text-slate-900 line-clamp-1">{p.title}</div>
                <div className="text-[10px] font-semibold text-slate-500 mt-1">{p.category}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Selected Sample Preview */}
        <div className="mt-4 p-4 rounded-2xl bg-slate-900 text-slate-200 text-xs font-mono">
          <div className="flex items-center justify-between text-[10px] text-slate-400 uppercase tracking-wider pb-2 border-b border-slate-800">
            <span className="flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-teal-400" />
              <span>Simulated Sequencing QC Input (FASTA)</span>
            </span>
            <span className="text-emerald-400 font-sans font-bold">gl.nondet.web.render</span>
          </div>
          <pre className="mt-3 text-[11px] leading-relaxed overflow-x-auto whitespace-pre-wrap text-teal-300 font-mono">
            {presets[selectedPreset].sampleFasta}
          </pre>
        </div>

        {/* Run Button */}
        <div className="mt-4 flex justify-end">
          <button
            onClick={handleRunSimulation}
            disabled={isSimulating}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold shadow-md transition-all active:scale-[0.98] disabled:opacity-50"
          >
            {isSimulating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-teal-400" />
                <span>Simulating GenVM Non-Det Consensus...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 text-emerald-400" />
                <span>Execute On-Chain Consensus Simulation</span>
              </>
            )}
          </button>
        </div>

        {/* Simulation Output */}
        {simResult && (
          <div className="mt-5 p-5 rounded-2xl bg-slate-50 border border-slate-200 animate-fadeIn space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
                  Consensus Output
                </span>
                <span className="font-mono text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold border border-emerald-200">
                  CANARY: {simResult.canary}
                </span>
              </div>
              <span className="font-mono text-xs font-bold text-teal-700">
                Confidence: {simResult.confidence}%
              </span>
            </div>

            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-xl border ${
                simResult.verdict === 'BIO_SYNTHESIS_VERIFIED'
                  ? 'bg-emerald-50 border-emerald-300 text-emerald-700'
                  : simResult.verdict === 'BIOHAZARD_BLOCKED'
                  ? 'bg-orange-50 border-orange-300 text-orange-700'
                  : 'bg-amber-50 border-amber-300 text-amber-700'
              }`}>
                {simResult.verdict === 'BIO_SYNTHESIS_VERIFIED' && <ShieldCheck className="w-5 h-5 text-emerald-600" />}
                {simResult.verdict === 'BIOHAZARD_BLOCKED' && <ShieldAlert className="w-5 h-5 text-orange-600" />}
                {simResult.verdict === 'SEQUENCE_DEFECTIVE' && <AlertTriangle className="w-5 h-5 text-amber-600" />}
              </div>
              <div>
                <div className="font-display font-black text-slate-900 text-base">
                  {simResult.verdict}
                </div>
                <div className="text-xs text-slate-500">
                  Fidelity Score: <span className="font-bold font-mono">{simResult.fidelity}%</span> (Benchmark: ≥80%)
                </div>
              </div>
            </div>

            <p className="text-xs text-slate-700 font-sans leading-relaxed bg-white p-3.5 rounded-xl border border-slate-200">
              {simResult.reason}
            </p>

            <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono pt-1">
              <span>SHA-256 Digest:</span>
              <span className="truncate max-w-[320px]">{simResult.hash}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
