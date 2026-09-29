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
  Microscope
} from 'lucide-react';
import { Navbar } from './components/Navbar';
import { StatsBar } from './components/StatsBar';
import { BioOrderCard } from './components/BioOrderCard';
import { BioForensicWorkbench } from './components/BioForensicWorkbench';
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
  const [workbenchOrder, setWorkbenchOrder] = useState<BioOrderData | null>(null);

  // Filters & Search
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Modals
  const [isOrderModalOpen, setIsOrderModalOpen] = useState(false);
  const [isProofModalOpen, setIsProofModalOpen] = useState(false);
  const [isInspectorModalOpen, setIsInspectorModalOpen] = useState(false);
  const [isDisputeModalOpen, setIsDisputeModalOpen] = useState(false);
  const [isStudioModalOpen, setIsStudioModalOpen] = useState(false);
  const [activeOrder, setActiveOrder] = useState<BioOrderData | null>(null);
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

      // Select first order for workbench if none active
      if (ordersData.length > 0) {
        setWorkbenchOrder((prev) => {
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
        text: `Convening AI Biosecurity Jury for Order #${orderId}. Fetching live FASTA/QC and running LLM consensus...`,
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
    <div className="min-h-screen bg-[#F1F5F9] text-[#0F172A] font-sans selection:bg-emerald-100 selection:text-emerald-800">
      
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

      {/* Main Cleanroom Surface */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Status Toast Alert */}
        {statusMessage && (
          <div
            className={`mb-6 p-4 rounded-2xl border text-xs font-semibold flex items-center justify-between shadow-sm animate-fadeIn ${
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

        {/* Hero Banner: Genomic Cleanroom & Biosecurity Protocol */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-sm mb-8 relative overflow-hidden">
          <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-emerald-50/60 to-transparent pointer-events-none" />
          <div className="max-w-3xl relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold mb-3">
              <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse" />
              <span>Decentralized Science (DeSci) & Synthetic Biosecurity</span>
            </div>

            <h1 className="font-display text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-slate-900 leading-tight">
              Autonomous Synthetic Biology Protocol & DNA Safety Escrow
            </h1>

            <p className="mt-3 text-sm text-slate-600 leading-relaxed">
              Enabling decentralized AI agents and researchers to commission gene and protein synthesis with on-chain biosecurity screening. Escrow is released only when GenLayer AI juries verify sequence alignment fidelity (≥80%) and certify zero dual-use pathogen risk.
            </p>

            {/* Quick Action Chamber */}
            <div className="mt-6 flex flex-wrap items-center gap-3">
              <button
                onClick={() => {
                  if (!account) {
                    connectWallet();
                  } else {
                    setIsOrderModalOpen(true);
                  }
                }}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20 transition-all active:scale-[0.98]"
              >
                <Plus className="w-4 h-4" />
                <span>Commission DNA Synthesis</span>
              </button>

              <button
                onClick={() => setIsStudioModalOpen(true)}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold shadow-md transition-all active:scale-[0.98]"
              >
                <Sparkles className="w-4 h-4 text-emerald-400" />
                <span>Open QC Consensus Studio</span>
              </button>

              <a
                href={STUDIO_URL}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-xs font-semibold text-slate-700 transition-colors"
              >
                <span>GenLayer Studio Console</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        </div>

        {/* Aggregated Cleanroom Metrics */}
        <StatsBar stats={stats} orders={orders} />

        {/* Interactive Forensic Workbench Section */}
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Microscope className="w-5 h-5 text-emerald-600" />
            <h2 className="font-display font-extrabold text-lg text-slate-900">
              Forensic Sequence Alignment & Biosecurity Workbench
            </h2>
          </div>
          <span className="text-xs text-slate-400 font-semibold hidden sm:inline">
            Click any order card below to inspect in real-time
          </span>
        </div>

        <BioForensicWorkbench
          order={workbenchOrder}
          currentUser={account}
          onOpenSubmitProof={(ord) => {
            setActiveOrder(ord);
            setIsProofModalOpen(true);
          }}
          onOpenDispute={(ord) => {
            setActiveOrder(ord);
            setIsDisputeModalOpen(true);
          }}
          onAdjudicate={handleAdjudicate}
          onFinalize={handleFinalize}
          onCancel={handleCancel}
          isProcessing={isProcessingAction}
        />

        {/* Filter & Search Bar */}
        <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
          
          {/* Status Tabs */}
          <div className="flex items-center gap-1 overflow-x-auto pb-1 md:pb-0 text-xs font-semibold">
            {[
              { id: 'all', label: 'All Orders' },
              { id: 'open', label: 'Open' },
              { id: 'synthesis', label: 'In Synthesis' },
              { id: 'cooling', label: 'Cooling-Off' },
              { id: 'verified', label: 'Verified' },
              { id: 'blocked', label: 'Biohazard' },
              { id: 'defective', label: 'Defective' },
              { id: 'disputed', label: 'Disputed' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setSelectedFilter(tab.id)}
                className={`px-3 py-1.5 rounded-xl whitespace-nowrap transition-all ${
                  selectedFilter === tab.id
                    ? 'bg-slate-900 text-white shadow-sm'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div className="relative min-w-[240px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search protein function, ID, or address..."
              className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-200 bg-slate-50 text-xs text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500"
            />
          </div>
        </div>

        {/* Orders Grid Ledger */}
        {isLoading ? (
          <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center">
            <RefreshCw className="w-8 h-8 text-emerald-600 animate-spin mx-auto mb-3" />
            <p className="text-xs font-bold text-slate-700">Connecting to GenLayer Studionet RPC...</p>
            <p className="text-[11px] text-slate-400 mt-1">Hydrating synthesis ledger & biosecurity states</p>
          </div>
        ) : filteredOrders.length === 0 ? (
          <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center max-w-xl mx-auto">
            <div className="w-12 h-12 rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-3">
              <Dna className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-slate-900">No Bio Orders Found</h3>
            <p className="text-xs text-slate-500 mt-1 mb-5">
              {searchQuery || selectedFilter !== 'all'
                ? 'No synthesis orders match your current filter parameters.'
                : 'No DNA synthesis escrows are currently active on this contract.'}
            </p>
            <button
              onClick={() => setIsOrderModalOpen(true)}
              className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20"
            >
              Commission First DNA Synthesis
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredOrders.map((order) => (
              <div
                key={order.order_id}
                onClick={() => setWorkbenchOrder(order)}
                className={`cursor-pointer transition-all ${
                  workbenchOrder?.order_id === order.order_id
                    ? 'ring-2 ring-emerald-500 rounded-2xl'
                    : ''
                }`}
              >
                <BioOrderCard
                  order={order}
                  currentUser={account}
                  onOpenSubmitProof={(ord) => {
                    setActiveOrder(ord);
                    setIsProofModalOpen(true);
                  }}
                  onOpenInspector={(ord) => {
                    setActiveOrder(ord);
                    setIsInspectorModalOpen(true);
                  }}
                  onOpenDispute={(ord) => {
                    setActiveOrder(ord);
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
          setActiveOrder(null);
        }}
        order={activeOrder}
        onSubmit={handleSubmitProof}
      />

      <SequenceInspectorModal
        isOpen={isInspectorModalOpen}
        onClose={() => {
          setIsInspectorModalOpen(false);
          setActiveOrder(null);
        }}
        order={activeOrder}
      />

      <DisputeModal
        isOpen={isDisputeModalOpen}
        onClose={() => {
          setIsDisputeModalOpen(false);
          setActiveOrder(null);
        }}
        order={activeOrder}
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
