import React, { useState, useEffect, useCallback } from 'react';
import { 
  Dna, 
  Plus, 
  Search, 
  Filter, 
  AlertCircle, 
  ShieldCheck, 
  ShieldAlert, 
  CheckCircle2, 
  HelpCircle, 
  ExternalLink,
  RefreshCw,
  Cpu,
  Layers,
  Sparkles,
  Microscope,
  LayoutGrid,
  Columns3
} from 'lucide-react';
import { Navbar } from './components/Navbar';
import { NucleotideRibbon } from './components/NucleotideRibbon';
import { StatsBar } from './components/StatsBar';
import { BioOrderCard } from './components/BioOrderCard';
import { OrderMatrixSidebar } from './components/OrderMatrixSidebar';
import { GenomicInspectionCockpit } from './components/GenomicInspectionCockpit';
import { DeSciVaultSidebar } from './components/DeSciVaultSidebar';
import { OrderSynthesisModal } from './components/OrderSynthesisModal';
import { SubmitProofModal } from './components/SubmitProofModal';
import { SequenceInspectorModal } from './components/SequenceInspectorModal';
import { DisputeModal } from './components/DisputeModal';
import { LiveQCStudioModal } from './components/LiveQCStudioModal';

import {
  STUDIO_URL,
  STUDIONET_CHAIN_ID,
  getSavedContractAddress,
  saveContractAddress,
  fetchStudionetBalance,
  fetchStats,
  fetchAllOrders,
  ensureStudionet,
  orderSynthesisOnChain,
  submitSynthesisProofOnChain,
  adjudicateBiosecurityOnChain,
  appealVerdictOnChain,
  finalizeSettlementOnChain,
  cancelOrReclaimOnChain,
  BioOrderData,
  ProtocolStats,
} from './config/genlayer';

