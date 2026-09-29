import React, { useState } from 'react';
import { Microscope, Loader2, Sparkles, ArrowRight } from 'lucide-react';
import { BioOrderData } from '../config/genlayer';
import { PRESET_FOUNDRY_PROOFS, formatGen } from '../utils/helpers';

interface SubmitProofModalProps {
  isOpen: boolean;
  onClose: () => void;
  order: BioOrderData | null;
  onSubmit: (orderId: number, qcReportUrl: string) => Promise<void>;
}

export const SubmitProofModal: React.FC<SubmitProofModalProps> = ({
  isOpen,
  onClose,
  order,
  onSubmit,
}) => {
  const [qcReportUrl, setQcReportUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !order) return null;

  const handleApplyPreset = (url: string) => {
    setQcReportUrl(url);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const cleanUrl = qcReportUrl.trim();
    if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
      setError('Valid public sequencing QC report URL (http/https) is required.');
      return;
    }

    try {
      setIsSubmitting(true);
      await onSubmit(order.order_id, cleanUrl);
      onClose();
    } catch (err: any) {
      console.error('Submit proof error:', err);
      setError(err?.message || 'Transaction failed on GenLayer Studionet.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-lg w-full p-6 sm:p-8 text-slate-900">
        
        {/* Header */}
        <div className="flex items-start justify-between pb-5 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center shadow-inner">
              <Microscope className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">Foundry QC Portal</h3>
              <p className="text-xs text-slate-500">Claim Order #{order.order_id} & Submit Sequencing Proof</p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="text-slate-400 hover:text-slate-600 font-semibold p-1"
          >
            ✕
          </button>
        </div>

        {/* Order Details Brief */}
        <div className="mt-5 p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-xs space-y-1.5">
          <div className="flex justify-between">
            <span className="text-slate-500">Escrow Value:</span>
            <span className="font-bold text-emerald-600 font-mono">
              {formatGen(order.escrow_amount)} GEN
            </span>
          </div>
          <div>
            <span className="text-slate-500 block">Biological Target:</span>
            <span className="font-medium text-slate-800 line-clamp-2">
              {order.target_protein_function}
            </span>
          </div>
        </div>

        {/* Preset Sequencing Proofs */}
        <div className="mt-5">
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-purple-600" />
            <span>Benchmark Sequencing Reports (Quick Pick)</span>
          </label>
          <div className="space-y-2">
            {PRESET_FOUNDRY_PROOFS.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleApplyPreset(preset.url)}
                className="w-full text-left p-3 rounded-xl border border-slate-200 bg-slate-50/70 hover:bg-purple-50/50 hover:border-purple-300 transition-all text-xs"
              >
                <div className="font-bold text-slate-800">{preset.label}</div>
                <div className="text-[11px] text-slate-500 mt-0.5">{preset.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">
              Sequencing QC Report URL (Sanger / NGS FastQ / FASTA)
            </label>
            <input
              type="url"
              value={qcReportUrl}
              onChange={(e) => setQcReportUrl(e.target.value)}
              placeholder="https://biofoundry.example.com/qc_runs/run_8921.fasta"
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-mono text-xs text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-purple-500/30 focus:border-purple-500"
            />
            <span className="text-[11px] text-slate-400 mt-1 block">
              GenLayer nodes will render and digest this URL live on-chain to evaluate sequence fidelity.
            </span>
          </div>

          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-medium">
              {error}
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-5 py-2.5 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shadow-md shadow-purple-600/20 transition-all active:scale-[0.98] disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Claiming & Submitting...</span>
                </>
              ) : (
                <>
                  <span>Claim Order & Submit Proof</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
