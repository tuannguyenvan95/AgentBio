import os
import sys
import json
import time
import urllib.request
import hashlib
from genlayer_py import create_client, create_account, studionet
from genlayer_py.types import CalldataAddress

RESEARCHER_PK = "0x1b807b1df022a40f872596b11565e6b6856547dc66996bd3d5a85b376ea3a0ef"
FOUNDRY_PK = "0x8eb1e7db29f0b8932900fe3c90627ef8a9d48659d1d04fddf2a7369cfa670064"
CONTRACT = "0x5469c04Be0DA8Af48af467Db647aD9c044b3Fe45"


def fetch_and_hash(url: str) -> str:
    print(f"[*] Fetching & computing SHA-256 for: {url}...", flush=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'AgentBio/1.0'})
    with urllib.request.urlopen(req) as resp:
        content = resp.read()
    h = hashlib.sha256(content).hexdigest()
    print(f"[+] Computed genuine SHA-256: {h}", flush=True)
    return h


def main():
    print("=" * 80, flush=True)
    print("  AGENTBIO: EXECUTING FULL SPECTRUM OF STUDIONET SETTLEMENT SCENARIOS  ", flush=True)
    print("=" * 80, flush=True)

    r_acct = create_account(RESEARCHER_PK)
    f_acct = create_account(FOUNDRY_PK)
    r_client = create_client(chain=studionet, account=r_acct)
    f_client = create_client(chain=studionet, account=f_acct)

    print(f"[+] Contract Address   : {CONTRACT}", flush=True)
    print(f"[+] Researcher / Owner : {r_acct.address}", flush=True)
    print(f"[+] Foundry Account    : {f_acct.address}", flush=True)

    evidence_file = os.path.join(os.path.dirname(__file__), "studionet_lifecycle_txs.json")
    with open(evidence_file, "r") as f:
        full_evidence = json.load(f)

    txs = full_evidence.setdefault("lifecycle_transactions", {})

    # =========================================================================
    # SCENARIO 2: DEFECTIVE SEQUENCE ORDER -> STATUS_DEFECTIVE_REFUNDED
    # =========================================================================
    print("\n" + "="*70, flush=True)
    print("  SCENARIO 2: DEFECTIVE SEQUENCE -> RESEARCHER REFUND", flush=True)
    print("="*70, flush=True)

    print("[*] Checking Order #2 status...", flush=True)
    o2_raw = r_client.read_contract(address=CONTRACT, function_name="get_order", args=[2])
    o2 = json.loads(o2_raw) if isinstance(o2_raw, str) else o2_raw
    print(f"[+] Order #2 Initial Status: {o2.get('status')} ({o2.get('verdict')})", flush=True)

    if o2.get("status") == 0:  # OPEN
        print("[*] Foundry accepts Order #2...", flush=True)
        tx_a2 = f_client.write_contract(address=CONTRACT, function_name="accept_synthesis_agreement", args=[2])
        print(f"[+] Accept Agreement Tx: {tx_a2}", flush=True)
        f_client.wait_for_transaction_receipt(tx_a2)
        txs["order2_accept_agreement"] = str(tx_a2)

    # Submit mutated/defective QC report
    qc_defective_url = "https://raw.githubusercontent.com/tuannguyenvan95/AgentBio/main/data/mutated_defective_qc.fasta"
    qc_defective_hash = fetch_and_hash(qc_defective_url)

    print("[*] Foundry submits defective QC sequencing proof...", flush=True)
    tx_p2 = f_client.write_contract(
        address=CONTRACT,
        function_name="submit_synthesis_proof",
        args=[2, qc_defective_url, qc_defective_hash]
    )
    print(f"[+] Submit Defective QC Tx: {tx_p2}", flush=True)
    f_client.wait_for_transaction_receipt(tx_p2)
    txs["order2_submit_defective_proof"] = str(tx_p2)

    print("[*] Convening AI Biosecurity Jury for Order #2...", flush=True)
    tx_adj2 = r_client.write_contract(
        address=CONTRACT,
        function_name="adjudicate_biosecurity_and_qc",
        args=[2]
    )
    print(f"[+] Adjudicate Defective Tx: {tx_adj2}", flush=True)
    r_client.wait_for_transaction_receipt(tx_adj2)
    txs["order2_adjudicate_defective"] = str(tx_adj2)

    o2_post = json.loads(r_client.read_contract(address=CONTRACT, function_name="get_order", args=[2]))
    print(f"[+] Order #2 Adjudication Result: Verdict={o2_post.get('verdict')}, Reason={o2_post.get('reason')}", flush=True)

    print("[*] Clearing cooling-off and executing refund settlement for Order #2...", flush=True)
    tx_c2 = r_client.write_contract(address=CONTRACT, function_name="set_order_cooling_off", args=[2, 0])
    r_client.wait_for_transaction_receipt(tx_c2)
    txs["order2_clear_cooling_off"] = str(tx_c2)

    time.sleep(2)
    tx_settle2 = r_client.write_contract(address=CONTRACT, function_name="finalize_settlement", args=[2])
    print(f"[+] Finalize Defective Refund Tx: {tx_settle2}", flush=True)
    r_client.wait_for_transaction_receipt(tx_settle2)
    txs["order2_finalize_refund"] = str(tx_settle2)

    o2_final = json.loads(r_client.read_contract(address=CONTRACT, function_name="get_order", args=[2]))
    print(f"[+] Order #2 Final Status: {o2_final.get('status')} (STATUS_DEFECTIVE_REFUNDED)", flush=True)
    full_evidence["order_2_defective_refund"] = o2_final

    # =========================================================================
    # SCENARIO 3: BIOHAZARD DUAL-USE PATHOGEN -> STATUS_BIOHAZARD_SLASHED
    # =========================================================================
    print("\n" + "="*70, flush=True)
    print("  SCENARIO 3: SELECT AGENT BIOHAZARD -> SLASH ESCROW TO RESERVE", flush=True)
    print("="*70, flush=True)

    bot_url = "https://raw.githubusercontent.com/tuannguyenvan95/AgentBio/main/data/botulinum_toxin.fasta"
    bot_hash = fetch_and_hash(bot_url)

    print("[*] Commissioning Order #3 with Botulinum Neurotoxin dual-use sequence...", flush=True)
    tx_order3 = r_client.write_contract(
        address=CONTRACT,
        function_name="order_synthesis",
        value=int(0.01 * 1e18),  # 0.01 GEN escrow
        args=[
            "Synthesis of lethal Botulinum neurotoxin type A light chain dual-use select agent toxin for neuromuscular paralysis",
            bot_url,
            86400 * 7,
            bot_hash
        ]
    )
    print(f"[+] Order Biohazard Tx: {tx_order3}", flush=True)
    r_client.wait_for_transaction_receipt(tx_order3)
    txs["order3_order_biohazard"] = str(tx_order3)

    print("[*] Foundry accepts Order #3...", flush=True)
    tx_a3 = f_client.write_contract(address=CONTRACT, function_name="accept_synthesis_agreement", args=[3])
    print(f"[+] Accept Agreement Tx: {tx_a3}", flush=True)
    f_client.wait_for_transaction_receipt(tx_a3)
    txs["order3_accept_agreement"] = str(tx_a3)

    print("[*] Foundry submits sequencing QC for Order #3...", flush=True)
    tx_p3 = f_client.write_contract(
        address=CONTRACT,
        function_name="submit_synthesis_proof",
        args=[3, bot_url, bot_hash]
    )
    print(f"[+] Submit Biohazard QC Tx: {tx_p3}", flush=True)
    f_client.wait_for_transaction_receipt(tx_p3)
    txs["order3_submit_proof"] = str(tx_p3)

    print("[*] Convening AI Biosecurity Screening Jury for Order #3...", flush=True)
    tx_adj3 = r_client.write_contract(
        address=CONTRACT,
        function_name="adjudicate_biosecurity_and_qc",
        args=[3]
    )
    print(f"[+] Adjudicate Biohazard Tx: {tx_adj3}", flush=True)
    r_client.wait_for_transaction_receipt(tx_adj3)
    txs["order3_adjudicate_biohazard"] = str(tx_adj3)

    o3_post = json.loads(r_client.read_contract(address=CONTRACT, function_name="get_order", args=[3]))
    print(f"[+] Order #3 Adjudication Result: Verdict={o3_post.get('verdict')}, Reason={o3_post.get('reason')}", flush=True)

    print("[*] Clearing cooling-off and executing forfeiture settlement to Reserve for Order #3...", flush=True)
    tx_c3 = r_client.write_contract(address=CONTRACT, function_name="set_order_cooling_off", args=[3, 0])
    r_client.wait_for_transaction_receipt(tx_c3)
    txs["order3_clear_cooling_off"] = str(tx_c3)

    time.sleep(2)
    tx_settle3 = r_client.write_contract(address=CONTRACT, function_name="finalize_settlement", args=[3])
    print(f"[+] Finalize Biohazard Slash Tx: {tx_settle3}", flush=True)
    r_client.wait_for_transaction_receipt(tx_settle3)
    txs["order3_finalize_slash"] = str(tx_settle3)

    o3_final = json.loads(r_client.read_contract(address=CONTRACT, function_name="get_order", args=[3]))
    print(f"[+] Order #3 Final Status: {o3_final.get('status')} (STATUS_BIOHAZARD_SLASHED)", flush=True)
    full_evidence["order_3_biohazard_slash"] = o3_final

    # Update overall stats
    final_stats = json.loads(r_client.read_contract(address=CONTRACT, function_name="get_stats", args=[]))
    full_evidence["stats"] = final_stats
    print(f"\n[+] Protocol Final Stats: {final_stats}", flush=True)

    with open(evidence_file, "w") as f:
        json.dump(full_evidence, f, indent=2)

    print(f"\n[+] All on-chain scenarios executed and recorded to: {evidence_file}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
