import React, { useState } from 'react';
import { 
  FileSearch, 
  ExternalLink, 
  ShieldCheck, 
  ShieldAlert, 
  AlertTriangle, 
  Hash, 
  Copy, 
  Check, 
  Fingerprint,
  Calendar,
  Layers
} from 'lucide-react';
import { BioOrderData } from '../config/genlayer';
import { formatGen, getStatusMeta, truncateAddress } from '../utils/helpers';

interface SequenceInspectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  order: BioOrderData | null;
}

export const SequenceInspectorModal: React.FC<SequenceInspectorModalProps> = ({
  isOpen,
  onClose,
  order,
}) => {
  const [copiedHash, setCopiedHash] = useState(false);

  if (!isOpen || !order) return null;

  const statusMeta = getStatusMeta(order.status);

  const copyEvidenceHash = () => {
    if (order.evidence_hash) {
      navigator.clipboard.writeText(order.evidence_hash);
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fadeIn overflow-y-auto">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-2xl w-full p-6 sm:p-8 my-8 text-slate-900">
        
        {/* Header */}
        <div className="flex items-start justify-between pb-5 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center shadow-inner">
              <FileSearch className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-slate-900">
                  Biosecurity & Fidelity Forensic Dossier
                </h3>
                <span className="font-mono text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold border border-slate-200">
                  #{order.order_id}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                On-Chain Subjective Consensus Audit Trail • GenLayer Studionet
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

        {/* Status & Verdict Highlight */}
        <div className="mt-6 p-4 rounded-2xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-xl border ${statusMeta.badgeBg}`}>
              {order.verdict === 'BIO_SYNTHESIS_VERIFIED' ? (
                <ShieldCheck className="w-5 h-5 text-emerald-600" />
              ) : order.verdict === 'BIOHAZARD_BLOCKED' ? (
                <ShieldAlert className="w-5 h-5 text-orange-600" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-amber-600" />
              )}
            </div>
            <div>
              <div className="text-[11px] uppercase tracking-wider text-slate-400 font-bold">
                Consensus Verdict
              </div>
              <div className="font-display font-black text-slate-900 text-base">
                {order.verdict || 'PENDING ADJUDICATION'}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs font-semibold">
            <div className="text-right">
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Fidelity Score</span>
              <span className={`text-base font-extrabold ${order.fidelity_score >= 80 ? 'text-emerald-600' : 'text-amber-600'}`}>
                {order.fidelity_score}%
              </span>
            </div>
            <div className="w-px h-8 bg-slate-200" />
            <div className="text-right">
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Confidence</span>
              <span className="text-base font-extrabold text-teal-600">
                {order.confidence}%
              </span>
            </div>
          </div>
        </div>

        {/* Alignment Gauge Bar */}
        <div className="mt-4">
          <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1.5">
            <span>Synthesis Sequence Fidelity Benchmark</span>
            <span className="font-mono">{order.fidelity_score} / 100</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden border border-slate-200">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                order.fidelity_score >= 80
                  ? 'bg-gradient-to-r from-teal-500 to-emerald-500'
                  : order.verdict === 'BIOHAZARD_BLOCKED'
                  ? 'bg-gradient-to-r from-orange-500 to-red-500'
                  : 'bg-gradient-to-r from-amber-400 to-amber-500'
              }`}
              style={{ width: `${Math.max(5, order.fidelity_score)}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-slate-400 mt-1">
            <span>0% (Defective)</span>
            <span className="text-emerald-700 font-semibold">80% Acceptance Threshold</span>
            <span>100% (Identical)</span>
          </div>
        </div>

        {/* AI Biosecurity Jury Rationale */}
        <div className="mt-5">
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1.5">
            <Fingerprint className="w-3.5 h-3.5 text-teal-600" />
            <span>AI Biosecurity Officer Rationale</span>
          </label>
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-700 leading-relaxed font-sans">
            {order.reason || 'No adjudication rationale recorded yet.'}
          </div>
        </div>

        {/* Target Function Specification */}
        <div className="mt-4">
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">
            Target Protein / Enzyme Application
          </label>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-800">
            {order.target_protein_function}
          </div>
        </div>

        {/* Sequence & QC Report Links */}
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded-xl border border-slate-200 bg-white">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
              Specification URL
            </span>
            <a
              href={order.sequence_spec_url}
              target="_blank"
              rel="noreferrer"
              className="text-emerald-600 hover:text-emerald-700 font-mono text-[11px] flex items-center gap-1 truncate"
            >
              <span className="truncate">{order.sequence_spec_url}</span>
              <ExternalLink className="w-3 h-3 shrink-0" />
            </a>
          </div>

          <div className="p-3 rounded-xl border border-slate-200 bg-white">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
              QC Sequencing Run URL
            </span>
            {order.qc_report_url ? (
              <a
                href={order.qc_report_url}
                target="_blank"
                rel="noreferrer"
                className="text-purple-600 hover:text-purple-700 font-mono text-[11px] flex items-center gap-1 truncate"
              >
                <span className="truncate">{order.qc_report_url}</span>
                <ExternalLink className="w-3 h-3 shrink-0" />
              </a>
            ) : (
              <span className="text-slate-400 italic">Not submitted yet</span>
            )}
          </div>
        </div>

        {/* Evidence Hash Snapshot */}
        {order.evidence_hash && (
          <div className="mt-4 p-3 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 overflow-hidden">
              <Hash className="w-4 h-4 text-slate-400 shrink-0" />
              <div className="truncate">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">
                  Immutable Evidence SHA-256 Digest
                </span>
                <span className="font-mono text-xs text-slate-700 truncate block">
                  {order.evidence_hash}
                </span>
              </div>
            </div>
            <button
              onClick={copyEvidenceHash}
              className="p-1.5 rounded-lg bg-white border border-slate-200 text-slate-600 hover:text-slate-900 shrink-0"
              title="Copy hash"
            >
              {copiedHash ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
        )}

        {/* Participants & Financials */}
        <div className="mt-5 pt-4 border-t border-slate-100 grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px]">
          <div>
            <span className="text-slate-400 block font-bold uppercase text-[9px]">Escrow Amount</span>
            <span className="font-bold text-slate-900 font-mono text-xs">
              {formatGen(order.escrow_amount)} GEN
            </span>
          </div>

          <div>
            <span className="text-slate-400 block font-bold uppercase text-[9px]">Researcher</span>
            <span className="font-mono text-slate-700 text-xs truncate block" title={order.researcher}>
              {truncateAddress(order.researcher)}
            </span>
          </div>

          <div>
            <span className="text-slate-400 block font-bold uppercase text-[9px]">Foundry</span>
            <span className="font-mono text-slate-700 text-xs truncate block" title={order.foundry}>
              {truncateAddress(order.foundry)}
            </span>
          </div>

          <div>
            <span className="text-slate-400 block font-bold uppercase text-[9px]">Dispute Bond</span>
            <span className="font-mono text-slate-700 text-xs">
              {order.dispute_bond ? `${formatGen(order.dispute_bond)} GEN` : '0 GEN'}
            </span>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition-all"
          >
            Close Dossier
          </button>
        </div>
      </div>
    </div>
  );
};
