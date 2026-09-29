import os
import sys
import json
import time
from genlayer_py import create_client, create_account, studionet

PK = "0x1b807b1df022a40f872596b11565e6b6856547dc66996bd3d5a85b376ea3a0ef"
CONTRACT = "0xD89bF46b5Ac5f096288647EB8FcaE12F6C7B7f16"


def main():
    print("=" * 70, flush=True)
    print("  LIVE AGENTBIO BIOSECURITY & QC AUDIT TEST ON GENLAYER STUDIONET  ", flush=True)
    print("=" * 70, flush=True)

    try:
        acct = create_account(PK)
        client = create_client(chain=studionet, account=acct)

        print(f"[+] Foundry / Operator Address : {acct.address}", flush=True)
        bal = client.get_balance(acct.address)
        print(f"[+] Operator Current Balance   : {bal / 1e18} GEN", flush=True)
        print(f"[+] Target Contract            : {CONTRACT}", flush=True)

        # 1. Read Stats
        raw_stats = client.read_contract(address=CONTRACT, function_name="get_stats", args=[])
        stats = json.loads(raw_stats) if isinstance(raw_stats, str) else raw_stats
        print(f"[+] Protocol Stats: {stats}", flush=True)

        # 2. Read Count
        count = int(client.read_contract(address=CONTRACT, function_name="get_order_count", args=[]))
        print(f"[+] Total Orders Registered: {count}", flush=True)

    except Exception as e:
        print(f"[!] Studionet connection or call status: {e}", flush=True)


if __name__ == "__main__":
    main()
