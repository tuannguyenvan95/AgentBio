import { createClient } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';
import { formatGen } from '../utils/helpers';

export const STUDIONET_CHAIN_ID = 61999;
export const STUDIONET_CHAIN_ID_HEX = '0xf22f'; // 61999 in hex (or 0xF1EF)
export const STUDIONET_RPC_URL = 'https://studio.genlayer.com/api';
export const STUDIO_URL = 'https://studio.genlayer.com';

// Default deployed contract address (updated via UI or localStorage)
export const DEFAULT_CONTRACT_ADDRESS = '0x58E439f80483B72FfAB6704dDB5d447439986549';

export function getSavedContractAddress(): string {
  if (typeof window !== 'undefined') {
    try {
      const stored = localStorage.getItem('agentbio_contract_address');
      if (
        stored &&
        stored.trim().startsWith('0x') &&
        stored.trim() !== '0xD89bF46b5Ac5f096288647EB8FcaE12F6C7B7f16' &&
        stored.trim() !== '0x567A9F625931Da69fd662a8a0F7ad4FF8276fb7D' &&
        stored.trim() !== '0xBF72c8b8b761BA05a0de8FF012658EF3956B49D6' &&
        stored.trim() !== '0x4c9a39c9D6355718bB46a49aDa9C129Ce05bE6F9' &&
        stored.trim() !== '0xd2F4c421a5365FA80e87d6b4E4b078792289694D'
      ) {
        return stored.trim();
      }
    } catch (e) {
      // ignore
    }
  }
  return DEFAULT_CONTRACT_ADDRESS;
}

export function saveContractAddress(address: string) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('agentbio_contract_address', address.trim());
  }
}

/**
 * Fetch real on-chain GEN balance directly from Studionet RPC endpoint
 */
export async function fetchStudionetBalance(address: string): Promise<string> {
  if (!address) return '0';

  try {
    const res = await fetch(STUDIONET_RPC_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'eth_getBalance',
        params: [address, 'latest'],
        id: Date.now(),
      }),
    });
    const json = await res.json();
    if (json && json.result !== undefined && json.result !== null) {
      return formatGen(json.result);
    }
  } catch (err) {
    console.warn('Direct Studionet RPC eth_getBalance error:', err);
  }

  if (typeof window !== 'undefined' && (window as any).ethereum) {
    try {
      const balHex = await (window as any).ethereum.request({
        method: 'eth_getBalance',
        params: [address, 'latest'],
      });
      if (balHex) {
        return formatGen(balHex);
      }
    } catch (e) {
      console.warn('MetaMask eth_getBalance fallback error:', e);
    }
  }

  return '0';
}

export interface BioOrderData {
  order_id: number;
  researcher: string;
  foundry: string;
  dispute_initiator?: string;
  escrow_amount: string;
  dispute_bond?: string;
  target_protein_function: string;
  sequence_spec_url: string;
  spec_evidence_hash?: string;
  qc_report_url: string;
  qc_evidence_hash?: string;
  evidence_hash?: string;
  status: number; // 0..7
  verdict: string;
  reason: string;
  confidence: number;
  fidelity_score: number;
  created_at?: string;
  expires_at?: string;
  audit_completed_at?: string;
  cooling_off_seconds?: string;
  created_at_block?: string;
  expires_at_block?: string;
  audit_completed_block?: string;
}

export interface ProtocolStats {
  total_orders: number;
  total_bio_locked: string;
  total_orders_settled: number;
  owner?: string;
  biosecurity_reserve?: string;
}

/**
 * Get GenLayer client configured with Studionet
 */
export function getGenLayerClient(accountAddress?: string) {
  const config: any = {
    chain: studionet,
    endpoint: STUDIONET_RPC_URL,
  };

  if (typeof window !== 'undefined' && (window as any).ethereum && accountAddress) {
    config.provider = (window as any).ethereum;
    config.account = accountAddress as `0x${string}`;
  }

  return createClient(config);
}

/**
 * Switch or add GenLayer Studionet chain in MetaMask (Chain ID: 61999)
 */
