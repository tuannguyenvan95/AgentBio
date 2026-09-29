import React from 'react';
import { 
  Dna, 
  ExternalLink, 
  Microscope, 
  Cpu, 
  CheckCircle, 
  FileSearch, 
  AlertTriangle, 
  ShieldAlert, 
  ShieldCheck, 
  Clock, 
  Ban,
  Gavel 
} from 'lucide-react';
import { BioOrderData } from '../config/genlayer';
import { formatGen, getStatusMeta, truncateAddress } from '../utils/helpers';

interface BioOrderCardProps {
  order: BioOrderData;
  currentUser: string | null;
  onOpenSubmitProof: (order: BioOrderData) => void;
  onOpenInspector: (order: BioOrderData) => void;
  onOpenDispute: (order: BioOrderData) => void;
  onOpenAppellate: (order: BioOrderData) => void;
  onAdjudicate: (orderId: number) => Promise<void>;
  onFinalize: (orderId: number) => Promise<void>;
  onCancel: (orderId: number) => Promise<void>;
  isProcessing: boolean;
}

export const BioOrderCard: React.FC<BioOrderCardProps> = ({
  order,
  currentUser,
  onOpenSubmitProof,
  onOpenInspector,
  onOpenDispute,
  onOpenAppellate,
  onAdjudicate,
  onFinalize,
  onCancel,
  isProcessing,
}) => {
  const statusMeta = getStatusMeta(order.status);
  const isResearcher = currentUser && currentUser.toLowerCase() === order.researcher.toLowerCase();
  const isFoundry = currentUser && currentUser.toLowerCase() === order.foundry.toLowerCase();

  return (
    <div className={`bg-white rounded-2xl border ${statusMeta.borderColor} shadow-sm hover:shadow-md transition-all p-5 sm:p-6 flex flex-col justify-between`}>
      
      {/* Top Bar: Order ID, Status Badge, Escrow Amount */}
      <div>
        <div className="flex items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 border border-slate-200">
              #{order.order_id}
            </span>
            <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold border ${statusMeta.badgeBg}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${statusMeta.ledColor}`} />
              <span>{statusMeta.label}</span>
            </div>
          </div>

          <div className="text-right">
            <span className="font-display font-black text-lg text-slate-900 font-mono tracking-tight">
              {formatGen(order.escrow_amount)}
            </span>
            <span className="text-xs font-bold text-emerald-600 ml-1">GEN</span>
          </div>
        </div>

        {/* Biological Target Function */}
        <div className="mt-4">
          <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">
            <Dna className="w-3.5 h-3.5 text-emerald-600" />
            <span>Target Biological Function</span>
          </div>
          <p className="text-xs font-medium text-slate-800 line-clamp-3 leading-relaxed">
            {order.target_protein_function}
          </p>
        </div>

        {/* Adjudication Verdict & Fidelity Badge (if evaluated) */}
        {order.status >= 2 && (
          <div className="mt-4 p-3 rounded-xl bg-slate-50 border border-slate-200">
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Consensus Verdict
              </span>
              <div className="flex items-center gap-1 font-bold">
                {order.verdict === 'BIO_SYNTHESIS_VERIFIED' ? (
                  <span className="text-emerald-700 flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5" /> VERIFIED
                  </span>
                ) : order.verdict === 'BIOHAZARD_BLOCKED' ? (
                  <span className="text-orange-700 flex items-center gap-1">
                    <ShieldAlert className="w-3.5 h-3.5" /> BIOHAZARD
                  </span>
                ) : (
                  <span className="text-amber-700 flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5" /> DEFECTIVE
                  </span>
                )}
              </div>
            </div>

            {/* Fidelity Mini Bar */}
            <div className="flex items-center justify-between text-[11px] text-slate-600 font-medium">
              <span>Sequence Fidelity:</span>
              <span className={`font-mono font-bold ${order.fidelity_score >= 80 ? 'text-emerald-600' : 'text-amber-600'}`}>
                {order.fidelity_score}%
              </span>
            </div>
          </div>
        )}

        {/* Address Metadata */}
        <div className="mt-4 pt-3 border-t border-slate-100 grid grid-cols-2 gap-2 text-[11px]">
          <div>
            <span className="text-slate-400 text-[10px] uppercase font-bold block">Researcher</span>
            <span className="font-mono text-slate-700 truncate block" title={order.researcher}>
              {truncateAddress(order.researcher)}
            </span>
          </div>
          <div>
            <span className="text-slate-400 text-[10px] uppercase font-bold block">DNA Foundry</span>
            <span className="font-mono text-slate-700 truncate block" title={order.foundry}>
              {truncateAddress(order.foundry)}
            </span>
          </div>
        </div>
      </div>

      {/* Bottom Action Chamber */}
      <div className="mt-5 pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2">
        
        {/* Left: View Dossier */}
        <button
          onClick={() => onOpenInspector(order)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-all"
        >
          <FileSearch className="w-3.5 h-3.5 text-teal-600" />
          <span>Dossier</span>
        </button>

        {/* Right: State Contextual Actions */}
        <div className="flex items-center gap-2">
          
          {/* Status 0: Open -> Foundry claims */}
          {order.status === 0 && (
            <>
              {isResearcher ? (
                <button
                  onClick={() => onCancel(order.order_id)}
                  disabled={isProcessing}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-semibold text-rose-600 hover:bg-rose-50 disabled:opacity-50"
                >
                  <Ban className="w-3.5 h-3.5" />
                  <span>Cancel</span>
                </button>
              ) : (
                <button
                  onClick={() => onOpenSubmitProof(order)}
                  disabled={isProcessing}
                  className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shadow-sm shadow-purple-600/20 active:scale-[0.98] disabled:opacity-50"
                >
                  <Microscope className="w-3.5 h-3.5" />
                  <span>Claim & Submit QC</span>
                </button>
              )}
            </>
          )}

          {/* Status 1: In Synthesis -> Convene AI Biosecurity Jury */}
          {order.status === 1 && (
            <button
              onClick={() => onAdjudicate(order.order_id)}
              disabled={isProcessing}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-sm shadow-teal-600/20 active:scale-[0.98] disabled:opacity-50"
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>Convene AI Jury</span>
            </button>
          )}

          {/* Status 2: Awaiting Payout (Cooling-off) */}
          {order.status === 2 && (
            <>
              <button
                onClick={() => onOpenDispute(order)}
                disabled={isProcessing}
                className="flex items-center gap-1 px-3 py-1.5 rounded-xl border border-rose-200 bg-rose-50/50 text-rose-700 hover:bg-rose-100 text-xs font-semibold"
                title="Contest verdict during cooling-off window (10% bond)"
              >
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Appeal (10%)</span>
              </button>

              <button
                onClick={() => onFinalize(order.order_id)}
                disabled={isProcessing}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-sm active:scale-[0.98] disabled:opacity-50"
              >
                <CheckCircle className="w-3.5 h-3.5" />
                <span>Finalize Payout</span>
              </button>
            </>
          )}

          {/* Status 3: Settled Paid */}
          {order.status === 3 && (
            <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200 flex items-center gap-1">
              <CheckCircle className="w-3 h-3" /> Disbursed to Foundry
            </span>
          )}

          {/* Status 4: Biohazard Slashed */}
          {order.status === 4 && (
            <span className="text-[11px] font-bold text-orange-700 bg-orange-50 px-2.5 py-1 rounded-lg border border-orange-200 flex items-center gap-1">
              <ShieldAlert className="w-3 h-3" /> Slashed to Reserve
            </span>
          )}

          {/* Status 5: Defective Refunded */}
          {order.status === 5 && (
            <span className="text-[11px] font-bold text-amber-700 bg-amber-50 px-2.5 py-1 rounded-lg border border-amber-200">
              Refunded to Researcher
            </span>
          )}

          {/* Status 7: Disputed Appeal */}
          {order.status === 7 && (
            <button
              onClick={() => onOpenAppellate(order)}
              disabled={isProcessing}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-sm active:scale-95 disabled:opacity-50"
            >
              <Gavel className="w-3.5 h-3.5" />
              <span>Appellate Jury</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
