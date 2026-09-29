import React, { useState, useEffect } from 'react';
import { Dna, Activity, ShieldCheck } from 'lucide-react';

export const NucleotideRibbon: React.FC = () => {
  const [activeOffset, setActiveOffset] = useState(0);

  // Simulated streaming sequencing base pairs: A (Adenine), T (Thymine), C (Cytosine), G (Guanine)
  const bases = ['A', 'T', 'G', 'C', 'C', 'A', 'T', 'G', 'G', 'T', 'A', 'A', 'C', 'G', 'T', 'A', 'A', 'T', 'C', 'G', 'G', 'A', 'T', 'C', 'T', 'A', 'C', 'G', 'A', 'T'];

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveOffset((prev) => (prev + 1) % bases.length);
    }, 1500);
    return () => clearInterval(interval);
  }, [bases.length]);

  const getBaseColor = (base: string) => {
    switch (base) {
      case 'A': return 'text-emerald-700 bg-emerald-100 border-emerald-300';
      case 'T': return 'text-rose-700 bg-rose-100 border-rose-300';
      case 'C': return 'text-blue-700 bg-blue-100 border-blue-300';
      case 'G': return 'text-amber-700 bg-amber-100 border-amber-300';
      default: return 'text-slate-700 bg-slate-100 border-slate-300';
    }
  };

  return (
    <div className="bg-slate-100/80 border-b border-slate-200/80 py-1.5 px-4 sm:px-6 lg:px-8 overflow-hidden text-[11px] font-mono">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        
        {/* Left Telemetry Tag */}
        <div className="hidden md:flex items-center gap-2 text-slate-500 shrink-0">
          <Dna className="w-3.5 h-3.5 text-emerald-600 animate-pulse" />
          <span className="font-bold text-[10px] uppercase tracking-wider text-slate-700">
            High-Throughput Sequencing Stream
          </span>
          <span className="text-slate-300">|</span>
          <span className="text-[10px] text-emerald-700 font-semibold bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
            Q-Score: 39.8 (99.99%)
          </span>
        </div>

        {/* Animated Nucleotide Base-Pair Ribbon */}
        <div className="flex items-center gap-1.5 overflow-hidden select-none">
          {bases.map((base, idx) => {
            const isHighlight = idx === activeOffset;
            return (
              <span
                key={idx}
                className={`w-5 h-5 flex items-center justify-center rounded text-[10px] font-bold border transition-all duration-300 ${getBaseColor(
                  base
                )} ${isHighlight ? 'scale-125 ring-2 ring-emerald-500 shadow-sm z-10' : 'opacity-85'}`}
                title={`Codon locus ${idx + 1}: ${base}`}
              >
                {base}
              </span>
            );
          })}
        </div>

        {/* Right Status */}
        <div className="hidden lg:flex items-center gap-2 text-slate-500 shrink-0 text-[10px]">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <span>Biosecurity Jury Active</span>
          <span className="text-slate-300">|</span>
          <span className="font-semibold text-slate-700">gl.nondet.web.render</span>
        </div>
      </div>
    </div>
  );
};