export async function ensureStudionet(): Promise<boolean> {
  if (typeof window === 'undefined' || !(window as any).ethereum) {
    throw new Error('MetaMask is not installed. Please install MetaMask to use AgentBio.');
  }

  const ethereum = (window as any).ethereum;

  try {
    await ethereum.request({
      method: 'wallet_switchEthereumChain',
      params: [{ chainId: STUDIONET_CHAIN_ID_HEX }],
    });
    return true;
  } catch (switchError: any) {
    if (
      switchError.code === 4902 ||
      switchError?.data?.originalError?.code === 4902 ||
      switchError?.message?.includes('Unrecognized chain') ||
      switchError?.message?.includes('wallet_addEthereumChain')
    ) {
      try {
        await ethereum.request({
          method: 'wallet_addEthereumChain',
          params: [
            {
              chainId: STUDIONET_CHAIN_ID_HEX,
              chainName: 'GenLayer Studionet',
              nativeCurrency: {
                name: 'GEN',
                symbol: 'GEN',
                decimals: 18,
              },
              rpcUrls: [STUDIONET_RPC_URL],
              blockExplorerUrls: ['https://genlayer-explorer.vercel.app'],
            },
          ],
        });
        return true;
      } catch (addError) {
        console.error('Failed to add Studionet chain to MetaMask:', addError);
        throw addError;
      }
    }
    console.error('Failed to switch to Studionet chain:', switchError);
    throw switchError;
  }
}

/**
 * Fetch aggregated protocol statistics
 */
export async function fetchStats(contractAddress: string): Promise<ProtocolStats> {
  if (!contractAddress || contractAddress === '0x0000000000000000000000000000000000000000') {
    return {
      total_orders: 0,
      total_bio_locked: '0',
      total_orders_settled: 0,
      biosecurity_reserve: '0x0000000000000000000000000000000000000000',
    };
  }

  try {
    const client = getGenLayerClient();
    const raw = await client.readContract({
      address: contractAddress as `0x${string}`,
      functionName: 'get_stats',
      args: [],
    });

    if (typeof raw === 'string') {
      return JSON.parse(raw);
    }
    return raw as unknown as ProtocolStats;
  } catch (err) {
    console.warn('fetchStats error:', err);
    return {
      total_orders: 0,
      total_bio_locked: '0',
      total_orders_settled: 0,
    };
  }
}

/**
 * Fetch all registered bio synthesis orders
 */
export async function fetchAllOrders(contractAddress: string): Promise<BioOrderData[]> {
  if (!contractAddress || contractAddress === '0x0000000000000000000000000000000000000000') {
    return [];
  }

  const client = getGenLayerClient();

  // 1. Fast path: get_all_orders
  try {
    const rawAll = await client.readContract({
      address: contractAddress as `0x${string}`,
      functionName: 'get_all_orders',
      args: [],
    });
    if (rawAll) {
      const parsed: BioOrderData[] = typeof rawAll === 'string' ? JSON.parse(rawAll) : rawAll;
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed;
      }
    }
  } catch (e) {
    // fallback to paginated
  }

  // 2. Secondary path: get_orders_paginated
  try {
    const rawPaginated = await client.readContract({
      address: contractAddress as `0x${string}`,
      functionName: 'get_orders_paginated',
      args: [0, 100],
    });
    if (rawPaginated) {
      const parsed: BioOrderData[] = typeof rawPaginated === 'string' ? JSON.parse(rawPaginated) : rawPaginated;
      if (Array.isArray(parsed)) {
        return parsed;
      }
    }
  } catch (e) {
    // fallback to sequential
  }

  // 3. Fallback: get_order_count + get_order_id_by_index + get_order
  try {
    const countRaw = await client.readContract({
      address: contractAddress as `0x${string}`,
      functionName: 'get_order_count',
      args: [],
    });

    const count = Number(countRaw);
    if (isNaN(count) || count <= 0) return [];

    const orders: BioOrderData[] = [];
    for (let i = 0; i < count; i++) {
      try {
        const oid = (await client.readContract({
          address: contractAddress as `0x${string}`,
          functionName: 'get_order_id_by_index',
          args: [i],
        })) as any;

        if (oid !== undefined) {
          const rawOrder = await client.readContract({
            address: contractAddress as `0x${string}`,
            functionName: 'get_order',
            args: [Number(oid)],
          });
          const parsed: BioOrderData = typeof rawOrder === 'string' ? JSON.parse(rawOrder) : rawOrder;
          orders.push(parsed);
        }
      } catch (err) {
        console.error(`Error reading order index ${i}:`, err);
      }
    }
    return orders;
  } catch (err) {
    console.warn('fetchAllOrders fallback error:', err);
    return [];
  }
}

