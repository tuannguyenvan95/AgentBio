import React, { useState } from 'react';
import { AlertTriangle, Loader2, ArrowRight, ShieldAlert } from 'lucide-react';
import { BioOrderData } from '../config/genlayer';
import { formatGen } from '../utils/helpers';

interface DisputeModalProps {
  isOpen: boolean;
  onClose: () => void;
  order: BioOrderData | null;
  onSubmit: (orderId: number, disputeReason: string, bondWei: bigint) => Promise<void>;
}

export const DisputeModal: React.FC<DisputeModalProps> = ({
  isOpen,
  onClose,
  order,
  onSubmit,
}) => {
  const [disputeReason, setDisputeReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !order) return null;

  // Calculate required 10% bond
  const escrowWei = BigInt(order.escrow_amount || '0');
  const bondWei = (escrowWei * 10n) / 100n > 0n ? (escrowWei * 10n) / 100n : 1n;
  const bondFormatted = formatGen(bondWei);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const cleanReason = disputeReason.trim();
    if (cleanReason.length < 10) {
      setError('Substantive dispute justification must be at least 10 characters.');
      return;
    }

    try {
      setIsSubmitting(true);
      await onSubmit(order.order_id, cleanReason, bondWei);
      onClose();
    } catch (err: any) {
      console.error('Appeal error:', err);
      setError(err?.message || 'Failed to submit appeal on Studionet.');
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
            <div className="w-12 h-12 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center shadow-inner">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">Contest Biosecurity Verdict</h3>
              <p className="text-xs text-slate-500">Cooling-Off Window Appeal • Order #{order.order_id}</p>
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

        {/* Bond Requirement Info */}
        <div className="mt-5 p-4 rounded-2xl bg-amber-50/80 border border-amber-200 text-xs text-amber-950 space-y-1.5">
          <div className="flex items-center gap-2 font-bold text-amber-900">
            <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
            <span>Anti-Griefing 10% Dispute Bond Required</span>
          </div>
          <p className="text-[11px] leading-relaxed text-amber-900/80">
            To prevent frivolous delays, appellants must stake 10% of the synthesis escrow (<span className="font-bold font-mono">{bondFormatted} GEN</span>). If the appeal is upheld, the bond is returned.
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">
              Forensic Rebuttal & Biological Justification
            </label>
            <textarea
              rows={4}
              value={disputeReason}
              onChange={(e) => setDisputeReason(e.target.value)}
              placeholder="e.g. Independent re-sequencing via Oxford Nanopore shows the alleged frame-shift was an artifact of homopolymer slip; intact therapeutic ORF confirmed with 99.2% fidelity..."
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-xs text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-rose-500/30 focus:border-rose-500"
            />
          </div>

          <div className="flex justify-between items-center p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
            <span className="text-slate-500 font-medium">Dispute Bond Stake:</span>
            <span className="font-bold text-slate-900 font-mono">{bondFormatted} GEN</span>
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
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold shadow-md shadow-rose-600/20 transition-all active:scale-[0.98] disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Staking Bond & Submitting...</span>
                </>
              ) : (
                <>
                  <span>Stake Bond & File Appeal</span>
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
