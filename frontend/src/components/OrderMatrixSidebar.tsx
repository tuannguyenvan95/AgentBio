import React from 'react';
import { 
  Plus, 
  Search, 
  Dna, 
  ShieldCheck, 
  ShieldAlert, 
  AlertTriangle, 
  Activity, 
  Clock, 
  CheckCircle2,
  ChevronRight,
  Filter
} from 'lucide-react';
import { BioOrderData } from '../config/genlayer';
import { formatGen, getStatusMeta, truncateAddress } from '../utils/helpers';

interface OrderMatrixSidebarProps {
  orders: BioOrderData[];
  selectedOrderId: number | null;
  onSelectOrder: (order: BioOrderData) => void;
  onOpenCommission: () => void;
  selectedFilter: string;
  onFilterChange: (filter: string) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

export const OrderMatrixSidebar: React.FC<OrderMatrixSidebarProps> = ({
  orders,
  selectedOrderId,
  onSelectOrder,
  onOpenCommission,
  selectedFilter,
  onFilterChange,
  searchQuery,
  onSearchChange,
}) => {
  const filterTabs = [
    { id: 'all', label: 'All' },
    { id: 'open', label: 'Open' },
    { id: 'synthesis', label: 'In QC' },
    { id: 'cooling', label: 'Cooling' },
    { id: 'verified', label: 'Verified' },
    { id: 'blocked', label: 'Blocked' },
    { id: 'defective', label: 'Defect' },
  ];

  return (
    <div className="bg-white rounded-3xl border border-slate-200 shadow-sm flex flex-col h-[calc(100vh-10rem)] max-h-[860px] overflow-hidden">
      
      {/* Top Header & Commission Button */}
      <div className="p-4 border-b border-slate-100 bg-slate-50/50 space-y-3 shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-200">
              <Dna className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-display font-extrabold text-xs uppercase tracking-wider text-slate-900">
                Synthesis Pipeline
              </h3>
              <span className="text-[10px] text-slate-400 font-mono">
                {orders.length} active escrows
              </span>
            </div>
          </div>

          <button
            onClick={onOpenCommission}
            className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-sm shadow-emerald-600/20 active:scale-95 transition-all"
            title="Commission New DNA Synthesis"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Order</span>
          </button>
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search protein, ID, address..."
            className="w-full pl-8 pr-3 py-1.5 rounded-xl border border-slate-200 bg-white text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 text-[11px] font-semibold no-scrollbar">
          {filterTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => onFilterChange(tab.id)}
              className={`px-2.5 py-1 rounded-lg whitespace-nowrap transition-all ${
                selectedFilter === tab.id
                  ? 'bg-slate-900 text-white shadow-xs font-bold'
                  : 'text-slate-500 hover:text-slate-900 hover:bg-slate-200/60'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Orders List Chamber */}
      <div className="flex-1 overflow-y-auto divide-y divide-slate-100 p-2 space-y-1">
        {orders.length === 0 ? (
          <div className="p-8 text-center text-slate-400">
            <Dna className="w-8 h-8 mx-auto mb-2 opacity-30" />
            <p className="text-xs font-medium">No synthesis orders match filter</p>
          </div>
        ) : (
          orders.map((order) => {
            const statusMeta = getStatusMeta(order.status);
            const isSelected = selectedOrderId === order.order_id;

            return (
              <div
                key={order.order_id}
                onClick={() => onSelectOrder(order)}
                className={`p-3 rounded-2xl cursor-pointer transition-all border ${
                  isSelected
                    ? 'bg-emerald-50/70 border-emerald-500 shadow-sm ring-1 ring-emerald-500/20'
                    : 'bg-white border-transparent hover:border-slate-200 hover:bg-slate-50/60'
                }`}
              >
                {/* Top Row: ID, Status, Escrow Amount */}
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono text-[11px] font-bold px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                      #{order.order_id}
                    </span>
                    <span className={`w-2 h-2 rounded-full ${statusMeta.ledColor}`} />
                    <span className="text-[10px] uppercase font-bold text-slate-500 truncate max-w-[90px]">
                      {statusMeta.code}
                    </span>
                  </div>

                  <span className="font-mono text-xs font-black text-slate-900">
                    {formatGen(order.escrow_amount)} <span className="text-emerald-700 font-bold text-[10px]">GEN</span>
                  </span>
                </div>

                {/* Target Function Preview */}
                <p className="text-xs text-slate-700 font-medium line-clamp-2 leading-relaxed">
                  {order.target_protein_function}
                </p>

                {/* Bottom Row: Fidelity Gauge & Parties */}
                <div className="mt-2.5 pt-2 border-t border-slate-100/80 flex items-center justify-between text-[10px] text-slate-500">
                  <div className="flex items-center gap-1">
                    {order.status >= 2 ? (
                      <span className={`font-mono font-bold ${
                        order.fidelity_score >= 80 ? 'text-emerald-700' : 'text-amber-700'
                      }`}>
                        Fidelity: {order.fidelity_score}%
                      </span>
                    ) : (
                      <span className="text-slate-400 italic">Awaiting QC</span>
                    )}
                  </div>

                  <div className="flex items-center gap-1 font-mono text-slate-400">
                    <span>{truncateAddress(order.researcher)}</span>
                    <ChevronRight className={`w-3 h-3 ${isSelected ? 'text-emerald-600' : 'text-slate-300'}`} />
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
