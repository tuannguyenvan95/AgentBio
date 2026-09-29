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
  Zap,
  Ban
} from 'lucide-react';
import { BioOrderData } from '../config/genlayer';
import { formatGen, getStatusMeta, truncateAddress } from '../utils/helpers';

interface BioForensicWorkbenchProps {
  order: BioOrderData | null;
  currentUser: string | null;
  onOpenSubmitProof: (order: BioOrderData) => void;
  onOpenDispute: (order: BioOrderData) => void;
  onAdjudicate: (orderId: number) => Promise<void>;
  onFinalize: (orderId: number) => Promise<void>;
  onCancel: (orderId: number) => Promise<void>;
  isProcessing: boolean;
}

export const BioForensicWorkbench: React.FC<BioForensicWorkbenchProps> = ({
  order,
  currentUser,
  onOpenSubmitProof,
  onOpenDispute,
  onAdjudicate,
  onFinalize,
  onCancel,
  isProcessing,
}) => {
  const [copiedHash, setCopiedHash] = useState(false);
  const [activeTab, setActiveTab] = useState<'alignment' | 'biosecurity' | 'metadata'>('alignment');

  if (!order) {
    return (
      <div className="bg-white rounded-3xl border border-slate-200 p-8 sm:p-12 text-center shadow-sm relative overflow-hidden">
        <div className="w-16 h-16 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-4 border border-emerald-100 shadow-inner">
          <Dna className="w-8 h-8 animate-pulse" />
        </div>
        <h3 className="font-display text-lg font-bold text-slate-900">
          Genomic Cleanroom Forensic Workbench
        </h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto mt-2 leading-relaxed">
          Select any synthesis order from the ledger below or commission a new DNA order to activate the on-chain nucleotide alignment radar, biosecurity screening telemetry, and consensus dossier.
        </p>
      </div>
    );
  }

  const statusMeta = getStatusMeta(order.status);
  const isResearcher = currentUser && currentUser.toLowerCase() === order.researcher.toLowerCase();
  const isFoundry = currentUser && currentUser.toLowerCase() === order.foundry.toLowerCase();

  // Radial calculation for fidelity gauge
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (order.fidelity_score / 100) * circumference;

  const handleCopyHash = () => {
    if (order.evidence_hash) {
      navigator.clipboard.writeText(order.evidence_hash);
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    }
  };

  // Generate simulated nucleotide comparison snippet based on fidelity
  const sampleSpecSeq = "ATG GTG CGT GTC CTG GTC CTG GCG CTG CTG GCG CTG GCC TCG GCC TCC GCC CTG GCC TGG CCT CAG";
  const sampleQCVerified = "ATG GTG CGT GTC CTG GTC CTG GCG CTG CTG GCG CTG GCC TCG GCC TCC GCC CTG GCC TGG CCT CAG";
  const sampleQCDefective = "ATG GTG CGT GTC CTG GTC CTG GCG CTG CTG --- CTG GCC TCG GCC TAA GCC CTG GCC TGG CCT CAG";
  const activeQCSeq = order.fidelity_score >= 80 ? sampleQCVerified : (order.status >= 2 ? sampleQCDefective : "AWAITING_FOUNDRY_QC_SUBMISSION_FOR_ALIGNMENT_DIGEST");

  return (
    <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden mb-8 transition-all">
      
      {/* Workbench Header */}
      <div className="p-6 sm:p-7 border-b border-slate-100 bg-slate-50/60 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white flex items-center justify-center shadow-md shadow-emerald-500/20 shrink-0">
            <Microscope className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-xs font-bold px-2.5 py-1 rounded-lg bg-slate-200/70 text-slate-800 border border-slate-300">
                BIO-ORDER #{order.order_id}
              </span>
              <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${statusMeta.badgeBg}`}>
                <span className={`w-2 h-2 rounded-full ${statusMeta.ledColor}`} />
                <span>{statusMeta.label}</span>
              </div>
            </div>
            <p className="text-xs text-slate-500 mt-1 font-medium line-clamp-1">
              {order.target_protein_function}
            </p>
          </div>
        </div>

        {/* Financial Escrow Metric */}
        <div className="flex items-center gap-4 bg-white px-4 py-2.5 rounded-2xl border border-slate-200 shadow-sm self-start md:self-auto">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              Escrow Locked
            </span>
            <div className="flex items-baseline gap-1">
              <span className="font-display font-black text-xl text-slate-900 font-mono">
                {formatGen(order.escrow_amount)}
              </span>
              <span className="text-xs font-bold text-emerald-600">GEN</span>
            </div>
          </div>
          {order.dispute_bond && BigInt(order.dispute_bond) > 0n && (
            <div className="border-l border-slate-100 pl-3">
              <span className="text-[10px] font-bold uppercase tracking-wider text-rose-500 block">
                Dispute Bond
              </span>
              <span className="font-mono text-xs font-bold text-slate-800">
                {formatGen(order.dispute_bond)} GEN
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Main Dual-Column Telemetry Grid */}
      <div className="p-6 sm:p-7 grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Radial Fidelity Radar & Biosecurity Status (5 Cols) */}
        <div className="lg:col-span-5 flex flex-col justify-between space-y-5 border-b lg:border-b-0 lg:border-r border-slate-100 lg:pr-6 pb-6 lg:pb-0">
          
          {/* Radial Fidelity Gauge */}
          <div className="p-5 rounded-2xl bg-slate-50/70 border border-slate-200 flex items-center justify-between gap-4">
            <div className="relative w-28 h-28 flex items-center justify-center shrink-0">
              <svg className="w-28 h-28 transform -rotate-90">
                <circle
                  cx="56"
                  cy="56"
                  r={radius}
                  stroke="#E2E8F0"
                  strokeWidth="8"
                  fill="transparent"
                />
                <circle
                  cx="56"
                  cy="56"
                  r={radius}
                  stroke={
                    order.fidelity_score >= 80
                      ? '#059669'
                      : order.verdict === 'BIOHAZARD_BLOCKED'
                      ? '#EA580C'
                      : '#D97706'
                  }
                  strokeWidth="8"
                  strokeDasharray={circumference}
                  strokeDashoffset={order.status >= 2 ? strokeDashoffset : circumference}
                  strokeLinecap="round"
                  fill="transparent"
                  className="transition-all duration-1000 ease-out"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                <span className="font-display font-black text-2xl text-slate-900 tracking-tight font-mono">
                  {order.status >= 2 ? `${order.fidelity_score}%` : '---'}
                </span>
                <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">
                  Fidelity
                </span>
              </div>
            </div>

            <div className="text-xs space-y-1.5 flex-1">
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Alignment Quality Index
              </div>
              <div className="font-bold text-slate-800 text-sm">
                {order.status < 2
                  ? 'Awaiting Adjudication'
                  : order.fidelity_score >= 80
                  ? '≥80% Verified Precision'
                  : 'Fidelity Below Benchmark'}
              </div>
              <p className="text-[11px] text-slate-500 leading-relaxed">
                Acceptance threshold is strictly 80.0%. Frame-shifts, codon deletions or truncations fail payment settlement.
              </p>
            </div>
          </div>

          {/* Biosecurity Screening Assessment */}
          <div className="p-5 rounded-2xl bg-slate-50/70 border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-emerald-600" />
                <span>Biosecurity Dual-Use Screen</span>
              </span>
              <span className="font-mono text-xs font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded-md border border-teal-200">
                Confidence: {order.confidence}%
              </span>
            </div>

            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-xl border ${statusMeta.badgeBg}`}>
                {order.verdict === 'BIO_SYNTHESIS_VERIFIED' ? (
                  <ShieldCheck className="w-5 h-5 text-emerald-600" />
                ) : order.verdict === 'BIOHAZARD_BLOCKED' ? (
                  <ShieldAlert className="w-5 h-5 text-orange-600" />
                ) : (
                  <Activity className="w-5 h-5 text-slate-500" />
                )}
              </div>
              <div>
                <div className="font-display font-black text-slate-900 text-sm">
                  {order.verdict === 'BIO_SYNTHESIS_VERIFIED' && 'CERTIFIED BIOSECURE & AUTHENTIC'}
                  {order.verdict === 'BIOHAZARD_BLOCKED' && 'PROHIBITED PATHOGEN INTERCEPTED'}
                  {order.verdict === 'SEQUENCE_DEFECTIVE' && 'SYNTHESIS DEFECTIVE (REFUND ELIGIBLE)'}
                  {order.verdict === 'PENDING' && 'CONSENSUS AUDIT PENDING'}
                </div>
                <div className="text-[11px] text-slate-500">
                  {order.verdict === 'BIOHAZARD_BLOCKED'
                    ? 'Immediate escrow slash to DeSci Biosecurity Reserve'
                    : 'Verified by autonomous GenLayer subjective consensus'}
                </div>
              </div>
            </div>

            {/* AI Jury Rationale */}
            {order.reason && (
              <div className="mt-2 p-3 rounded-xl bg-white border border-slate-200 text-[11px] text-slate-700 leading-relaxed font-sans">
                <strong className="text-slate-900 font-semibold block mb-0.5">
                  Forensic Opinion:
                </strong>
                {order.reason}
              </div>
            )}
          </div>

          {/* Evidence SHA-256 Digest */}
          {order.evidence_hash && (
            <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-between gap-2 text-xs">
              <div className="flex items-center gap-2 overflow-hidden">
                <Hash className="w-4 h-4 text-slate-400 shrink-0" />
                <div className="truncate">
                  <span className="text-[10px] text-slate-400 uppercase font-bold block">
                    Evidence SHA-256 Digest
                  </span>
                  <span className="font-mono text-[11px] text-slate-700 truncate block">
                    {order.evidence_hash}
                  </span>
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

        {/* Right Column: Interactive Nucleotide Codon Matrix & Sequence Inspector (7 Cols) */}
        <div className="lg:col-span-7 flex flex-col justify-between space-y-4">
          
          {/* Sub-Tabs */}
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab('alignment')}
                className={`px-3 py-1 rounded-xl text-xs font-bold transition-all ${
                  activeTab === 'alignment'
                    ? 'bg-slate-900 text-white shadow-sm'
                    : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                Codon Alignment
              </button>
              <button
                onClick={() => setActiveTab('biosecurity')}
                className={`px-3 py-1 rounded-xl text-xs font-bold transition-all ${
                  activeTab === 'biosecurity'
                    ? 'bg-slate-900 text-white shadow-sm'
                    : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                Biosecurity Rules
              </button>
              <button
                onClick={() => setActiveTab('metadata')}
                className={`px-3 py-1 rounded-xl text-xs font-bold transition-all ${
                  activeTab === 'metadata'
                    ? 'bg-slate-900 text-white shadow-sm'
                    : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                On-Chain Metadata
              </button>
            </div>

            <div className="flex items-center gap-2 text-xs font-mono text-slate-500">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>GenVM Non-Det Render</span>
            </div>
          </div>

          {/* Tab 1: Codon Alignment Matrix */}
          {activeTab === 'alignment' && (
            <div className="space-y-3 font-mono text-xs">
              <div className="p-4 rounded-2xl bg-slate-900 text-slate-100 space-y-3 shadow-inner">
                <div>
                  <div className="flex justify-between text-[10px] text-slate-400 uppercase tracking-wider mb-1 font-bold">
                    <span>Target Design Specification (Reference ORF)</span>
                    <span className="text-emerald-400">FASTA Input</span>
                  </div>
                  <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 text-emerald-400 text-xs overflow-x-auto whitespace-pre tracking-wider">
                    {sampleSpecSeq}
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-[10px] text-slate-400 uppercase tracking-wider mb-1 font-bold">
                    <span>Foundry Sequenced Read (Sanger / NGS)</span>
                    <span className={order.fidelity_score >= 80 ? 'text-teal-400' : 'text-amber-400'}>
                      QC Proof
                    </span>
                  </div>
                  <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 text-teal-300 text-xs overflow-x-auto whitespace-pre tracking-wider">
                    {activeQCSeq}
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800 grid grid-cols-3 gap-2 text-[10px] text-slate-400 font-sans">
                  <div>
                    <span className="block text-slate-500">Mean Q-Score:</span>
                    <span className="font-mono text-slate-200 font-bold">
                      {order.status >= 2 ? (order.fidelity_score >= 80 ? '39.8 (99.99%)' : '21.2 (Low)') : 'Pending'}
                    </span>
                  </div>
                  <div>
                    <span className="block text-slate-500">ORF Reading Frame:</span>
                    <span className="font-mono text-slate-200 font-bold">
                      {order.status >= 2 ? (order.fidelity_score >= 80 ? 'Intact Full Length' : 'Frameshift Codon 44') : 'Pending'}
                    </span>
                  </div>
                  <div>
                    <span className="block text-slate-500">Residual Contaminants:</span>
                    <span className="font-mono text-slate-200 font-bold">
                      {order.status >= 2 ? '< 0.001% (Clean)' : 'Pending'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Resource Links */}
              <div className="grid grid-cols-2 gap-3 text-xs font-sans">
                <a
                  href={order.sequence_spec_url}
                  target="_blank"
                  rel="noreferrer"
                  className="p-3 rounded-xl border border-slate-200 bg-slate-50 hover:bg-emerald-50/50 hover:border-emerald-300 transition-all flex items-center justify-between"
                >
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase block">Specification Spec URL</span>
                    <span className="font-mono text-emerald-700 text-[11px] truncate block max-w-[180px]">
                      {order.sequence_spec_url}
                    </span>
                  </div>
                  <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                </a>

                {order.qc_report_url ? (
                  <a
                    href={order.qc_report_url}
                    target="_blank"
                    rel="noreferrer"
                    className="p-3 rounded-xl border border-slate-200 bg-slate-50 hover:bg-purple-50/50 hover:border-purple-300 transition-all flex items-center justify-between"
                  >
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 uppercase block">Sequencing QC Report</span>
                      <span className="font-mono text-purple-700 text-[11px] truncate block max-w-[180px]">
                        {order.qc_report_url}
                      </span>
                    </div>
                    <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                  </a>
                ) : (
                  <div className="p-3 rounded-xl border border-dashed border-slate-200 bg-slate-50 text-slate-400 text-xs flex items-center">
                    Foundry has not yet submitted sequencing QC report.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Tab 2: Biosecurity Screen Rules */}
          {activeTab === 'biosecurity' && (
            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-3 text-xs font-sans">
              <h4 className="font-bold text-slate-900 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>On-Chain Biosecurity Dual-Use Protocol Guidelines</span>
              </h4>
              <ul className="space-y-2 text-slate-600 text-[11px] leading-relaxed">
                <li className="flex items-start gap-2">
                  <span className="font-bold text-emerald-700">1.</span>
                  <span><strong>Select Agent Screening:</strong> GenVM digests all sequences against international Tier 1 pathogen registries (e.g. Botulinum, Ricin, Smallpox virulence factors).</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="font-bold text-emerald-700">2.</span>
                  <span><strong>80% Fidelity Requirement:</strong> Only sequences with full-length integrity and at least 80% identity disburse payment to the synthesis provider.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="font-bold text-orange-600">3.</span>
                  <span><strong>Slashing Penalty:</strong> Parties attempting to secretly synthesize weaponized toxins forfeit 100% of their escrow into the DeSci Biosecurity Reserve.</span>
                </li>
              </ul>
            </div>
          )}

          {/* Tab 3: On-Chain Metadata */}
          {activeTab === 'metadata' && (
            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 text-xs font-sans grid grid-cols-2 gap-4">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Researcher Address</span>
                <span className="font-mono text-slate-800 text-xs block truncate" title={order.researcher}>
                  {order.researcher}
                </span>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Foundry Address</span>
                <span className="font-mono text-slate-800 text-xs block truncate" title={order.foundry}>
                  {order.foundry}
                </span>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Created at Block Counter</span>
                <span className="font-mono text-slate-800 text-xs block">
                  {order.created_at_block || '0'}
                </span>
              </div>
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Audit Completed Block</span>
                <span className="font-mono text-slate-800 text-xs block">
                  {order.audit_completed_block || '0'}
                </span>
              </div>
            </div>
          )}

          {/* Bottom Action Chamber */}
          <div className="pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
            <div className="text-xs text-slate-500 font-medium">
              {order.status === 0 && 'Order open for DNA synthesis foundry claim.'}
              {order.status === 1 && 'Sequencing QC uploaded. Ready for on-chain AI adjudication.'}
              {order.status === 2 && '24-block cooling-off dispute window active before settlement.'}
              {order.status === 3 && 'Order fully settled and funds disbursed.'}
              {order.status === 4 && 'Funds confiscated to protocol reserve.'}
              {order.status === 5 && 'Refund disbursed to researcher.'}
              {order.status === 7 && 'Verdict actively contested under appeal.'}
            </div>

            <div className="flex items-center gap-2">
              {/* Status 0: Open */}
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
                      className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shadow-md shadow-purple-600/20 active:scale-[0.98] disabled:opacity-50"
                    >
                      <Microscope className="w-4 h-4" />
                      <span>Claim & Submit QC Proof</span>
                    </button>
                  )}
                </>
              )}

              {/* Status 1: In Synthesis */}
              {order.status === 1 && (
                <button
                  onClick={() => onAdjudicate(order.order_id)}
                  disabled={isProcessing}
                  className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-md shadow-teal-600/20 active:scale-[0.98] disabled:opacity-50"
                >
                  <Cpu className="w-4 h-4" />
                  <span>Convene AI Biosecurity Jury</span>
                </button>
              )}

              {/* Status 2: Cooling-off */}
              {order.status === 2 && (
                <>
                  <button
                    onClick={() => onOpenDispute(order)}
                    disabled={isProcessing}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100 text-xs font-bold transition-all"
                  >
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Appeal Verdict (10% Bond)</span>
                  </button>

                  <button
                    onClick={() => onFinalize(order.order_id)}
                    disabled={isProcessing}
                    className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20 active:scale-[0.98] disabled:opacity-50"
                  >
                    <CheckCircle className="w-4 h-4" />
                    <span>Finalize Settlement</span>
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
