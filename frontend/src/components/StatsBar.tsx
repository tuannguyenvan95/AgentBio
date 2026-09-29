import React from 'react';
import { Lock, CheckCircle2, ShieldAlert, Cpu, Activity } from 'lucide-react';
import { formatGen } from '../utils/helpers';
import { ProtocolStats, BioOrderData } from '../config/genlayer';

interface StatsBarProps {
  stats: ProtocolStats;
  orders: BioOrderData[];
}

export const StatsBar: React.FC<StatsBarProps> = ({ stats, orders }) => {
  const activeOrders = orders.filter((o) => o.status === 0 || o.status === 1 || o.status === 2).length;
  const verifiedCount = orders.filter((o) => o.status === 3).length;
  const blockedCount = orders.filter((o) => o.status === 4).length;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {/* 1. Total Escrow Locked */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm hover:border-slate-300 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Total Bio Escrow Locked
          </span>
          <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <Lock className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="font-display text-2xl font-black text-slate-900 tracking-tight">
            {formatGen(stats.total_bio_locked)}
          </span>
          <span className="text-xs font-bold text-emerald-600">GEN</span>
        </div>
        <p className="mt-1 text-xs text-slate-400">
          Secured in GenVM intelligent escrow
        </p>
      </div>

      {/* 2. Syntheses Settled */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm hover:border-slate-300 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Verified Syntheses
          </span>
          <div className="w-8 h-8 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center">
            <CheckCircle2 className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="font-display text-2xl font-black text-slate-900 tracking-tight">
            {verifiedCount}
          </span>
          <span className="text-xs text-slate-400">
            / {stats.total_orders || orders.length} orders
          </span>
        </div>
        <p className="mt-1 text-xs text-slate-400">
          Passed ≥80% sequencing fidelity
        </p>
      </div>

      {/* 3. Biosecurity Shield Fines */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm hover:border-slate-300 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Pathogens Intercepted
          </span>
          <div className="w-8 h-8 rounded-lg bg-orange-50 text-orange-600 flex items-center justify-center">
            <ShieldAlert className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="font-display text-2xl font-black text-orange-600 tracking-tight">
            {blockedCount}
          </span>
          <span className="text-xs font-bold text-slate-500">Slashed</span>
        </div>
        <p className="mt-1 text-xs text-slate-400">
          Confiscated to DeSci Biosecurity Reserve
        </p>
      </div>

      {/* 4. Active Synthesis Pipeline */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm hover:border-slate-300 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Active Pipeline
          </span>
          <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
            <Activity className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="font-display text-2xl font-black text-slate-900 tracking-tight">
            {activeOrders}
          </span>
          <span className="text-xs font-semibold text-purple-600">in process</span>
        </div>
        <p className="mt-1 text-xs text-slate-400 flex items-center gap-1">
          <Cpu className="w-3 h-3 text-slate-400 inline" />
          Live LLM consensus validation
        </p>
      </div>
    </div>
  );
};
