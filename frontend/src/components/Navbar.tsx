import React, { useState } from 'react';
import { 
  Dna, 
  Wallet, 
  ExternalLink, 
  ShieldCheck, 
  Settings, 
  RefreshCw, 
  Copy, 
  Check, 
  AlertCircle 
} from 'lucide-react';
import { truncateAddress } from '../utils/helpers';
import { STUDIO_URL } from '../config/genlayer';

interface NavbarProps {
  account: string | null;
  balance: string;
  isConnecting: boolean;
  onConnect: () => void;
  onRefresh: () => void;
  isRefreshing: boolean;
  contractAddress: string;
  onSaveContractAddress: (addr: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  account,
  balance,
  isConnecting,
  onConnect,
  onRefresh,
  isRefreshing,
  contractAddress,
  onSaveContractAddress,
}) => {
  const [showConfig, setShowConfig] = useState(false);
  const [customAddress, setCustomAddress] = useState(contractAddress);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (account) {
      navigator.clipboard.writeText(account);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleSaveContract = (e: React.FormEvent) => {
    e.preventDefault();
    if (customAddress.trim().startsWith('0x')) {
      onSaveContractAddress(customAddress.trim());
      setShowConfig(false);
    }
  };

  return (
    <>
      <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 flex items-center justify-between">
          
          {/* Logo & Protocol Branding */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center shadow-md shadow-emerald-500/20 text-white">
              <Dna className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-display font-extrabold text-xl tracking-tight text-slate-900">
                  Agent<span className="text-emerald-600">Bio</span>
                </span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  DeSci Escrow
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium">
                Autonomous Synthetic Biology Protocol & DNA Safety Escrow
              </p>
            </div>
          </div>

          {/* Right Action Bar */}
          <div className="flex items-center gap-3">
            {/* Studionet Chain Badge */}
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs font-semibold text-slate-700">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
              <span>Studionet</span>
              <span className="font-mono text-slate-400 text-[11px]">#61999</span>
            </div>

            {/* Refresh Button */}
            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              className="p-2 rounded-lg border border-slate-200 bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors disabled:opacity-50"
              title="Refresh ledger state"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-emerald-600' : ''}`} />
            </button>

            {/* Contract Settings */}
            <button
              onClick={() => {
                setCustomAddress(contractAddress);
                setShowConfig(true);
              }}
              className="p-2 rounded-lg border border-slate-200 bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors"
              title="Configure Contract Address"
            >
              <Settings className="w-4 h-4" />
            </button>

            {/* Wallet Connect */}
            {account ? (
              <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-xl p-1 pl-3 shadow-sm">
                <div className="flex flex-col text-right pr-1">
                  <div className="flex items-center gap-1">
                    <span className="text-xs font-bold text-slate-900 font-mono">
                      {balance} GEN
                    </span>
                    {balance === '0' && (
                      <a
                        href={STUDIO_URL}
                        target="_blank"
                        rel="noreferrer"
                        title="Get testnet GEN from GenLayer Studio"
                        className="text-[10px] text-amber-600 underline font-semibold flex items-center gap-0.5 ml-1"
                      >
                        <AlertCircle className="w-3 h-3 inline text-amber-500" />
                        Faucet
                      </a>
                    )}
                  </div>
                  <span className="text-[11px] text-slate-500 font-mono">
                    {truncateAddress(account)}
                  </span>
                </div>

                <button
                  onClick={handleCopy}
                  className="p-1.5 rounded-lg bg-white border border-slate-200 text-slate-500 hover:text-slate-800 transition-colors"
                  title="Copy address"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            ) : (
              <button
                onClick={onConnect}
                disabled={isConnecting}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-md shadow-slate-900/10 transition-all active:scale-[0.98] disabled:opacity-50"
              >
                <Wallet className="w-4 h-4" />
                <span>{isConnecting ? 'Connecting...' : 'Connect MetaMask'}</span>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Contract Config Modal */}
      {showConfig && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full p-6 text-slate-900">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Contract Configuration</h3>
                  <p className="text-xs text-slate-500">GenLayer Studionet Intelligent Contract</p>
                </div>
              </div>
              <button
                onClick={() => setShowConfig(false)}
                className="text-slate-400 hover:text-slate-600 text-sm font-semibold p-1"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveContract} className="mt-5 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Deployed AgentBio Contract Address
                </label>
                <input
                  type="text"
                  value={customAddress}
                  onChange={(e) => setCustomAddress(e.target.value)}
                  placeholder="0x..."
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 font-mono text-xs text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500"
                />
              </div>

              <div className="bg-slate-50 rounded-xl p-3 border border-slate-200 text-xs text-slate-600 space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-500">RPC Endpoint:</span>
                  <span className="font-mono text-slate-800">studio.genlayer.com/api</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Chain ID:</span>
                  <span className="font-mono text-slate-800">61999 (0xF1EF)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Consensus Mode:</span>
                  <span className="font-semibold text-emerald-700">Subjective Non-det LLM</span>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2">
                <a
                  href={STUDIO_URL}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-emerald-600 hover:text-emerald-700 font-semibold flex items-center gap-1"
                >
                  <span>Open GenLayer Studio</span>
                  <ExternalLink className="w-3 h-3" />
                </a>

                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setShowConfig(false)}
                    className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm"
                  >
                    Save Address
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};
