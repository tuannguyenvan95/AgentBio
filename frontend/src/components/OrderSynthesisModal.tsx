import React, { useState } from 'react';
import { Dna, ShieldAlert, Sparkles, Loader2, ArrowRight } from 'lucide-react';
import { parseGenToWei, PRESET_SYNTHESIS_ORDERS } from '../utils/helpers';

interface OrderSynthesisModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (targetFn: string, specUrl: string, durationBlocks: number, depositWei: bigint) => Promise<void>;
  userBalance: string;
}

export const OrderSynthesisModal: React.FC<OrderSynthesisModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  userBalance,
}) => {
  const [targetFunction, setTargetFunction] = useState('');
  const [specUrl, setSpecUrl] = useState('');
  const [depositGen, setDepositGen] = useState('2.5');
  const [durationBlocks, setDurationBlocks] = useState(5000);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleApplyPreset = (idx: number) => {
    const preset = PRESET_SYNTHESIS_ORDERS[idx];
    if (preset) {
      setTargetFunction(preset.targetFunction);
      setSpecUrl(preset.specUrl);
      setDepositGen(preset.depositGen);
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const cleanFn = targetFunction.trim();
    if (cleanFn.length < 10) {
      setError('Target biological function must be at least 10 characters.');
      return;
    }

    const cleanUrl = specUrl.trim();
    if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
      setError('Valid public FASTA / GenBank specification URL (http/https) is required.');
      return;
    }

    const depositWei = parseGenToWei(depositGen);
    if (depositWei <= 0n) {
      setError('Escrow deposit must be greater than 0 GEN.');
      return;
    }

    try {
      setIsSubmitting(true);
      await onSubmit(cleanFn, cleanUrl, durationBlocks, depositWei);
      onClose();
    } catch (err: any) {
      console.error('Order synthesis error:', err);
      setError(err?.message || 'Transaction failed on GenLayer Studionet.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fadeIn overflow-y-auto">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-xl w-full p-6 sm:p-8 my-8 text-slate-900">
        
        {/* Header */}
        <div className="flex items-start justify-between pb-5 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center shadow-inner">
              <Dna className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">Commission DNA Synthesis</h3>
              <p className="text-xs text-slate-500">Lock GEN escrow with on-chain biosecurity screening</p>
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

        {/* Quick Presets */}
        <div className="mt-5">
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
            <span>Standard DeSci Benchmarks (Quick Fill)</span>
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            {PRESET_SYNTHESIS_ORDERS.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleApplyPreset(idx)}
                className="text-left p-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-emerald-50/50 hover:border-emerald-300 transition-all text-xs"
              >
                <span className="font-bold text-slate-800 line-clamp-1">{preset.title}</span>
                <span className="text-[10px] text-emerald-700 font-semibold mt-0.5 block">
                  {preset.depositGen} GEN • {preset.category}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">
              Target Protein / Enzyme Function & Biological Application
            </label>
            <textarea
              rows={3}
              value={targetFunction}
              onChange={(e) => setTargetFunction(e.target.value)}
              placeholder="e.g. Engineered alpha-amylase enzyme for high-temperature starch hydrolysis with enhanced calcium stability..."
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-xs text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500"
            />
            <span className="text-[11px] text-slate-400 mt-1 block">
              Used by GenLayer AI Biosecurity Jury to verify intended biological application.
            </span>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">
              FASTA / GenBank Sequence Specification URL
            </label>
            <input
              type="url"
              value={specUrl}
              onChange={(e) => setSpecUrl(e.target.value)}
              placeholder="https://raw.githubusercontent.com/.../target_sequence.fasta"
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-mono text-xs text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Escrow Deposit (GEN)
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={depositGen}
                  onChange={(e) => setDepositGen(e.target.value)}
                  placeholder="2.5"
                  className="w-full pl-3.5 pr-14 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-bold text-xs text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500"
                />
                <span className="absolute right-3 top-2.5 text-xs font-bold text-slate-400">
                  GEN
                </span>
              </div>
              <span className="text-[10px] text-slate-400 mt-1 block font-mono">
                Balance: {userBalance} GEN
              </span>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Synthesis Duration (Blocks)
              </label>
              <input
                type="number"
                value={durationBlocks}
                onChange={(e) => setDurationBlocks(Number(e.target.value))}
                min={100}
                max={50000}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-xs font-semibold text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500"
              />
              <span className="text-[10px] text-slate-400 mt-1 block">
                Approx. {Math.round(durationBlocks / 20)} minutes timelock
              </span>
            </div>
          </div>

          {/* Biosecurity Warning Notice */}
          <div className="p-3.5 rounded-2xl bg-amber-50/70 border border-amber-200/80 text-xs text-amber-900 flex items-start gap-2.5">
            <ShieldAlert className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
            <div className="text-[11px] leading-relaxed">
              <strong className="font-bold">Automated Biosecurity Screening:</strong> If the synthesized sequence is verified safe with ≥80% fidelity, 100% of escrow releases to the foundry. If defective, you receive a full refund. <span className="font-semibold text-orange-700">Notice: Submitting prohibited dual-use pathogens or weaponized toxins results in immediate escrow slashing to the Biosecurity Reserve.</span>
            </div>
          </div>

          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-medium">
              {error}
            </div>
          )}

          {/* Action Buttons */}
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
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20 transition-all active:scale-[0.98] disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Locking Escrow on Studionet...</span>
                </>
              ) : (
                <>
                  <span>Lock Escrow & Submit</span>
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
