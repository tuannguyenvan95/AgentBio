import React, { useState } from 'react';
import { 
  Dna, 
  ShieldCheck, 
  ShieldAlert, 
  AlertTriangle, 
  ExternalLink, 
  Microscope, 
  Cpu, 
  CheckCircle, 
  Hash, 
  Copy, 
  Check, 
  Fingerprint, 
  Clock, 
  Layers, 
  ArrowRight,
  Crosshair,
  Activity,
  FileCode,
  Shield,
  Ban,
  FileSearch,
  CheckCircle2
} from 'lucide-react';
import { BioOrderData } from '../config/genlayer';
import { formatGen, getStatusMeta, truncateAddress } from '../utils/helpers';

interface GenomicInspectionCockpitProps {
  order: BioOrderData | null;
  currentUser: string | null;
  onOpenSubmitProof: (order: BioOrderData) => void;
  onOpenInspector: (order: BioOrderData) => void;
  onOpenDispute: (order: BioOrderData) => void;
  onAdjudicate: (orderId: number) => Promise<void>;
  onFinalize: (orderId: number) => Promise<void>;
  onCancel: (orderId: number) => Promise<void>;
  isProcessing: boolean;
}

export const GenomicInspectionCockpit: React.FC<GenomicInspectionCockpitProps> = ({
  order,
  currentUser,
  onOpenSubmitProof,
  onOpenInspector,
  onOpenDispute,
  onAdjudicate,
  onFinalize,
  onCancel,
  isProcessing,
}) => {
  const [copiedHash, setCopiedHash] = useState(false);

  if (!order) {
    return (
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-12 text-center h-[calc(100vh-10rem)] max-h-[860px] flex flex-col items-center justify-center">
        <div className="w-16 h-16 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4 border border-emerald-100 shadow-inner">
          <Crosshair className="w-8 h-8 animate-pulse" />
        </div>
        <h3 className="font-display text-lg font-bold text-slate-900">
          Awaiting Synthesis Order Selection
        </h3>
        <p className="text-xs text-slate-500 max-w-sm mt-2 leading-relaxed">
          Select an order from the left pipeline or commission a new DNA sequence to initialize real-time nucleotide alignment and biosecurity screening.
        </p>
      </div>
    );
  }

  const statusMeta = getStatusMeta(order.status);
  const isResearcher = currentUser && currentUser.toLowerCase() === order.researcher.toLowerCase();
  const isFoundry = currentUser && currentUser.toLowerCase() === order.foundry.toLowerCase();

  // Radial calculation for fidelity meter
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (order.fidelity_score / 100) * circumference;

  const handleCopyHash = () => {
    if (order.evidence_hash) {
      navigator.clipboard.writeText(order.evidence_hash);
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    }
  };

  // Codon base sequences for visual inspection
  const specCodons = [
    { codon: 'ATG', aa: 'Met', status: 'match' },
    { codon: 'GTG', aa: 'Val', status: 'match' },
    { codon: 'CGT', aa: 'Arg', status: 'match' },
    { codon: 'GTC', aa: 'Val', status: 'match' },
    { codon: 'CTG', aa: 'Leu', status: 'match' },
    { codon: 'GTC', aa: 'Val', status: 'match' },
    { codon: 'CTG', aa: 'Leu', status: 'match' },
    { codon: 'GCG', aa: 'Ala', status: 'match' },
    { codon: 'CTG', aa: 'Leu', status: 'match' },
    { codon: 'CTG', aa: 'Leu', status: 'match' },
  ];

  const qcCodonsVerified = [
    { codon: 'ATG', aa: 'Met', status: 'match' },
    { codon: 'GTG', aa: 'Val', status: 'match' },
    { codon: 'CGT', aa: 'Arg', status: 'match' },
    { codon: 'GTC', aa: 'Val', status: 'match' },
    { codon: 'CTG', aa: 'Leu', status: 'match' },
    { codon: 'GTC', aa: 'Val', status: 'match' },
    { codon: 'CTG', aa: 'Leu', status: 'match' },
    { codon: 'GCG', aa: 'Ala', status: 'match' },
    { codon: 'CTG', aa: 'Leu', status: 'match' },
    { codon: 'CTG', aa: 'Leu', status: 'match' },
  ];

  const qcCodonsDefective = [
    { codon: 'ATG', aa: 'Met', status: 'match' },
    { codon: 'GTG', aa: 'Val', status: 'match' },
    { codon: 'CGT', aa: 'Arg', status: 'match' },
    { codon: 'GTC', aa: 'Val', status: 'match' },
    { codon: '---', aa: 'DEL', status: 'error' },
    { codon: 'GTC', aa: 'Val', status: 'mismatch' },
    { codon: 'CTG', aa: 'Leu', status: 'mismatch' },
    { codon: 'TAA', aa: 'STP', status: 'error' },
    { codon: '---', aa: 'TRN', status: 'error' },
    { codon: '---', aa: 'TRN', status: 'error' },
  ];

  const currentQCCodons = order.fidelity_score >= 80 ? qcCodonsVerified : qcCodonsDefective;

  return (
    <div className="bg-white rounded-3xl border border-slate-200 shadow-sm flex flex-col h-[calc(100vh-10rem)] max-h-[860px] overflow-hidden">
      
      {/* Top Banner: ID, Status, Escrow, Addresses */}
      <div className="p-5 sm:p-6 border-b border-slate-100 bg-slate-50/60 shrink-0">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white flex items-center justify-center shadow-md shadow-emerald-500/20 shrink-0">
              <Microscope className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-mono text-xs font-black px-2 py-0.5 rounded-lg bg-slate-900 text-white">
                  ORDER #{order.order_id}
                </span>
                <div className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${statusMeta.badgeBg}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${statusMeta.ledColor}`} />
                  <span>{statusMeta.label}</span>
                </div>
              </div>
              <p className="text-xs font-bold text-slate-800 mt-1 line-clamp-1">
                {order.target_protein_function}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 self-end sm:self-auto">
            <div className="text-right">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Escrow Amount</span>
              <span className="font-display font-black text-lg text-slate-900 font-mono">
                {formatGen(order.escrow_amount)} <span className="text-xs font-bold text-emerald-600">GEN</span>
              </span>
            </div>
            <button
              onClick={() => onOpenInspector(order)}
              className="p-2 rounded-xl border border-slate-200 bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors"
              title="Open Forensic Dossier"
            >
              <FileSearch className="w-4 h-4 text-teal-600" />
            </button>
          </div>
        </div>

        {/* Addresses & Duration Details */}
        <div className="mt-3 pt-3 border-t border-slate-200/60 grid grid-cols-2 sm:grid-cols-4 gap-2 text-[10px] text-slate-500 font-mono">
          <div>
            <span className="text-slate-400 uppercase font-bold block text-[9px]">Researcher:</span>
            <span className="truncate block" title={order.researcher}>{truncateAddress(order.researcher)}</span>
          </div>
          <div>
            <span className="text-slate-400 uppercase font-bold block text-[9px]">DNA Foundry:</span>
            <span className="truncate block" title={order.foundry}>{truncateAddress(order.foundry)}</span>
          </div>
          <div>
            <span className="text-slate-400 uppercase font-bold block text-[9px]">Duration Limit:</span>
            <span>{order.expires_at_block || '5000 Blocks'}</span>
          </div>
          <div>
            <span className="text-slate-400 uppercase font-bold block text-[9px]">Dispute Bond:</span>
            <span>{order.dispute_bond ? `${formatGen(order.dispute_bond)} GEN` : '0 GEN'}</span>
          </div>
        </div>
      </div>

      {/* Main Inspection Chamber (Scrollable) */}
      <div className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-6">
        
        {/* Dual Meter HUD: Alignment Radial + Biosecurity Threat Gauge */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          
          {/* Gauge 1: Sequence Alignment Fidelity */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-between gap-4">
            <div className="relative w-24 h-24 flex items-center justify-center shrink-0">
              <svg className="w-24 h-24 transform -rotate-90">
                <circle
                  cx="48"
                  cy="48"
                  r={radius}
                  stroke="#E2E8F0"
                  strokeWidth="7"
                  fill="transparent"
                />
                <circle
                  cx="48"
                  cy="48"
                  r={radius}
                  stroke={
                    order.fidelity_score >= 80
                      ? '#059669'
                      : order.verdict === 'BIOHAZARD_BLOCKED'
                      ? '#EA580C'
                      : '#D97706'
                  }
                  strokeWidth="7"
                  strokeDasharray={circumference}
                  strokeDashoffset={order.status >= 2 ? strokeDashoffset : circumference}
                  strokeLinecap="round"
                  fill="transparent"
                  className="transition-all duration-1000 ease-out"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                <span className="font-display font-black text-xl text-slate-900 font-mono">
                  {order.status >= 2 ? `${order.fidelity_score}%` : '---'}
                </span>
                <span className="text-[8px] font-bold text-slate-400 uppercase">
                  Fidelity
                </span>
              </div>
            </div>

            <div className="text-xs space-y-1 flex-1">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">
                Sequence Quality
              </span>
              <div className="font-bold text-slate-800 text-sm">
                {order.status < 2
                  ? 'Awaiting QC Run'
                  : order.fidelity_score >= 80
                  ? '≥80% Valid Precision'
                  : 'Fidelity Defective'}
              </div>
              <p className="text-[11px] text-slate-500 leading-relaxed">
                Evaluated against the target open reading frame on GenLayer Studionet.
              </p>
            </div>
          </div>

          {/* Gauge 2: Biosecurity Threat Screening */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-between gap-4">
            <div className={`w-20 h-20 rounded-2xl border flex items-center justify-center shrink-0 ${statusMeta.badgeBg}`}>
              {order.verdict === 'BIO_SYNTHESIS_VERIFIED' ? (
                <ShieldCheck className="w-10 h-10 text-emerald-600" />
              ) : order.verdict === 'BIOHAZARD_BLOCKED' ? (
                <ShieldAlert className="w-10 h-10 text-orange-600 animate-pulse" />
              ) : (
                <Shield className="w-10 h-10 text-slate-400" />
              )}
            </div>

            <div className="text-xs space-y-1 flex-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-bold text-slate-400">
                  Pathogen Shield
                </span>
                <span className="font-mono text-[10px] font-bold text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded border border-teal-200">
                  Conf: {order.confidence}%
                </span>
              </div>
              <div className="font-bold text-slate-800 text-sm">
                {order.verdict === 'BIO_SYNTHESIS_VERIFIED' && 'Verified Safe & Compliant'}
                {order.verdict === 'BIOHAZARD_BLOCKED' && 'Hazardous Toxin Intercepted'}
                {order.verdict === 'SEQUENCE_DEFECTIVE' && 'Safe (Sequence Defective)'}
                {order.verdict === 'PENDING' && 'Screening Standby'}
              </div>
              <p className="text-[11px] text-slate-500 leading-relaxed">
                Screened against international Tier 1 select agent & pathogen toxin registries.
              </p>
            </div>
          </div>
        </div>

        {/* Interactive Nucleotide Codon Matrix */}
        <div className="p-4 rounded-2xl bg-slate-900 text-slate-200 space-y-3 shadow-inner">
          <div className="flex items-center justify-between text-xs pb-2 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Dna className="w-4 h-4 text-emerald-400" />
              <span className="font-mono font-bold text-slate-200 text-xs">
                Interactive Codon Alignment Matrix
              </span>
            </div>
            <span className="font-mono text-[10px] text-teal-400">
              Loci 1 - 10 (High Res Alignment)
            </span>
          </div>

          {/* Reference Specification Track */}
          <div>
            <div className="text-[9px] uppercase font-bold text-slate-400 tracking-wider mb-1 font-mono">
              Reference Design Spec (FASTA):
            </div>
            <div className="grid grid-cols-10 gap-1.5">
              {specCodons.map((c, i) => (
                <div key={i} className="p-1 rounded bg-slate-800 border border-slate-700 text-center font-mono">
                  <div className="text-[10px] font-bold text-emerald-400">{c.codon}</div>
                  <div className="text-[8px] text-slate-400">{c.aa}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Sequenced QC Read Track */}
          <div>
            <div className="text-[9px] uppercase font-bold text-slate-400 tracking-wider mb-1 font-mono">
              Foundry Sequenced QC Read:
            </div>
            <div className="grid grid-cols-10 gap-1.5">
              {currentQCCodons.map((c, i) => (
                <div
                  key={i}
                  className={`p-1 rounded text-center font-mono border ${
                    c.status === 'match'
                      ? 'bg-slate-800/80 border-teal-500/50 text-teal-300'
                      : 'bg-rose-950/80 border-rose-500 text-rose-300'
                  }`}
                >
                  <div className="text-[10px] font-bold">{c.codon}</div>
                  <div className="text-[8px] opacity-75">{c.aa}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Readout Telemetry Footer */}
          <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[10px] text-slate-400 font-mono">
            <span>Mean Read Depth: 840x</span>
            <span>Contaminant Homology: 0.00%</span>
            <span>Alignment Mode: Semi-Global</span>
          </div>
        </div>

        {/* AI Biosecurity Officer Rationale */}
        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Fingerprint className="w-3.5 h-3.5 text-teal-600" />
              <span>AI Biosecurity Officer Rationale</span>
            </span>
            <span className="font-mono text-[10px] text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              Canary Token Verified
            </span>
          </div>
          <p className="text-xs text-slate-700 leading-relaxed font-sans bg-white p-3 rounded-xl border border-slate-200">
            {order.reason || 'Order is open. Awaiting sequencing proof submission by synthesis foundry.'}
          </p>
        </div>

        {/* Cooling-off 24-Block Dispute Window Progress Bar (if in status 2) */}
        {order.status === 2 && (
          <div className="p-4 rounded-2xl bg-blue-50/70 border border-blue-200 space-y-2 text-xs">
            <div className="flex items-center justify-between font-bold text-blue-900">
              <span className="flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-blue-600 animate-spin" />
                <span>24-Block Cooling-Off Dispute Window Active</span>
              </span>
              <span className="font-mono text-[11px]">Audit Block + 24</span>
            </div>
            <p className="text-[11px] text-blue-800 leading-relaxed">
              Either researcher or foundry may appeal this verdict by staking a 10% dispute bond. Escrow cannot be disbursed until this timelock expires uncontested.
            </p>
            <div className="w-full bg-blue-200/70 rounded-full h-2 overflow-hidden">
              <div className="bg-blue-600 h-full rounded-full w-2/3 animate-pulse" />
            </div>
          </div>
        )}

        {/* Evidence Hash Snapshot */}
        {order.evidence_hash && (
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between gap-2 text-xs">
            <div className="flex items-center gap-2 overflow-hidden">
              <Hash className="w-4 h-4 text-slate-400 shrink-0" />
              <div className="truncate">
                <span className="text-[9px] uppercase font-bold text-slate-400 block">Immutable Evidence SHA-256</span>
                <span className="font-mono text-[11px] text-slate-700 truncate block">{order.evidence_hash}</span>
              </div>
            </div>
            <button
              onClick={handleCopyHash}
              className="p-1.5 rounded-lg bg-white border border-slate-200 text-slate-600 hover:text-slate-900 shrink-0"
              title="Copy hash"
            >
              {copiedHash ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
        )}
      </div>

      {/* Bottom Execution Control Chamber */}
      <div className="p-4 sm:p-5 border-t border-slate-100 bg-slate-50/70 shrink-0 flex flex-wrap items-center justify-between gap-3">
        <div className="text-xs text-slate-500 font-medium">
          {order.status === 0 && 'Ready for DNA Foundry to claim and submit sequencing QC.'}
          {order.status === 1 && 'Sequencing proof submitted. Click below to convene on-chain AI Jury.'}
          {order.status === 2 && 'Cooling-off window active. Ready for appeal or settlement.'}
          {order.status === 3 && 'Order settled. Escrow disbursed to Foundry.'}
          {order.status === 4 && 'Biohazard blocked. Escrow slashed to Biosecurity Reserve.'}
          {order.status === 5 && 'Sequence defective. Full refund disbursed to Researcher.'}
          {order.status === 7 && 'Verdict under formal dispute appeal.'}
        </div>

        <div className="flex items-center gap-2">
          {order.status === 0 && (
            <>
              {isResearcher ? (
                <button
                  onClick={() => onCancel(order.order_id)}
                  disabled={isProcessing}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-rose-600 hover:bg-rose-50 disabled:opacity-50"
                >
                  <Ban className="w-3.5 h-3.5" />
                  <span>Cancel Order</span>
                </button>
              ) : (
                <button
                  onClick={() => onOpenSubmitProof(order)}
                  disabled={isProcessing}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shadow-md shadow-purple-600/20 active:scale-95 transition-all disabled:opacity-50"
                >
                  <Microscope className="w-4 h-4" />
                  <span>Claim & Submit QC Proof</span>
                </button>
              )}
            </>
          )}

          {order.status === 1 && (
            <button
              onClick={() => onAdjudicate(order.order_id)}
              disabled={isProcessing}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-md shadow-teal-600/20 active:scale-95 transition-all disabled:opacity-50"
            >
              <Cpu className="w-4 h-4" />
              <span>Convene AI Biosecurity Jury</span>
            </button>
          )}

          {order.status === 2 && (
            <>
              <button
                onClick={() => onOpenDispute(order)}
                disabled={isProcessing}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100 text-xs font-bold transition-all"
              >
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Appeal (10% Bond)</span>
              </button>

              <button
                onClick={() => onFinalize(order.order_id)}
                disabled={isProcessing}
                className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20 active:scale-95 transition-all disabled:opacity-50"
              >
                <CheckCircle className="w-4 h-4" />
                <span>Finalize Settlement</span>
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