export function App() {
  // Web3 State
  const [account, setAccount] = useState<string | null>(null);
  const [balance, setBalance] = useState<string>('0');
  const [isConnecting, setIsConnecting] = useState(false);
  const [contractAddress, setContractAddress] = useState<string>(getSavedContractAddress());

  // Protocol State
  const [stats, setStats] = useState<ProtocolStats>({
    total_orders: 0,
    total_bio_locked: '0',
    total_orders_settled: 0,
  });
  const [orders, setOrders] = useState<BioOrderData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);
  const [selectedOrder, setSelectedOrder] = useState<BioOrderData | null>(null);

  // Layout View Mode: 'cockpit' (Novel 3-Panel Biocomputing Console) vs 'grid' (Ledger Grid)
  const [layoutMode, setLayoutMode] = useState<'cockpit' | 'grid'>('cockpit');

  // Filters & Search
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Modals
  const [isOrderModalOpen, setIsOrderModalOpen] = useState(false);
  const [isProofModalOpen, setIsProofModalOpen] = useState(false);
  const [isInspectorModalOpen, setIsInspectorModalOpen] = useState(false);
  const [isDisputeModalOpen, setIsDisputeModalOpen] = useState(false);
  const [isStudioModalOpen, setIsStudioModalOpen] = useState(false);
  const [activeModalOrder, setActiveModalOrder] = useState<BioOrderData | null>(null);
  const [isProcessingAction, setIsProcessingAction] = useState(false);

  // Connect Wallet
  const connectWallet = async () => {
    if (typeof window === 'undefined' || !(window as any).ethereum) {
      setStatusMessage({
        type: 'error',
        text: 'MetaMask is not detected. Please install MetaMask to interact with AgentBio.',
      });
      return;
    }

    try {
      setIsConnecting(true);
      await ensureStudionet();
      const accounts = await (window as any).ethereum.request({
        method: 'eth_requestAccounts',
      });
      if (accounts && accounts.length > 0) {
        setAccount(accounts[0]);
        const bal = await fetchStudionetBalance(accounts[0]);
        setBalance(bal);
        setStatusMessage({
          type: 'success',
          text: `Connected to GenLayer Studionet (${accounts[0].slice(0, 6)}...${accounts[0].slice(-4)})`,
        });
      }
    } catch (err: any) {
      console.error('Wallet connection error:', err);
      setStatusMessage({
        type: 'error',
        text: err?.message || 'Failed to connect MetaMask.',
      });
    } finally {
      setIsConnecting(false);
    }
  };

  // Load Contract State
  const loadData = useCallback(async () => {
    if (!contractAddress) return;
    try {
      setIsRefreshing(true);
      const [statsData, ordersData] = await Promise.all([
        fetchStats(contractAddress),
        fetchAllOrders(contractAddress),
      ]);
      setStats(statsData);
      setOrders(ordersData);

      // Maintain or initialize selected order for cockpit
      if (ordersData.length > 0) {
        setSelectedOrder((prev) => {
          if (!prev) return ordersData[0];
          const updated = ordersData.find((o) => o.order_id === prev.order_id);
          return updated || ordersData[0];
        });
      }

      if (account) {
        const bal = await fetchStudionetBalance(account);
        setBalance(bal);
      }
    } catch (err) {
      console.error('Error fetching contract data:', err);
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
    }
  }, [contractAddress, account]);

  // Initial load
  useEffect(() => {
    setIsLoading(true);
    loadData();

    if (typeof window !== 'undefined' && (window as any).ethereum) {
      (window as any).ethereum
        .request({ method: 'eth_accounts' })
        .then(async (accounts: string[]) => {
          if (accounts.length > 0) {
            setAccount(accounts[0]);
            const bal = await fetchStudionetBalance(accounts[0]);
            setBalance(bal);
          }
        })
        .catch(() => {});

      (window as any).ethereum.on('accountsChanged', (accounts: string[]) => {
        if (accounts.length > 0) {
          setAccount(accounts[0]);
          fetchStudionetBalance(accounts[0]).then(setBalance);
        } else {
          setAccount(null);
          setBalance('0');
        }
      });
    }
  }, [loadData]);

  const handleSaveContractAddress = (newAddr: string) => {
    saveContractAddress(newAddr);
    setContractAddress(newAddr);
    setStatusMessage({
      type: 'info',
      text: `Contract address updated: ${newAddr}`,
    });
  };

  // Actions
  const handleOrderSynthesis = async (
    targetFn: string,
    specUrl: string,
    durationBlocks: number,
    depositWei: bigint
  ) => {
    if (!account) {
      await connectWallet();
      return;
    }
    const tx = await orderSynthesisOnChain(
      contractAddress,
      account,
      targetFn,
      specUrl,
      durationBlocks,
      depositWei
    );
    setStatusMessage({
      type: 'success',
      text: `DNA synthesis commissioned on-chain! Tx: ${tx.slice(0, 10)}...`,
    });
    await loadData();
  };

  const handleSubmitProof = async (orderId: number, qcReportUrl: string) => {
    if (!account) {
      await connectWallet();
      return;
    }
    const tx = await submitSynthesisProofOnChain(contractAddress, account, orderId, qcReportUrl);
    setStatusMessage({
      type: 'success',
      text: `Sequencing QC report submitted for Order #${orderId}! Tx: ${tx.slice(0, 10)}...`,
    });
    await loadData();
  };

  const handleAdjudicate = async (orderId: number) => {
    if (!account) {
      await connectWallet();
      return;
    }
    try {
      setIsProcessingAction(true);
      setStatusMessage({
        type: 'info',
        text: `Convening AI Biosecurity Jury for Order #${orderId}. Digesting live FASTA/QC and executing consensus...`,
      });
      const tx = await adjudicateBiosecurityOnChain(contractAddress, account, orderId);
      setStatusMessage({
        type: 'success',
        text: `Consensus adjudication complete for Order #${orderId}! Tx: ${tx.slice(0, 10)}...`,
      });
      await loadData();
    } catch (err: any) {
      console.error('Adjudication error:', err);
      setStatusMessage({
        type: 'error',
        text: err?.message || 'Biosecurity adjudication failed on Studionet.',
      });
    } finally {
      setIsProcessingAction(false);
    }
  };

  const handleAppeal = async (orderId: number, disputeReason: string, bondWei: bigint) => {
    if (!account) {
      await connectWallet();
      return;
    }
    const tx = await appealVerdictOnChain(contractAddress, account, orderId, disputeReason, bondWei);
    setStatusMessage({
      type: 'success',
      text: `Appeal filed and 10% bond staked for Order #${orderId}! Tx: ${tx.slice(0, 10)}...`,
    });
    await loadData();
  };

  const handleFinalize = async (orderId: number) => {
    if (!account) {
      await connectWallet();
      return;
    }
    try {
      setIsProcessingAction(true);
      const tx = await finalizeSettlementOnChain(contractAddress, account, orderId);
      setStatusMessage({
        type: 'success',
        text: `Settlement finalized and escrow disbursed for Order #${orderId}! Tx: ${tx.slice(0, 10)}...`,
      });
      await loadData();
    } catch (err: any) {
      console.error('Finalize error:', err);
      setStatusMessage({
        type: 'error',
        text: err?.message || 'Finalization failed. Ensure 24-block cooling-off has elapsed.',
      });
    } finally {
      setIsProcessingAction(false);
    }
  };

  const handleCancel = async (orderId: number) => {
    if (!account) {
      await connectWallet();
      return;
    }
    try {
      setIsProcessingAction(true);
      const tx = await cancelOrReclaimOnChain(contractAddress, account, orderId);
      setStatusMessage({
        type: 'success',
        text: `Order #${orderId} cancelled and funds reclaimed! Tx: ${tx.slice(0, 10)}...`,
      });
      await loadData();
    } catch (err: any) {
      console.error('Cancel error:', err);
      setStatusMessage({
        type: 'error',
        text: err?.message || 'Cannot cancel: Order duration has not expired.',
      });
    } finally {
      setIsProcessingAction(false);
    }
  };

  // Filtered orders
  const filteredOrders = orders.filter((o) => {
    if (selectedFilter === 'open' && o.status !== 0) return false;
    if (selectedFilter === 'synthesis' && o.status !== 1) return false;
    if (selectedFilter === 'cooling' && o.status !== 2) return false;
    if (selectedFilter === 'verified' && o.status !== 3) return false;
    if (selectedFilter === 'blocked' && o.status !== 4) return false;
    if (selectedFilter === 'defective' && o.status !== 5) return false;
    if (selectedFilter === 'disputed' && o.status !== 7) return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchFn = o.target_protein_function.toLowerCase().includes(q);
      const matchRes = o.researcher.toLowerCase().includes(q);
      const matchFnd = o.foundry.toLowerCase().includes(q);
      const matchId = String(o.order_id) === q;
      return matchFn || matchRes || matchFnd || matchId;
    }

    return true;
  });

  return (
    <div className="min-h-screen bg-[#F1F5F9] text-[#0F172A] font-sans selection:bg-emerald-100 selection:text-emerald-800 flex flex-col">
      
      {/* Precision Cleanroom Navbar */}
      <Navbar
        account={account}
        balance={balance}
        isConnecting={isConnecting}
        onConnect={connectWallet}
        onRefresh={loadData}
        isRefreshing={isRefreshing}
        contractAddress={contractAddress}
        onSaveContractAddress={handleSaveContractAddress}
      />

      {/* Streaming Nucleotide Sequence Ribbon */}
      <NucleotideRibbon />

      {/* Main Surface */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        
        {/* Status Toast Alert */}
        {statusMessage && (
          <div
            className={`mb-5 p-4 rounded-2xl border text-xs font-semibold flex items-center justify-between shadow-sm animate-fadeIn ${
              statusMessage.type === 'success'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : statusMessage.type === 'error'
                ? 'bg-rose-50 border-rose-200 text-rose-800'
                : 'bg-blue-50 border-blue-200 text-blue-800'
            }`}
          >
            <div className="flex items-center gap-2">
              {statusMessage.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-600" />
              )}
              <span>{statusMessage.text}</span>
            </div>
            <button
              onClick={() => setStatusMessage(null)}
              className="text-slate-400 hover:text-slate-600 ml-4 font-bold"
            >
              ✕
            </button>
          </div>
        )}

        {/* Layout Control Bar & Cleanroom Telemetry Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <h1 className="font-display font-extrabold text-xl sm:text-2xl text-slate-900 tracking-tight">
                Genomic Cleanroom & Bio-Foundry Console
              </h1>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Autonomous Synthetic Biology Protocol & DNA Sequence Safety Escrow • GenLayer Studionet #61999
            </p>
          </div>

          {/* Layout Mode Switcher */}
          <div className="flex items-center gap-2 self-start sm:self-auto bg-white p-1 rounded-2xl border border-slate-200 shadow-xs">
            <button
              onClick={() => setLayoutMode('cockpit')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                layoutMode === 'cockpit'
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <Columns3 className="w-3.5 h-3.5" />
              <span>Cockpit Console</span>
            </button>

            <button
              onClick={() => setLayoutMode('grid')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                layoutMode === 'grid'
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              <span>Matrix Ledger</span>
            </button>

            <button
              onClick={() => setIsStudioModalOpen(true)}
              className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-teal-50 text-teal-700 hover:bg-teal-100 border border-teal-200 text-xs font-bold transition-all ml-1"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Simulator</span>
            </button>
          </div>
        </div>

        {/* ── MODE 1: NOVEL 3-PANEL COCKPIT CONSOLE ────────────────── */}
        {layoutMode === 'cockpit' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
            
            {/* Left Column: Order Matrix Sidebar (3 Cols) */}
            <div className="lg:col-span-3">
              <OrderMatrixSidebar
                orders={filteredOrders}
                selectedOrderId={selectedOrder?.order_id || null}
                onSelectOrder={(ord) => setSelectedOrder(ord)}
                onOpenCommission={() => {
                  if (!account) connectWallet();
                  else setIsOrderModalOpen(true);
                }}
                selectedFilter={selectedFilter}
                onFilterChange={setSelectedFilter}
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
              />
            </div>

            {/* Center Column: Genomic Inspection Cockpit (6 Cols) */}
            <div className="lg:col-span-6">
              <GenomicInspectionCockpit
                order={selectedOrder}
                currentUser={account}
                onOpenSubmitProof={(ord) => {
                  setActiveModalOrder(ord);
                  setIsProofModalOpen(true);
                }}
                onOpenInspector={(ord) => {
                  setActiveModalOrder(ord);
                  setIsInspectorModalOpen(true);
                }}
                onOpenDispute={(ord) => {
                  setActiveModalOrder(ord);
                  setIsDisputeModalOpen(true);
                }}
                onAdjudicate={handleAdjudicate}
                onFinalize={handleFinalize}
                onCancel={handleCancel}
                isProcessing={isProcessingAction}
              />
            </div>

            {/* Right Column: DeSci Protocol Vault Sidebar (3 Cols) */}
            <div className="lg:col-span-3">
              <DeSciVaultSidebar
                stats={stats}
                orders={orders}
                onOpenStudio={() => setIsStudioModalOpen(true)}
                onOpenCommission={() => {
                  if (!account) connectWallet();
                  else setIsOrderModalOpen(true);
                }}
              />
            </div>
          </div>
        )}

        {/* ── MODE 2: MATRIX LEDGER GRID VIEW ──────────────────────── */}
        {layoutMode === 'grid' && (
          <div className="space-y-6">
            <StatsBar stats={stats} orders={orders} />

            {/* Filter Tabs in Grid Mode */}
            <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center gap-1 overflow-x-auto text-xs font-semibold">
                {[
                  { id: 'all', label: 'All Orders' },
                  { id: 'open', label: 'Open' },
                  { id: 'synthesis', label: 'In Synthesis' },
                  { id: 'cooling', label: 'Cooling-Off' },
                  { id: 'verified', label: 'Verified' },
                  { id: 'blocked', label: 'Biohazard' },
                  { id: 'defective', label: 'Defective' },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setSelectedFilter(tab.id)}
                    className={`px-3 py-1.5 rounded-xl whitespace-nowrap transition-all ${
                      selectedFilter === tab.id
                        ? 'bg-slate-900 text-white shadow-xs'
                        : 'text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search orders..."
                  className="px-3.5 py-1.5 rounded-xl border border-slate-200 bg-slate-50 text-xs text-slate-800"
                />
                <button
                  onClick={() => {
                    if (!account) connectWallet();
                    else setIsOrderModalOpen(true);
                  }}
                  className="flex items-center gap-1 px-4 py-1.5 rounded-xl bg-emerald-600 text-white text-xs font-bold shadow-sm"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Commission</span>
                </button>
              </div>
            </div>

            {/* Grid Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {filteredOrders.map((order) => (
                <div
                  key={order.order_id}
                  onClick={() => {
                    setSelectedOrder(order);
                    setLayoutMode('cockpit');
                  }}
                  className="cursor-pointer"
                >
                  <BioOrderCard
                    order={order}
                    currentUser={account}
                    onOpenSubmitProof={(ord) => {
                      setActiveModalOrder(ord);
                      setIsProofModalOpen(true);
                    }}
                    onOpenInspector={(ord) => {
                      setActiveModalOrder(ord);
                      setIsInspectorModalOpen(true);
                    }}
                    onOpenDispute={(ord) => {
                      setActiveModalOrder(ord);
                      setIsDisputeModalOpen(true);
                    }}
                    onAdjudicate={handleAdjudicate}
                    onFinalize={handleFinalize}
                    onCancel={handleCancel}
                    isProcessing={isProcessingAction}
                  />
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Modals */}
      <OrderSynthesisModal
        isOpen={isOrderModalOpen}
        onClose={() => setIsOrderModalOpen(false)}
        onSubmit={handleOrderSynthesis}
        userBalance={balance}
      />

      <SubmitProofModal
        isOpen={isProofModalOpen}
        onClose={() => {
          setIsProofModalOpen(false);
          setActiveModalOrder(null);
        }}
        order={activeModalOrder}
        onSubmit={handleSubmitProof}
      />

      <SequenceInspectorModal
        isOpen={isInspectorModalOpen}
        onClose={() => {
          setIsInspectorModalOpen(false);
          setActiveModalOrder(null);
        }}
        order={activeModalOrder}
      />

      <DisputeModal
        isOpen={isDisputeModalOpen}
        onClose={() => {
          setIsDisputeModalOpen(false);
          setActiveModalOrder(null);
        }}
        order={activeModalOrder}
        onSubmit={handleAppeal}
      />

      <LiveQCStudioModal
        isOpen={isStudioModalOpen}
        onClose={() => setIsStudioModalOpen(false)}
      />
    </div>
  );
}
export default App;
