#!/usr/bin/env python3
"""LAYER 8: gate-integrity self-verification. Every protocol script calls
verify_or_die() before doing ANYTHING. If any guarded script's hash deviates
from the blessed MANIFEST.sha256, ALL gates lock simultaneously.

Re-blessing the manifest is a USER-ONLY act (CLAUDE.md protocol): review the
`git diff` on qa/ first, then:

  python3 qa/integrity.py --rebless --i-am-the-user

Standalone check:  python3 qa/integrity.py
"""
import hashlib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GUARDED = ["integrity.py", "compose.py", "audit_prompt.py", "bank.py",
           "verify_chain.py", "preflight.py"]

def _hash(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()

def manifest_fingerprint():
    man = os.path.join(HERE, "MANIFEST.sha256")
    return _hash(man)[:16] if os.path.exists(man) else "NO-MANIFEST"

def verify_or_die():
    man = os.path.join(HERE, "MANIFEST.sha256")
    if not os.path.exists(man):
        print("GATE INTEGRITY FAILURE: qa/MANIFEST.sha256 missing — ALL GATES LOCKED.")
        sys.exit(2)
    want = {}
    for line in open(man):
        h, _, name = line.strip().partition("  ")
        if name: want[name] = h
    bad = []
    for name in GUARDED:
        p = os.path.join(HERE, name)
        if not os.path.exists(p):
            bad.append(f"{name}: MISSING"); continue
        if want.get(name) != _hash(p):
            bad.append(f"{name}: hash mismatch vs blessed manifest")
    if set(want) != set(GUARDED):
        bad.append("manifest file-list mismatch")
    if bad:
        print("GATE INTEGRITY FAILURE — protocol scripts changed since the user-blessed manifest:")
        for b in bad: print(f"  ✗ {b}")
        print("ALL GATES LOCKED. Review `git diff` on qa/, then ONLY THE USER may run:")
        print("  python3 qa/integrity.py --rebless --i-am-the-user")
        sys.exit(2)

def rebless():
    man = os.path.join(HERE, "MANIFEST.sha256")
    with open(man, "w") as f:
        for name in GUARDED:
            f.write(f"{_hash(os.path.join(HERE, name))}  {name}\n")
    print("manifest re-blessed — commit it so the change is visible in git history")

if __name__ == "__main__":
    if "--rebless" in sys.argv:
        if "--i-am-the-user" not in sys.argv:
            print("rebless requires --i-am-the-user (Claude is prohibited from re-blessing; see CLAUDE.md protocol)")
            sys.exit(2)
        rebless()
    else:
        verify_or_die()
        print(f"gates intact ✓  (manifest fingerprint {manifest_fingerprint()})")
