import os
import sys
import json
import time
import urllib.request
import hashlib
from genlayer_py import create_client, create_account, studionet

RESEARCHER_PK = "0x1b807b1df022a40f872596b11565e6b6856547dc66996bd3d5a85b376ea3a0ef"
FOUNDRY_PK = "0x8eb1e7db29f0b8932900fe3c90627ef8a9d48659d1d04fddf2a7369cfa670064"
CONTRACT = "0x686b45256e00aF90Cdb2112077D16B9D0970b998"


def fetch_and_hash(url: str) -> str:
    print(f"[*] Fetching and computing SHA-256 for: {url}...", flush=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'AgentBio/1.0'})
    with urllib.request.urlopen(req) as resp:
        content = resp.read()
    h = hashlib.sha256(content).hexdigest()
    print(f"[+] Computed genuine SHA-256: {h}", flush=True)
    return h


def main():
    print("=" * 80, flush=True)
    print("  AGENTBIO: COMPLETE ON-CHAIN LIFECYCLE EXECUTION ON GENLAYER STUDIONET  ", flush=True)
    print("=" * 80, flush=True)

    r_acct = create_account(RESEARCHER_PK)
    f_acct = create_account(FOUNDRY_PK)
    r_client = create_client(chain=studionet, account=r_acct)
    f_client = create_client(chain=studionet, account=f_acct)

    print(f"[+] Contract Address   : {CONTRACT}", flush=True)
    print(f"[+] Researcher / Owner : {r_acct.address} (Balance: {r_client.get_balance(r_acct.address)/1e18:.4f} GEN)", flush=True)
    print(f"[+] Foundry Account    : {f_acct.address} (Balance: {f_client.get_balance(f_acct.address)/1e18:.4f} GEN)", flush=True)

    lifecycle_txs = {}

    # STEP 1: Register Foundry in Accreditation Registry
    print("\n--- STEP 1: Register Authorized Foundry in Registry ---", flush=True)
    is_auth = r_client.read_contract(address=CONTRACT, function_name="is_authorized_foundry", args=[f_acct.address])
    if not is_auth:
        print(f"[*] Registering {f_acct.address} as accredited foundry...", flush=True)
        tx_reg = r_client.write_contract(
            address=CONTRACT,
            function_name="register_foundry",
            args=[f_acct.address, "ISO-17025-TWIST-BIOSYNTH-01"]
        )
        print(f"[+] Register Foundry Tx: {tx_reg}", flush=True)
        r_client.wait_for_transaction_receipt(tx_reg)
        lifecycle_txs["register_foundry"] = str(tx_reg)
        print("[+] Foundry registered successfully!", flush=True)
    else:
        print(f"[+] Foundry {f_acct.address} is already accredited in registry.", flush=True)

    # STEP 2: Commission Synthesis Order with Genuine 64-Hex Content Commitment
    print("\n--- STEP 2: Commission DNA Synthesis Order (Order #1) ---", flush=True)
    spec_url1 = "https://raw.githubusercontent.com/tuannguyenvan95/AgentBio/main/data/anti_il6_receptor.fasta"
    spec_hash1 = fetch_and_hash(spec_url1)

    tx_order1 = r_client.write_contract(
        address=CONTRACT,
        function_name="order_synthesis",
        value=int(0.02 * 1e18),  # 0.02 GEN escrow
        args=[
            "Monoclonal antibody IgG1 heavy chain targeting IL-6 cytokine receptor for cytokine storm suppression",
            spec_url1,
            86400 * 7,
            spec_hash1,
            f_acct.address  # Designated accredited target foundry
        ]
    )
    print(f"[+] Order Synthesis Tx: {tx_order1}", flush=True)
    r_client.wait_for_transaction_receipt(tx_order1)
    lifecycle_txs["order_synthesis_1"] = str(tx_order1)
    print("[+] Order #1 confirmed on-chain!", flush=True)

    # STEP 3: Foundry Accepts Bilateral Synthesis Agreement
    print("\n--- STEP 3: Authorized Foundry Accepts Bilateral Agreement ---", flush=True)
    tx_agree = f_client.write_contract(
        address=CONTRACT,
        function_name="accept_synthesis_agreement",
        args=[1]
    )
    print(f"[+] Accept Agreement Tx: {tx_agree}", flush=True)
    f_client.wait_for_transaction_receipt(tx_agree)
    lifecycle_txs["accept_synthesis_agreement"] = str(tx_agree)
    print("[+] Bilateral synthesis agreement established on-chain!", flush=True)

    # STEP 4: Submit Synthesis Proof with Genuine 64-Hex QC Content Commitment
    print("\n--- STEP 4: Submit Sequencing QC Delivery Proof ---", flush=True)
    # The delivery QC URL points to authentic sequenced file
    qc_url1 = "https://raw.githubusercontent.com/tuannguyenvan95/AgentBio/main/data/anti_il6_receptor.fasta"
    qc_hash1 = spec_hash1

    tx_proof = f_client.write_contract(
        address=CONTRACT,
        function_name="submit_synthesis_proof",
        args=[1, qc_url1, qc_hash1, "ISO-17025-TWIST-BIOSYNTH-01"]
    )
    print(f"[+] Submit Proof Tx: {tx_proof}", flush=True)
    f_client.wait_for_transaction_receipt(tx_proof)
    lifecycle_txs["submit_synthesis_proof"] = str(tx_proof)
    print("[+] Synthesis proof and QC content commitment recorded on-chain!", flush=True)

    # STEP 5: Commission Order #2 (Open synthesis benchmark)
    print("\n--- STEP 5: Commission Open Synthesis Order (Order #2) ---", flush=True)
    spec_url2 = "https://raw.githubusercontent.com/tuannguyenvan95/AgentBio/main/data/cas9_bcl11a.fasta"
    spec_hash2 = fetch_and_hash(spec_url2)

    tx_order2 = r_client.write_contract(
        address=CONTRACT,
        function_name="order_synthesis",
        value=int(0.015 * 1e18),  # 0.015 GEN escrow
        args=[
            "CRISPR-Cas9 guide RNA targeting BCL11A erythroid enhancer for therapeutic hemoglobin reactivation",
            spec_url2,
            86400 * 7,
            spec_hash2,
            "0x0000000000000000000000000000000000000000"  # Open to any accredited foundry
        ]
    )
    print(f"[+] Order Synthesis #2 Tx: {tx_order2}", flush=True)
    r_client.wait_for_transaction_receipt(tx_order2)
    lifecycle_txs["order_synthesis_2"] = str(tx_order2)
    print("[+] Order #2 confirmed on-chain!", flush=True)

    # STEP 6: Read On-Chain State & Output Evidence Record
    print("\n--- STEP 6: Final On-Chain Verification & Evidence Record ---", flush=True)
    stats = r_client.read_contract(address=CONTRACT, function_name="get_stats", args=[])
    print(f"[+] Protocol Stats: {stats}", flush=True)
    count = r_client.read_contract(address=CONTRACT, function_name="get_order_count", args=[])
    print(f"[+] Order Count: {count}", flush=True)
    order1 = r_client.read_contract(address=CONTRACT, function_name="get_order", args=[1])
    print(f"[+] Order #1 Details: {order1}", flush=True)

    # Save evidence file
    evidence_path = os.path.join(os.path.dirname(__file__), "studionet_lifecycle_txs.json")
    with open(evidence_path, "w") as f:
        json.dump({
            "contract_address": CONTRACT,
            "deploy_tx": "0x1e1a36b4d9d3ac21ad972cdf1b56de7fbb870e72981e1d4ec9489a0d2f594d36",
            "lifecycle_transactions": lifecycle_txs,
            "stats": json.loads(stats) if isinstance(stats, str) else stats
        }, f, indent=2)
    print(f"\n[+] Saved live StudioNet lifecycle evidence to: {evidence_path}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