/**
 * Bio-Researcher locks GEN synthesis payment and submits DNA design specification
 */
export async function orderSynthesisOnChain(
  contractAddress: string,
  userAddress: string,
  targetProteinFunction: string,
  sequenceSpecUrl: string,
  durationBlocks: number,
  depositWei: bigint
): Promise<string> {
  await ensureStudionet();
  const client = getGenLayerClient(userAddress);

  const txHash = await client.writeContract({
    address: contractAddress as `0x${string}`,
    functionName: 'order_synthesis',
    args: [targetProteinFunction.trim(), sequenceSpecUrl.trim(), durationBlocks],
    value: depositWei,
  });

  await client.waitForTransactionReceipt({ hash: txHash });
  return txHash;
}

/**
 * DNA Foundry claims order and submits sequencing QC report URL
 */
export async function submitSynthesisProofOnChain(
  contractAddress: string,
  userAddress: string,
  orderId: number,
  qcReportUrl: string
): Promise<string> {
  await ensureStudionet();
  const client = getGenLayerClient(userAddress);

  const txHash = await (client.writeContract as any)({
    address: contractAddress as `0x${string}`,
    functionName: 'submit_synthesis_proof',
    args: [orderId, qcReportUrl.trim()],
    value: 0n,
  });

  await client.waitForTransactionReceipt({ hash: txHash });
  return txHash;
}

/**
 * Convene AI Biosecurity Jury and trigger subjective consensus adjudication
 */
export async function adjudicateBiosecurityOnChain(
  contractAddress: string,
  userAddress: string,
  orderId: number
): Promise<string> {
  await ensureStudionet();
  const client = getGenLayerClient(userAddress);

  const txHash = await (client.writeContract as any)({
    address: contractAddress as `0x${string}`,
    functionName: 'adjudicate_biosecurity_and_qc',
    args: [orderId],
    value: 0n,
  });

  await client.waitForTransactionReceipt({ hash: txHash });
  return txHash;
}

/**
 * Appeal verdict during 24-block cooling-off window with 10% bond
 */
export async function appealVerdictOnChain(
  contractAddress: string,
  userAddress: string,
  orderId: number,
  disputeReason: string,
  bondWei: bigint
): Promise<string> {
  await ensureStudionet();
  const client = getGenLayerClient(userAddress);

  const txHash = await (client.writeContract as any)({
    address: contractAddress as `0x${string}`,
    functionName: 'appeal_verdict',
    args: [orderId, disputeReason.trim()],
    value: bondWei,
  });

  await client.waitForTransactionReceipt({ hash: txHash });
  return txHash;
}

/**
 * High Appellate Bio-Jury re-evaluates the contested order and settles funds cleanly
 */
export async function adjudicateAppealOnChain(
  contractAddress: string,
  userAddress: string,
  orderId: number,
  supplementalQcUrl: string
): Promise<string> {
  await ensureStudionet();
  const client = getGenLayerClient(userAddress);

  const txHash = await (client.writeContract as any)({
    address: contractAddress as `0x${string}`,
    functionName: 'adjudicate_appeal',
    args: [orderId, supplementalQcUrl.trim()],
    value: 0n,
  });

  await client.waitForTransactionReceipt({ hash: txHash });
  return txHash;
}

/**
 * Finalize settlement after cooling-off window elapses uncontested
 */
export async function finalizeSettlementOnChain(
  contractAddress: string,
  userAddress: string,
  orderId: number
): Promise<string> {
  await ensureStudionet();
  const client = getGenLayerClient(userAddress);

  const txHash = await (client.writeContract as any)({
    address: contractAddress as `0x${string}`,
    functionName: 'finalize_settlement',
    args: [orderId],
    value: 0n,
  });

  await client.waitForTransactionReceipt({ hash: txHash });
  return txHash;
}

/**
 * Reclaim expired or stalled order
 */
export async function cancelOrReclaimOnChain(
  contractAddress: string,
  userAddress: string,
  orderId: number
): Promise<string> {
  await ensureStudionet();
  const client = getGenLayerClient(userAddress);

  const txHash = await (client.writeContract as any)({
    address: contractAddress as `0x${string}`,
    functionName: 'cancel_or_reclaim',
    args: [orderId],
    value: 0n,
  });

  await client.waitForTransactionReceipt({ hash: txHash });
  return txHash;
}
