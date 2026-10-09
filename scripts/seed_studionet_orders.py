import os
import sys
import json
import time
from genlayer_py import create_client, create_account, studionet

PK = "0x1b807b1df022a40f872596b11565e6b6856547dc66996bd3d5a85b376ea3a0ef"
CONTRACT = "0x7bb63F04827cf531A1efe99205d4EbEDD88eB2cA"

def main():
    print("=" * 70, flush=True)
    print("  SEEDING REAL ON-CHAIN ORDERS ON STUDIONET  ", flush=True)
    print("=" * 70, flush=True)

    acct = create_account(PK)
    client = create_client(chain=studionet, account=acct)

    print(f"[+] Account: {acct.address}", flush=True)
    bal = client.get_balance(acct.address)
    print(f"[+] Balance: {bal / 1e18} GEN", flush=True)

    # 1. Order 1
    print("\n[*] Creating Order 1: CRISPR-Cas9 Precision gRNA...", flush=True)
    tx1 = client.write_contract(
        address=CONTRACT,
        function_name="order_synthesis",
        value=int(0.1 * 1e18),
        args=[
            "High-fidelity CRISPR-Cas9 ribonucleoprotein guide RNA targeting BCL11A erythroid enhancer for sickle cell therapy",
            "https://raw.githubusercontent.com/tuannguyenvan95/AgentBio/main/data/cas9_bcl11a.fasta",
            86400 * 7
        ]
    )
    print(f"[+] Tx1 submitted: {tx1}", flush=True)
    client.wait_for_transaction_receipt(tx1)
    print("[+] Tx1 confirmed!", flush=True)

    # 2. Order 2
    print("\n[*] Creating Order 2: Monoclonal Antibody Anti-IL6...", flush=True)
    tx2 = client.write_contract(
        address=CONTRACT,
        function_name="order_synthesis",
        value=int(0.15 * 1e18),
        args=[
            "Monoclonal antibody IgG1 heavy chain targeting IL-6 cytokine receptor for cytokine storm suppression in ARDS",
            "https://raw.githubusercontent.com/tuannguyenvan95/AgentBio/main/data/anti_il6_receptor.fasta",
            86400 * 7
        ]
    )
    print(f"[+] Tx2 submitted: {tx2}", flush=True)
    client.wait_for_transaction_receipt(tx2)
    print("[+] Tx2 confirmed!", flush=True)

    # 3. Check stats
    stats = client.read_contract(address=CONTRACT, function_name="get_stats", args=[])
    print(f"\n[+] Protocol Stats after orders: {stats}", flush=True)
    orders = client.read_contract(address=CONTRACT, function_name="get_all_orders", args=[])
    print(f"[+] All Orders: {orders}", flush=True)

if __name__ == "__main__":
    main()
