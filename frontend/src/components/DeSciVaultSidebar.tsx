import React from 'react';
import { 
  Lock, 
  ShieldAlert, 
  CheckCircle2, 
  Sparkles, 
  Cpu, 
  Activity, 
  ExternalLink,
  Layers,
  ArrowRight,
  Database
} from 'lucide-react';
import { ProtocolStats, BioOrderData, STUDIO_URL } from '../config/genlayer';
import { formatGen, truncateAddress } from '../utils/helpers';

interface DeSciVaultSidebarProps {
  stats: ProtocolStats;
  orders: BioOrderData[];
  onOpenStudio: () => void;
  onOpenCommission: () => void;
}

export const DeSciVaultSidebar: React.FC<DeSciVaultSidebarProps> = ({
  stats,
  orders,
  onOpenStudio,
  onOpenCommission,
}) => {
  const verifiedCount = orders.filter((o) => o.status === 3).length;
  const blockedCount = orders.filter((o) => o.status === 4).length;
  const inReviewCount = orders.filter((o) => o.status === 1 || o.status === 2).length;

  return (
    <div className="bg-white rounded-3xl border border-slate-200 shadow-sm flex flex-col h-[calc(100vh-10rem)] max-h-[860px] overflow-hidden">
      
      {/* Vault Header */}
      <div className="p-4 border-b border-slate-100 bg-slate-50/50 shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-teal-50 text-teal-600 border border-teal-200">
              <Database className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-display font-extrabold text-xs uppercase tracking-wider text-slate-900">
                DeSci Protocol Vault
              </h3>
              <span className="text-[10px] text-slate-400 font-mono">
                GenLayer Studionet #61999
              </span>
            </div>
          </div>

          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
        </div>
      </div>

      {/* Main Vault Content (Scrollable) */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        
        {/* Metric 1: Total Bio Escrow Locked */}
        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between text-[10px] uppercase font-bold text-slate-400">
            <span>Escrow Locked</span>
            <Lock className="w-3.5 h-3.5 text-emerald-600" />
          </div>
          <div className="mt-2 flex items-baseline gap-1.5">
            <span className="font-display font-black text-2xl text-slate-900 font-mono tracking-tight">
              {formatGen(stats.total_bio_locked)}
            </span>
            <span className="text-xs font-bold text-emerald-600">GEN</span>
          </div>
          <p className="text-[10px] text-slate-400 mt-0.5">
            Locked in GenVM smart contracts
          </p>
        </div>

        {/* Metric 2: Slashed Pathogen Fines */}
        <div className="p-4 rounded-2xl bg-orange-50/50 border border-orange-200/80">
          <div className="flex items-center justify-between text-[10px] uppercase font-bold text-orange-700">
            <span>Biosecurity Reserve</span>
            <ShieldAlert className="w-3.5 h-3.5 text-orange-600" />
          </div>
          <div className="mt-2 flex items-baseline gap-1.5">
            <span className="font-display font-black text-2xl text-orange-700 font-mono tracking-tight">
              {blockedCount}
            </span>
            <span className="text-xs font-bold text-orange-700">Slashed</span>
          </div>
          <p className="text-[10px] text-orange-900/70 mt-0.5">
            Confiscated from dangerous pathogen orders
          </p>
        </div>

        {/* Metric 3: Synthesis Settlement Ticker */}
        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
          <div className="flex items-center justify-between text-[10px] uppercase font-bold text-slate-400">
            <span>Verified Disbursed</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" />
          </div>
          <div className="mt-2 flex items-baseline gap-1.5">
            <span className="font-display font-black text-2xl text-slate-900 font-mono tracking-tight">
              {verifiedCount}
            </span>
            <span className="text-xs text-slate-400">/ {orders.length} orders</span>
          </div>
          <p className="text-[10px] text-slate-400 mt-0.5">
            Passed ≥80% sequence fidelity
          </p>
        </div>

        {/* Interactive Simulation Studio Card */}
        <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 text-white space-y-3 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-teal-400 flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5" />
              <span>QC Consensus Simulator</span>
            </span>
            <span className="text-[9px] font-mono bg-slate-800 px-1.5 py-0.5 rounded text-slate-300">
              Interactive
            </span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed font-sans">
            Test how GenLayer subjective AI juries review FASTA files, flag bioweapon toxins, and enforce Canary tokens.
          </p>
          <button
            onClick={onOpenStudio}
            className="w-full flex items-center justify-center gap-1.5 py-2 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 text-xs font-bold transition-all active:scale-95 shadow-sm"
          >
            <span>Launch Simulation Studio</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Network & Consensus Health */}
        <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-xs space-y-2">
          <div className="text-[10px] uppercase font-bold text-slate-400">
            Studionet Telemetry
          </div>
          <div className="space-y-1.5 text-[11px]">
            <div className="flex justify-between">
              <span className="text-slate-500">Chain ID:</span>
              <span className="font-mono text-slate-800 font-bold">61999 (0xF1EF)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Consensus Engine:</span>
              <span className="font-semibold text-emerald-700">Subjective Non-Det LLM</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Active In Review:</span>
              <span className="font-mono text-purple-700 font-bold">{inReviewCount} orders</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Link to Studio */}
      <div className="p-3 border-t border-slate-100 bg-slate-50 shrink-0 text-center">
        <a
          href={STUDIO_URL}
          target="_blank"
          rel="noreferrer"
          className="text-xs text-slate-500 hover:text-emerald-700 font-semibold inline-flex items-center gap-1"
        >
          <span>Open GenLayer Studio Console</span>
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </div>
  );
};
