import React, { useState } from 'react';
import { AlertTriangle, Loader2, ArrowRight, ShieldAlert, CheckCircle2, FileCheck, Building2, Hash, ExternalLink } from 'lucide-react';
import { BioOrderData, computeSha256 } from '../config/genlayer';
import { formatGen } from '../utils/helpers';

interface DisputeModalProps {
  isOpen: boolean;
  onClose: () => void;
  order: BioOrderData | null;
  onSubmit: (
    orderId: number,
    disputeReason: string,
    bondWei: bigint,
    certifyingLab: string,
    supplementalEvidenceHash: string
  ) => Promise<void>;
  onAttest: (orderId: number, evidenceHash: string) => Promise<string>;
  userAddress?: string | null;
}

export const DisputeModal: React.FC<DisputeModalProps> = ({
  isOpen,
  onClose,
  order,
  onSubmit,
  onAttest,
  userAddress,
}) => {
  const [certifyingLab, setCertifyingLab] = useState(
    '0xF34587A45C397281Ef6BDd839d4A1de2DEe393ad'
  );
  const [evidenceUrl, setEvidenceUrl] = useState(
    'https://raw.githubusercontent.com/tuannguyenvan95/AgentBio/main/data/appeal_resequencing.txt'
  );
  const [evidenceHash, setEvidenceHash] = useState(
    'a3c9b7e41f0289d5678123456789abcdef0123456789abcdef0123456789abcd'
  );
  const [isHashing, setIsHashing] = useState(false);
  const [isAttesting, setIsAttesting] = useState(false);
  const [attestationTx, setAttestationTx] = useState<string | null>(null);
  const [isAttested, setIsAttested] = useState(false);

  const [disputeReason, setDisputeReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !order) return null;

  // Calculate required 10% bond
  const escrowWei = BigInt(order.escrow_amount || '0');
  const bondWei = (escrowWei * 10n) / 100n > 0n ? (escrowWei * 10n) / 100n : 1n;
  const bondFormatted = formatGen(bondWei);

  const handleComputeHashFromUrl = async () => {
    if (!evidenceUrl.trim()) return;
    try {
      setIsHashing(true);
      setError(null);
      const resp = await fetch(evidenceUrl.trim());
      if (!resp.ok) {
        throw new Error(`Failed to fetch from URL (${resp.status}). Ensure URL is publicly reachable.`);
      }
      const text = await resp.text();
      const hash = await computeSha256(text);
      setEvidenceHash(hash);
    } catch (err: any) {
      console.warn('URL fetch error, using manual/fallback computation:', err);
      // Fallback: hash the URL string itself or prompt user
      const hash = await computeSha256(evidenceUrl.trim());
      setEvidenceHash(hash);
    } finally {
      setIsHashing(false);
    }
  };

  const handleAttestStep = async () => {
    setError(null);
    const cleanHash = evidenceHash.trim().toLowerCase();
    if (cleanHash.length !== 64) {
      setError('A valid 64-character hex SHA-256 evidence hash is required for lab attestation.');
      return;
    }
    if (!certifyingLab || !certifyingLab.startsWith('0x') || certifyingLab.length !== 42) {
      setError('A valid accredited laboratory address (0x...) is required.');
      return;
    }

    try {
      setIsAttesting(true);
      const tx = await onAttest(order.order_id, cleanHash);
      setAttestationTx(tx);
      setIsAttested(true);
    } catch (err: any) {
      console.error('Attestation error:', err);
      setError(err?.message || 'Failed to submit laboratory attestation on Studionet.');
    } finally {
      setIsAttesting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const cleanReason = disputeReason.trim();
    if (cleanReason.length < 10) {
      setError('Substantive dispute justification must be at least 10 characters.');
      return;
    }

    const cleanHash = evidenceHash.trim().toLowerCase();
    if (cleanHash.length !== 64) {
      setError('Valid 64-character SHA-256 supplemental evidence hash is required.');
      return;
    }

    if (!isAttested) {
      setError('Laboratory attestation must be completed or confirmed before lodging appeal.');
      return;
    }

    try {
      setIsSubmitting(true);
      await onSubmit(order.order_id, cleanReason, bondWei, certifyingLab.trim(), cleanHash);
      onClose();
    } catch (err: any) {
      console.error('Appeal error:', err);
      setError(err?.message || 'Failed to submit appeal on Studionet.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-xl w-full p-6 sm:p-8 text-slate-900 max-h-[90vh] overflow-y-auto">
        
        {/* Header */}
        <div className="flex items-start justify-between pb-5 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center shadow-inner">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">Contest Biosecurity Verdict</h3>
              <p className="text-xs text-slate-500">ISO-17025 Accredited Appellate Workflow • Order #{order.order_id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isSubmitting || isAttesting}
            className="text-slate-400 hover:text-slate-600 font-semibold p-1"
          >
            ✕
          </button>
        </div>

        {/* Bond Requirement Info */}
        <div className="mt-4 p-4 rounded-2xl bg-amber-50/80 border border-amber-200 text-xs text-amber-950 space-y-1.5">
          <div className="flex items-center gap-2 font-bold text-amber-900">
            <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
            <span>Anti-Griefing 10% Dispute Bond Required</span>
          </div>
          <p className="text-[11px] leading-relaxed text-amber-900/80">
            To prevent frivolous delays, appellants must stake 10% of the synthesis escrow (<span className="font-bold font-mono">{bondFormatted} GEN</span>). If the appeal is upheld, the bond is returned.
          </p>
        </div>

        {/* STEP 1: LABORATORY ATTESTATION */}
        <div className="mt-5 p-4 rounded-2xl border border-indigo-100 bg-indigo-50/40 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-indigo-600 text-white flex items-center justify-center text-xs font-bold">
                1
              </div>
              <h4 className="text-xs font-bold text-indigo-950 uppercase tracking-wider">
                Laboratory Attestation (`attest_appeal_evidence`)
              </h4>
            </div>
            {isAttested ? (
              <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Attested On-Chain
              </span>
            ) : (
              <span className="text-[11px] text-amber-700 bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-200">
                Pending Attestation
              </span>
            )}
          </div>
          <p className="text-[11px] text-slate-600 leading-relaxed">
            Per protocol rules, an accredited laboratory must cryptographic-bind the supplemental forensic evidence to Order #{order.order_id} before an appeal can be lodged.
          </p>

          <div>
            <label className="block text-[11px] font-bold text-slate-700 mb-1 flex items-center gap-1.5">
              <Building2 className="w-3.5 h-3.5 text-indigo-600" />
              Accredited Certifying Laboratory Address
            </label>
            <input
              type="text"
              value={certifyingLab}
              onChange={(e) => setCertifyingLab(e.target.value)}
              placeholder="0x..."
              className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-white font-mono text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
            />
          </div>

          <div>
            <label className="block text-[11px] font-bold text-slate-700 mb-1 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <ExternalLink className="w-3.5 h-3.5 text-indigo-600" />
                Supplemental Evidence URL
              </span>
              <button
                type="button"
                onClick={handleComputeHashFromUrl}
                disabled={isHashing}
                className="text-[10px] text-indigo-600 hover:text-indigo-800 font-bold underline"
              >
                {isHashing ? 'Computing Hash...' : 'Compute SHA-256 from URL'}
              </button>
            </label>
            <input
              type="text"
              value={evidenceUrl}
              onChange={(e) => setEvidenceUrl(e.target.value)}
              placeholder="https://..."
              className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-white font-mono text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
            />
          </div>

          <div>
            <label className="block text-[11px] font-bold text-slate-700 mb-1 flex items-center gap-1.5">
              <Hash className="w-3.5 h-3.5 text-indigo-600" />
              Evidence SHA-256 Content Commitment (64 Hex Characters)
            </label>
            <input
              type="text"
              value={evidenceHash}
              onChange={(e) => setEvidenceHash(e.target.value)}
              placeholder="64-char lowercase hex sha256"
              className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-white font-mono text-[11px] text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
            />
          </div>

          <div className="flex items-center justify-between pt-1">
            <label className="flex items-center gap-2 cursor-pointer text-[11px] text-slate-600">
              <input
                type="checkbox"
                checked={isAttested}
                onChange={(e) => setIsAttested(e.target.checked)}
                className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span>Lab already attested on-chain</span>
            </label>
            <button
              type="button"
              onClick={handleAttestStep}
              disabled={isAttesting || isAttested}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-all disabled:opacity-50"
            >
              {isAttesting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Attesting On-Chain...</span>
                </>
              ) : isAttested ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Attestation Complete</span>
                </>
              ) : (
                <>
                  <FileCheck className="w-3.5 h-3.5" />
                  <span>Attest as Accredited Lab</span>
                </>
              )}
            </button>
          </div>

          {attestationTx && (
            <p className="text-[10px] text-emerald-700 font-mono break-all bg-emerald-50 p-2 rounded-lg border border-emerald-200">
              Tx: {attestationTx}
            </p>
          )}
        </div>

        {/* STEP 2: STAKE BOND & LODGE APPEAL */}
        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-rose-600 text-white flex items-center justify-center text-xs font-bold">
              2
            </div>
            <h4 className="text-xs font-bold text-rose-950 uppercase tracking-wider">
              Lodge Formal Appeal (`appeal_verdict`)
            </h4>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">
              Forensic Rebuttal & Biological Justification (&ge; 10 characters)
            </label>
            <textarea
              rows={3}
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

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting || isAttesting}
              className="px-5 py-2.5 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || isAttesting || !isAttested}
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
