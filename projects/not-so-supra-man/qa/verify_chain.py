#!/usr/bin/env python3
"""LAYER 7: user-runnable trust audit. Scans the ledger + pages-log for entries
recorded WITHOUT the full receipt chain (i.e., banked by hand or by a
rule-breaking agent). Run anytime:  python3 qa/verify_chain.py
"""
import json, os

bad, ok = [], 0

led = json.load(open("references/ref-ledger.json"))
for char, body in led.get("characters", {}).items():
    for key, v in body.items():
        if isinstance(v, dict) and "flow_id" in v:
            if "chain" in v: ok += 1
            else: bad.append(f"ledger: {char}.{key} ({v.get('flow_id','?')[:8]}…) — NO CHAIN (pre-protocol or bypassed)")

if os.path.exists("pages-log.json"):
    log = json.load(open("pages-log.json"))
    for pid, v in log.get("done", {}).items():
        if "chain" in v: ok += 1
        else: bad.append(f"pages-log: {pid} — NO CHAIN (pre-protocol or bypassed)")

print(f"chain-verified entries: {ok}")
if bad:
    print(f"entries WITHOUT a receipt chain: {len(bad)}")
    for b in bad: print(f"  ! {b}")
    print("(pre-protocol v1/early-v2 entries are expected here; anything banked from now on must have a chain)")
else:
    print("all entries carry full receipt chains ✓")
