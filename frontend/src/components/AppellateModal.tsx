import React, { useState } from 'react';
import { Gavel, Loader2, Sparkles, ArrowRight, ShieldCheck } from 'lucide-react';
import { BioOrderData } from '../config/genlayer';
import { formatGen } from '../utils/helpers';

interface AppellateModalProps {
  isOpen: boolean;
  onClose: () => void;
  order: BioOrderData | null;
  onSubmit: (orderId: number, supplementalQcUrl: string) => Promise<void>;
}

export const AppellateModal: React.FC<AppellateModalProps> = ({
  isOpen,
  onClose,
  order,
  onSubmit,
}) => {
  const [supplementalUrl, setSupplementalUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !order) return null;

  const presets = [
    {
      title: 'PacBio HiFi Re-Sequencing Alignment (99.8% Purity)',
      url: 'https://raw.githubusercontent.com/biopython/biopython/master/Tests/GenBank/cor6_6.gb',
      desc: 'Independent long-read PacBio HiFi sequencing confirming unbroken therapeutic coding sequence.',
    },
    {
      title: 'Oxford Nanopore Ultra-Long Read Verification',
      url: 'https://raw.githubusercontent.com/biopython/biopython/master/Tests/SwissProt/sp001.dat',
      desc: 'Resolves homopolymer repeat artifacts and verifies correct codon translation without frame-shifts.',
    }
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const cleanUrl = supplementalUrl.trim();
    if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
      setError('Valid public supplemental QC evidence URL (http/https) is required.');
      return;
    }

    try {
      setIsSubmitting(true);
      await onSubmit(order.order_id, cleanUrl);
      onClose();
    } catch (err: any) {
      console.error('Appellate review error:', err);
      setError(err?.message || 'Appellate review failed on Studionet.');
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
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center shadow-inner">
              <Gavel className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">Supreme Appellate Bio-Jury</h3>
              <p className="text-xs text-slate-500">Convene Final Binding Settlement • Order #{order.order_id}</p>
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

        {/* Dispute Summary */}
        <div className="mt-5 p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs space-y-2">
          <div className="flex justify-between">
            <span className="text-slate-500">Contested Escrow:</span>
            <span className="font-mono font-bold text-slate-900">{formatGen(order.escrow_amount)} GEN</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Staked Dispute Bond:</span>
            <span className="font-mono font-bold text-rose-600">{formatGen(order.dispute_bond)} GEN</span>
          </div>
          <div className="pt-2 border-t border-slate-200/80">
            <span className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Contestation Claim:</span>
            <p className="text-[11px] text-slate-700 italic line-clamp-3">"{order.reason}"</p>
          </div>
        </div>

        {/* Preset Evidence */}
        <div className="mt-4">
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            <span>Supplemental Evidence Vectors</span>
          </label>
          <div className="space-y-2">
            {presets.map((p, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setSupplementalUrl(p.url)}
                className="w-full text-left p-3 rounded-xl border border-slate-200 bg-slate-50/70 hover:bg-indigo-50/50 hover:border-indigo-300 transition-all text-xs"
              >
                <div className="font-bold text-slate-800">{p.title}</div>
                <div className="text-[11px] text-slate-500 mt-0.5">{p.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">
              Supplemental Evidence / Re-Sequencing URL
            </label>
            <input
              type="url"
              value={supplementalUrl}
              onChange={(e) => setSupplementalUrl(e.target.value)}
              placeholder="https://pacbio.evidence.org/hi-fi-run-44.fasta"
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-mono text-xs text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500"
            />
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
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition-all active:scale-95 disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Adjudicating Appeal...</span>
                </>
              ) : (
                <>
                  <span>Adjudicate & Settle Appeal</span>
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
