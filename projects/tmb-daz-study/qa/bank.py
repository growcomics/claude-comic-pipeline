#!/usr/bin/env python3
"""LAYER 5: the ONLY way picks enter the ledger/pages-log. REFUSES to record
anything lacking the full chain: compose receipt + audit-pass marker (hash
match) + post-flight verdict file with pass=true. Unbanked work is invisible
to every downstream step (refs must come from the ledger), so a skipped layer
cannot propagate.

  python3 qa/bank.py --job sheet:deedee-t8-destroya --flow-id <uuid> --disk references/characters/dee-dee/turnaround-t8.png
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import integrity; integrity.verify_or_die()  # LAYER 8

def refuse(m):
    print(f"BANK REFUSED: {m}")
    sys.exit(1)

a = argparse.ArgumentParser()
a.add_argument("--job", required=True)
a.add_argument("--flow-id", required=True)
a.add_argument("--disk", required=True)
a.add_argument("--ledger-key", default=None, help="characters.<id>.<key> path for sheets")
args = a.parse_args()

stem = f"qa/receipts/{args.job.replace(':','_')}"
rpath, apath, vpath = stem + ".receipt.json", stem + ".audit-pass", stem + ".verdict.json"

if not os.path.exists(rpath): refuse(f"no compose receipt ({rpath}) — Layer 0 skipped")
if not os.path.exists(apath): refuse(f"no audit-pass marker ({apath}) — Layer 2 skipped")
rec = json.load(open(rpath))
if open(apath).read().strip() != rec["prompt_sha"]: refuse("audit marker hash mismatch — stale audit")
if not os.path.exists(vpath): refuse(f"no post-flight verdict ({vpath}) — Layer 4 skipped (fresh-context subagent must judge the result first)")
verdict = json.load(open(vpath))
if not verdict.get("pass"): refuse(f"post-flight verdict is FAIL: {verdict.get('tags', [])} — re-roll, don't bank")
if not os.path.exists(args.disk): refuse(f"pick not downloaded to {args.disk}")

led = json.load(open("references/ref-ledger.json"))
chain = {"flow_id": args.flow_id, "disk": args.disk,
         "chain": {"receipt": rpath, "audit": apath, "verdict": vpath,
                   "verdict_tags": verdict.get("tags", []), "prompt_sha": rec["prompt_sha"]}}
kind, _, ident = args.job.partition(":")
if kind == "sheet":
    if not args.ledger_key: refuse("--ledger-key required for sheets (e.g. dee-dee.turnaround_t8)")
    char, _, key = args.ledger_key.partition(".")
    led["characters"].setdefault(char, {})[key] = chain
    json.dump(led, open("references/ref-ledger.json", "w"), indent=2)
else:
    log = json.load(open("pages-log.json"))
    log["done"][ident] = chain
    if ident in log.get("pending", []): log["pending"].remove(ident)
    json.dump(log, open("pages-log.json", "w"), indent=2)
print(f"BANKED {args.job} -> {args.disk}  (full chain verified)")
