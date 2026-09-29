export function formatGen(wei: string | bigint | number | undefined): string {
  if (!wei) return '0';
  try {
    const weiBig = typeof wei === 'bigint' ? wei : BigInt(wei.toString());
    if (weiBig === 0n) return '0';
    const whole = weiBig / 10n ** 18n;
    const remainder = weiBig % 10n ** 18n;
    if (remainder === 0n) {
      return whole.toString();
    }
    let fraction = remainder.toString().padStart(18, '0').slice(0, 4);
    fraction = fraction.replace(/0+$/, '');
    if (!fraction) {
      return whole.toString();
    }
    return `${whole}.${fraction}`;
  } catch (e) {
    return '0';
  }
}

export function parseGenToWei(genStr: string | number): bigint {
  try {
    const clean = String(genStr).trim();
    if (!clean || isNaN(Number(clean))) return 0n;
    const [wholePart, decPart = ''] = clean.split('.');
    const paddedDec = decPart.padEnd(18, '0').slice(0, 18);
    return BigInt(wholePart) * 10n ** 18n + BigInt(paddedDec);
  } catch (e) {
    return 0n;
  }
}

export function truncateAddress(addr: string): string {
  if (!addr || addr === '0x0000000000000000000000000000000000000000') return 'UNASSIGNED';
  if (addr.length <= 12) return addr;
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`.toLowerCase();
}

export interface StatusMeta {
  code: string;
  label: string;
  badgeBg: string;
  ledColor: string;
  borderColor: string;
  description: string;
  category: 'open' | 'active' | 'cooling' | 'verified' | 'blocked' | 'defective' | 'disputed' | 'cancelled';
}

export function getStatusMeta(status: number): StatusMeta {
  switch (status) {
    case 0:
      return {
        code: 'ORDER_OPEN',
        label: 'OPEN FOR FOUNDRY',
        badgeBg: 'bg-slate-100 text-slate-700 border-slate-300',
        ledColor: 'bg-slate-400',
        borderColor: 'border-slate-300 hover:border-slate-400',
        description: 'Escrow locked. Awaiting DNA synthesis foundry claim & sequencing submission.',
        category: 'open',
      };
    case 1:
      return {
        code: 'IN_SYNTHESIS',
        label: 'IN SYNTHESIS & REVIEW',
        badgeBg: 'bg-purple-50 text-purple-700 border-purple-200',
        ledColor: 'bg-purple-500 animate-pulse',
        borderColor: 'border-purple-300 hover:border-purple-400',
        description: 'Foundry submitted sequencing QC proof. AI Biosecurity Jury examining codon alignment.',
        category: 'active',
      };
    case 2:
      return {
        code: 'AWAITING_PAYOUT',
        label: 'COOLING-OFF (24 BLOCKS)',
        badgeBg: 'bg-blue-50 text-blue-700 border-blue-200',
        ledColor: 'bg-blue-500 animate-ping',
        borderColor: 'border-blue-300 hover:border-blue-400',
        description: 'Biosecurity verdict reached. 24-block timelock window open for dispute/appeal.',
        category: 'cooling',
      };
    case 3:
      return {
        code: 'VERIFIED_PAID',
        label: 'VERIFIED & RELEASED',
        badgeBg: 'bg-emerald-50 text-emerald-700 border-emerald-300',
        ledColor: 'bg-emerald-500',
        borderColor: 'border-emerald-300 hover:border-emerald-400',
        description: 'Fidelity & biosecurity verified (>=80%). 100% escrow disbursed to Foundry.',
        category: 'verified',
      };
    case 4:
      return {
        code: 'BIOHAZARD_SLASHED',
        label: 'BIOHAZARD BLOCKED',
        badgeBg: 'bg-orange-50 text-orange-700 border-orange-300',
        ledColor: 'bg-orange-600',
        borderColor: 'border-orange-300 hover:border-orange-500',
        description: 'Prohibited biological agent/toxin detected. Researcher escrow confiscated to Biosecurity Reserve.',
        category: 'blocked',
      };
    case 5:
      return {
        code: 'DEFECTIVE_REFUNDED',
        label: 'DEFECTIVE (REFUNDED)',
        badgeBg: 'bg-amber-50 text-amber-700 border-amber-300',
        ledColor: 'bg-amber-500',
        borderColor: 'border-amber-300 hover:border-amber-400',
        description: 'Sequence mutated or fidelity < 80%. 100% escrow refunded to Researcher.',
        category: 'defective',
      };
    case 6:
      return {
        code: 'CANCELLED',
        label: 'CANCELLED / RECLAIMED',
        badgeBg: 'bg-gray-100 text-gray-600 border-gray-300',
        ledColor: 'bg-gray-400',
        borderColor: 'border-gray-300',
        description: 'Order expired unclaimed or cancelled by researcher.',
        category: 'cancelled',
      };
    case 7:
      return {
        code: 'DISPUTED',
        label: 'UNDER DISPUTE APPEAL',
        badgeBg: 'bg-rose-50 text-rose-700 border-rose-300',
        ledColor: 'bg-rose-500 animate-pulse',
        borderColor: 'border-rose-300 hover:border-rose-400',
        description: 'Verdict contested with 10% appeal bond. Escrow frozen for protocol re-examination.',
        category: 'disputed',
      };
    default:
      return {
        code: 'UNKNOWN',
        label: 'UNKNOWN STATUS',
        badgeBg: 'bg-gray-100 text-gray-500 border-gray-200',
        ledColor: 'bg-gray-400',
        borderColor: 'border-gray-200',
        description: 'Unrecognized order state.',
        category: 'open',
      };
  }
}

export interface PresetSynthesisOrder {
  title: string;
  targetFunction: string;
  specUrl: string;
  depositGen: string;
  category: string;
}

export const PRESET_SYNTHESIS_ORDERS: PresetSynthesisOrder[] = [
  {
    title: 'Monoclonal Antibody Anti-IL6 Fab Fragment',
    targetFunction: 'Therapeutic monoclonal antibody binding domain specifically targeting Human Interleukin-6 for cytokine storm mitigation in severe autoimmune syndromes.',
    specUrl: 'https://raw.githubusercontent.com/biopython/biopython/master/Tests/GenBank/cor6_6.gb',
    depositGen: '3.5',
    category: 'Therapeutic Protein',
  },
  {
    title: 'Thermostable PETase Enzyme for Plastic Depolymerization',
    targetFunction: 'Engineered high-efficiency Ideonella sakaiensis PETase variant with enhanced melting temperature (Tm=78C) for circular enzymatic recycling of polyethylene terephthalate.',
    specUrl: 'https://raw.githubusercontent.com/biopython/biopython/master/Tests/SwissProt/sp001.dat',
    depositGen: '2.0',
    category: 'Bioremediation Enzyme',
  },
  {
    title: 'Synthetic Luciferase Biosensor for Arsenic Toxicity',
    targetFunction: 'Allosteric biosensor cassette coupling ArsR repressor promoter with codon-optimized NanoLuciferase for real-time groundwater arsenic quantification.',
    specUrl: 'https://raw.githubusercontent.com/biopython/biopython/master/Tests/FASTA/f002',
    depositGen: '1.8',
    category: 'Biosensor Reporter',
  }
];

export const PRESET_FOUNDRY_PROOFS = [
  {
    label: 'Verified Pure Synthesis (99.4% Fidelity)',
    url: 'https://raw.githubusercontent.com/biopython/biopython/master/Tests/GenBank/cor6_6.gb',
    description: 'Clean Sanger/NGS sequencing alignment confirming 100% full-length target identity with no frame-shifts.',
  },
  {
    label: 'Defective Mutated Batch (Low Fidelity / 32%)',
    url: 'https://raw.githubusercontent.com/biopython/biopython/master/Tests/FASTA/f001',
    description: 'Sequencing reads show early termination and point mutations failing the 80% fidelity benchmark.',
  }
];
