#!/usr/bin/env python3
"""Bakeoff lane orchestrator — anchor -> over-generate -> judge -> retry -> select.

Industrializes the owner's proven manual method (over-generate in Flow, favorite
winners, anchor with images) instead of the specify->generate-once->hope flow.
See runners/bakeoff/README.md for the beat contract and driver protocol.

Subcommands (each idempotent, state lives in <run>/state.json):
  plan     beatsheet.json -> run dir with resolved refs/anchors + round-1 jobsheet
  collect  scan variants/ for generated PNGs, mark jobsheet entries done
  judge    ingest variants to the board (accepted=0), stage-A qascan (registry
           IDs), stage-B picks-calibrated ranker over survivors
  retry    re-roll zero-clean beats with defect findings injected (max 2), then
           flag to the human-review queue
  select   land winners: accepted=true rating=good (+judge-pick tag), never
           overriding an owner-accepted panel in the same group
  stats    per-run yield metrics -> state, data/bakeoff-yield.json, bridge do=yield
  status   human-readable run summary

Generation itself is driver-executed (Higgsfield MCP session, Flow via Chrome,
or owner-manual) — the lane emits/consumes the jobsheet and never hard-codes a
backend. Stdlib-only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bridge_client import Bridge, BridgeError            # noqa: E402
import judge as judge_mod                                 # noqa: E402
import registry as reg                                    # noqa: E402

REPO = Path(__file__).resolve().parents[2]
RUNS_DIR = Path(__file__).resolve().parent / "runs"
YIELD_FILE = REPO / "data" / "bakeoff-yield.json"
MAX_RETRIES = 2

# Refs-are-truth lint: appearance prose belongs in reference images, not prompts.
APPEARANCE_TOKENS = [
    "blonde", "blond ", "brunette", "redhead", "red hair", "black hair", "brown hair",
    "blue eyes", "green eyes", "brown eyes", "hazel", "freckle", "wearing a",
    "dressed in", "outfit of", "her face is", "his face is", "skin tone",
]


def now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def log(state: dict, msg: str) -> None:
    state.setdefault("log", []).append({"ts": now(), "msg": msg})
    print(f"[{now()}] {msg}")


def load_state(run: Path) -> dict:
    return json.loads((run / "state.json").read_text())


def save_state(run: Path, state: dict) -> None:
    tmp = run / "state.json.tmp"
    tmp.write_text(json.dumps(state, indent=1))
    tmp.rename(run / "state.json")


def slot_path(run: Path, beat: str, rnd: int, n: int) -> Path:
    return run / "variants" / beat / f"r{rnd}v{n}.png"


# ---------------------------------------------------------------------------
# plan


def cmd_plan(args) -> None:
    sheet = json.loads(Path(args.sheet).read_text())
    pid = sheet["project"]
    run_id = args.run_id or "bo-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run = RUNS_DIR / run_id
    if run.exists():
        sys.exit(f"run dir exists: {run}")
    (run / "refs").mkdir(parents=True)
    (run / "variants").mkdir()

    br = Bridge()
    spec = br.genspec(pid)
    if not spec.get("locked"):
        print("WARNING: project refs are not locked — genspec refs may be empty.")
    refs_by_file = {r["file"]: r for r in spec.get("refs", [])}
    refs_by_char: dict[str, list] = {}
    for r in spec.get("refs", []):
        refs_by_char.setdefault((r.get("char") or "").lower(), []).append(r)

    state = {
        "runId": run_id, "project": pid, "backend": sheet.get("backend", "flow-chrome"),
        "createdAt": now(), "style": sheet.get("style", spec.get("style", "")),
        "beats": {}, "log": [],
    }
    jobsheet = []
    for b in sheet["beats"]:
        bid = b["id"]
        if not re.fullmatch(r"[a-z0-9_-]+", bid):
            sys.exit(f"beat id must be [a-z0-9_-]: {bid}")
        for tok in APPEARANCE_TOKENS:
            if tok in b["prompt"].lower():
                print(f"LINT {bid}: appearance prose {tok!r} in prompt — refs are "
                      "truth; move looks into reference images.")
        # resolve identity refs: by char name (locked refs via genspec) or file
        ref_files: list[dict] = []
        for ir in b.get("identityRefs", []):
            if ir.get("char"):
                pool = refs_by_char.get(ir["char"].lower(), [])
                pool = [r for r in pool if r.get("kind") in (ir.get("kinds") or ["face", "view", "body"])]
                ref_files.extend(pool[: ir.get("max", 2)])
            elif ir.get("file") and ir["file"] in refs_by_file:
                ref_files.append(refs_by_file[ir["file"]])
            elif ir.get("file"):
                ref_files.append({"file": ir["file"], "char": "", "kind": "ref", "label": ir.get("label", "")})
        # download anchors + refs locally so any driver can attach them
        local_anchors, local_refs = [], []
        for i, a in enumerate(b.get("anchors", [])):
            if a.get("local"):
                p = Path(a["local"]).expanduser()
                if not p.is_file():
                    sys.exit(f"{bid}: local anchor missing: {p}")
                local_anchors.append(str(p))
            else:
                f = a["board"] if a.get("board") else a["file"]
                dest = run / "refs" / f"{bid}-anchor{i}-{Path(f).name}"
                dest.write_bytes(br.img_bytes(pid, f))
                local_anchors.append(str(dest))
        for r in ref_files:
            dest = run / "refs" / f"ref-{Path(r['file']).name}"
            if not dest.exists():
                dest.write_bytes(br.img_bytes(pid, r["file"]))
            local_refs.append({"path": str(dest), "file": r["file"],
                               "char": r.get("char", ""), "kind": r.get("kind", ""),
                               "label": r.get("label", "")})
        n = int(b.get("variants", 4))
        state["beats"][bid] = {
            "prompt": b["prompt"], "kind": b.get("kind", "panel"),
            "aspect": b.get("aspect", "3:4"), "variants": n,
            "anchors": local_anchors, "refs": local_refs,
            "rounds": [{"round": 1, "prompt": b["prompt"], "injected": [],
                        "variants": []}],
            "status": "generating", "retries": 0, "winner": None,
        }
        (run / "variants" / bid).mkdir()
        jobsheet.append(_job_entry(state, bid, 1))
    (run / "jobsheet.json").write_text(json.dumps(jobsheet, indent=1))
    log(state, f"planned {len(sheet['beats'])} beats for project {pid} "
               f"(backend {state['backend']})")
    save_state(run, state)
    print(f"\nRun: {run}\nJobsheet: {run / 'jobsheet.json'}\n"
          f"Driver: generate each entry's variants to the listed 'out' paths, "
          f"then run: bakeoff.py collect --run {run}")


def _job_entry(state: dict, bid: str, rnd: int) -> dict:
    b = state["beats"][bid]
    round_rec = b["rounds"][rnd - 1]
    return {
        "beat": bid, "round": rnd, "prompt": round_rec["prompt"],
        "style": state.get("style", ""), "aspect": b["aspect"],
        "count": b["variants"], "anchors": b["anchors"],
        "refs": [r["path"] for r in b["refs"]],
        "out": [str(slot_path(RUNS_DIR / state["runId"], bid, rnd, n + 1))
                for n in range(b["variants"])],
        "done": False,
    }


# ---------------------------------------------------------------------------
# collect


def cmd_collect(args) -> None:
    run = Path(args.run)
    state = load_state(run)
    sheet_p = run / "jobsheet.json"
    jobsheet = json.loads(sheet_p.read_text())
    changed = 0
    for e in jobsheet:
        if e["done"]:
            continue
        have = [p for p in e["out"] if Path(p).is_file()]
        if len(have) >= max(1, e["count"] - int(args.tolerate_missing)):
            e["done"] = True
            e["have"] = have
            b = state["beats"][e["beat"]]
            b["rounds"][e["round"] - 1]["variants"] = [
                {"slot": Path(p).stem, "path": p} for p in sorted(have)]
            b["status"] = "judging"
            changed += 1
            log(state, f"{e['beat']} r{e['round']}: collected {len(have)}/{e['count']} variants")
    sheet_p.write_text(json.dumps(jobsheet, indent=1))
    save_state(run, state)
    print(f"collected {changed} jobsheet entries")


# ---------------------------------------------------------------------------
# judge


def cmd_judge(args) -> None:
    run = Path(args.run)
    state = load_state(run)
    br = Bridge()
    pid = state["project"]
    for bid, b in state["beats"].items():
        if b["status"] != "judging":
            continue
        rnd = len(b["rounds"])
        rec = b["rounds"][rnd - 1]
        # -- ingest to the board (accepted=0 defeats autoApprove) ------------
        parent = None
        if rnd > 1:  # keep retries in round-1's beat group (genkey inheritance)
            for v0 in b["rounds"][0]["variants"]:
                if v0.get("board"):
                    parent = v0["board"]
                    break
        ingested = False
        for i, v in enumerate(rec["variants"]):
            if v.get("board") or v.get("gen"):
                continue
            gen = f"{state['runId']}-{bid}-{v['slot']}"
            br.ingest(
                pid, Path(v["path"]), orig=f"{gen}.png", gen=gen,
                prompt=rec["prompt"], parent=parent,
                refs_used=[{"file": r["file"], "label": r.get("label", ""),
                            "kind": r.get("kind", ""), "src": "bakeoff"}
                           for r in b["refs"]],
                accepted=0, seq=i,
            )
            v["gen"] = gen
            ingested = True
            save_state(run, state)
        # ingest doesn't echo the stored filename — resolve board files by gen id
        if ingested or any(not v.get("board") for v in rec["variants"]):
            by_gen = {m.get("gen"): m.get("file") for m in br.images(pid)}
            for v in rec["variants"]:
                if not v.get("board") and v.get("gen") and by_gen.get(v["gen"]):
                    v["board"] = by_gen[v["gen"]]
                    log(state, f"{bid} {v['slot']}: ingested as {v['board']}")
            save_state(run, state)
        # -- stage A ---------------------------------------------------------
        for v in rec["variants"]:
            if v.get("stageA"):
                continue
            try:
                qa = br.qascan(pid, v["board"])
            except BridgeError as e:
                log(state, f"{bid} {v['slot']}: qascan error {e}")
                continue
            analysis = qa.get("analysis", qa)
            typed = analysis.get("typed", [])
            resolved = reg.resolve(typed, beat_kind=b["kind"])
            v["stageA"] = {
                "verdict": analysis.get("verdict"),
                "registry": [d["id"] for d in resolved],
                "resolved": resolved,
                "clean": not any(d["blocking"] for d in resolved),
            }
            log(state, f"{bid} {v['slot']}: stage A {analysis.get('verdict')} "
                       f"{[d['id'] for d in resolved] or 'clean'}")
            save_state(run, state)
        # -- verdict per round ----------------------------------------------
        judged = [v for v in rec["variants"] if v.get("stageA")]
        clean = [v for v in judged if v["stageA"]["clean"]]
        if not judged:
            continue
        if not clean:
            b["status"] = "retry"
            log(state, f"{bid}: 0/{len(judged)} clean -> retry")
        elif len(clean) == 1:
            b["winner"] = {"slot": clean[0]["slot"], "board": clean[0]["board"],
                           "via": "sole-survivor"}
            b["status"] = "clean"
            log(state, f"{bid}: single survivor {clean[0]['slot']} wins")
        else:
            # Stage B is pluggable: <run>/stageb-verdicts.json (written by ANY
            # fresh-context judge — e.g. an orchestrating Claude session's Sonnet
            # subagent when the local `claude` CLI has no auth) wins; otherwise a
            # fresh `claude -p` ranker; otherwise first-clean with a logged note.
            ext = _external_verdict(run, bid, [v["slot"] for v in clean])
            try:
                verdict = ext or judge_mod.rank_variants(
                    rec["prompt"], [
                        {"slot": v["slot"], "path": v["path"],
                         "stageA_summary": "; ".join(
                             f"{d['id']}:{d['detail'][:60]}"
                             for d in v["stageA"]["resolved"]) or "clean"}
                        for v in clean],
                    beat_kind=b["kind"], model=args.judge_model)
            except judge_mod.JudgeError as e:
                log(state, f"{bid}: stage B failed ({e}); falling back to first clean")
                verdict = {"winner": clean[0]["slot"], "ranking": [], "raw": str(e)}
            rec["stageB"] = {k: verdict[k] for k in ("winner", "ranking") if k in verdict}
            wv = next(v for v in clean if v["slot"] == verdict["winner"])
            b["winner"] = {"slot": wv["slot"], "board": wv["board"],
                           "via": "stage-b-external" if ext else "stage-b"}
            b["status"] = "clean"
            log(state, f"{bid}: stage B winner {wv['slot']} of {len(clean)} survivors")
        save_state(run, state)
    save_state(run, state)


def _external_verdict(run: Path, bid: str, slots: list[str]):
    f = run / "stageb-verdicts.json"
    if not f.is_file():
        return None
    v = json.loads(f.read_text()).get(bid)
    if not v or v.get("winner") not in slots:
        return None
    return v


# ---------------------------------------------------------------------------
# retry


def cmd_retry(args) -> None:
    run = Path(args.run)
    state = load_state(run)
    br = Bridge()
    pid = state["project"]
    sheet_p = run / "jobsheet.json"
    jobsheet = json.loads(sheet_p.read_text())
    for bid, b in state["beats"].items():
        if b["status"] != "retry":
            continue
        last = b["rounds"][-1]
        all_resolved = [d for v in last["variants"] if v.get("stageA")
                        for d in v["stageA"]["resolved"]]
        if b["retries"] >= MAX_RETRIES:
            # human-review queue: flag, tag, never silently ship
            best = min((v for v in last["variants"] if v.get("stageA")),
                       key=lambda v: sum(d["blocking"] for d in v["stageA"]["resolved"]),
                       default=None)
            if best:
                blockers = [d for d in best["stageA"]["resolved"] if d["blocking"]]
                top = blockers[0] if blockers else {"id": "MISC-00", "detail": ""}
                br.flag(pid, best["board"], top["id"],
                        note=f"bakeoff {state['runId']} {bid}: no clean variant "
                             f"after {MAX_RETRIES} retries", src="gate")
                br.write_decisions(pid, [{"file": best["board"],
                                          "addtags": ["bakeoff", "needs-human"]}])
            b["status"] = "human"
            log(state, f"{bid}: retries exhausted -> human-review queue")
            save_state(run, state)
            continue
        inj = reg.injections_for(all_resolved)
        new_prompt = b["prompt"] + "\n" + "\n".join(inj) if inj else b["prompt"]
        b["retries"] += 1
        b["rounds"].append({"round": len(b["rounds"]) + 1, "prompt": new_prompt,
                            "injected": inj, "variants": []})
        b["status"] = "generating"
        jobsheet.append(_job_entry(state, bid, len(b["rounds"])))
        log(state, f"{bid}: retry {b['retries']}/{MAX_RETRIES} queued with "
                   f"{len(inj)} injected fixes: {[i.split(':')[0] for i in inj]}")
    sheet_p.write_text(json.dumps(jobsheet, indent=1))
    save_state(run, state)


# ---------------------------------------------------------------------------
# select


def cmd_select(args) -> None:
    run = Path(args.run)
    state = load_state(run)
    br = Bridge()
    pid = state["project"]
    images = br.images(pid)
    by_file = {m.get("file"): m for m in images}
    accepted_groups = {m.get("group") for m in images if m.get("accepted")}
    for bid, b in state["beats"].items():
        if b["status"] != "clean" or not b.get("winner"):
            continue
        wfile = b["winner"]["board"]
        grp = (by_file.get(wfile) or {}).get("group", "")
        if grp and grp in accepted_groups:
            b["status"] = "selected"
            b["winner"]["note"] = "owner already accepted a panel in this group; not overridden"
            log(state, f"{bid}: group '{grp}' already has an owner-accepted winner — skipping")
            continue
        br.write_decisions(pid, [{"file": wfile, "accepted": True, "rating": "good",
                                  "addtags": ["bakeoff", "judge-pick"]}])
        b["status"] = "selected"
        log(state, f"{bid}: winner {b['winner']['slot']} accepted on board ({wfile})")
        save_state(run, state)
    save_state(run, state)


# ---------------------------------------------------------------------------
# stats


def cmd_stats(args) -> None:
    run = Path(args.run)
    state = load_state(run)
    rolls = clean_rolls = 0
    beats_r1_clean = beats_retry_clean = beats_human = 0
    defects_by_id: dict[str, int] = {}
    shipped_defects = shipped = 0
    for b in state["beats"].values():
        for i, rec in enumerate(b["rounds"]):
            for v in rec["variants"]:
                if not v.get("stageA"):
                    continue
                rolls += 1
                clean_rolls += int(v["stageA"]["clean"])
                for d in v["stageA"]["resolved"]:
                    defects_by_id[d["id"]] = defects_by_id.get(d["id"], 0) + 1
        if b["status"] in ("clean", "selected") and b.get("winner"):
            shipped += 1
            if len(b["rounds"]) == 1:
                beats_r1_clean += 1
            else:
                beats_retry_clean += 1
            for rec in b["rounds"]:
                for v in rec["variants"]:
                    if v["slot"] == b["winner"]["slot"] and v.get("stageA"):
                        shipped_defects += len(v["stageA"]["resolved"])
        elif b["status"] == "human":
            beats_human += 1
    n_beats = len(state["beats"])
    stats = {
        "runId": state["runId"], "project": state["project"],
        "backend": state["backend"], "at": now(),
        "beats": n_beats, "rolls": rolls,
        "cleanVariantRate": round(clean_rolls / rolls, 3) if rolls else None,
        "beatsCleanFirstRoll": beats_r1_clean,
        "beatsClearedAfterRetry": beats_retry_clean,
        "beatsHumanQueue": beats_human,
        "clearRate": round((beats_r1_clean + beats_retry_clean) / n_beats, 3) if n_beats else None,
        "defectsPerShippedPanel": round(shipped_defects / shipped, 2) if shipped else None,
        "defectsById": dict(sorted(defects_by_id.items(), key=lambda kv: -kv[1])),
        "creditsSpent": args.credits,
    }
    state["stats"] = stats
    save_state(run, state)
    _append_yield(stats)
    try:
        Bridge().push_yield(stats)
        print("yield stats pushed to studio (do=yield)")
    except BridgeError as e:
        print(f"note: studio yield push unavailable ({e}) — stats kept locally")
    print(json.dumps(stats, indent=1))


def _append_yield(stats: dict) -> None:
    YIELD_FILE.parent.mkdir(exist_ok=True)
    lock = YIELD_FILE.with_suffix(".lock")
    with open(lock, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        runs = json.loads(YIELD_FILE.read_text()) if YIELD_FILE.is_file() else []
        runs = [r for r in runs if r.get("runId") != stats["runId"]] + [stats]
        tmp = YIELD_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(runs, indent=1))
        tmp.rename(YIELD_FILE)


# ---------------------------------------------------------------------------
# status


def cmd_status(args) -> None:
    state = load_state(Path(args.run))
    print(f"run {state['runId']}  project {state['project']}  backend {state['backend']}")
    for bid, b in state["beats"].items():
        rnd = len(b["rounds"])
        w = b.get("winner")
        print(f"  {bid:14s} {b['status']:11s} round {rnd}  retries {b['retries']}"
              + (f"  winner {w['slot']} ({w['via']})" if w else ""))
    if state.get("stats"):
        s = state["stats"]
        print(f"  yield: cleanVariantRate={s['cleanVariantRate']} "
              f"clearRate={s['clearRate']} human={s['beatsHumanQueue']}")


# ---------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("--sheet", required=True)
    p.add_argument("--run-id"); p.set_defaults(fn=cmd_plan)
    p = sub.add_parser("collect"); p.add_argument("--run", required=True)
    p.add_argument("--tolerate-missing", type=int, default=1,
                   help="accept a round with up to N missing variants (filter drops)")
    p.set_defaults(fn=cmd_collect)
    p = sub.add_parser("judge"); p.add_argument("--run", required=True)
    p.add_argument("--judge-model", default=judge_mod.JUDGE_MODEL)
    p.set_defaults(fn=cmd_judge)
    p = sub.add_parser("retry"); p.add_argument("--run", required=True)
    p.set_defaults(fn=cmd_retry)
    p = sub.add_parser("select"); p.add_argument("--run", required=True)
    p.set_defaults(fn=cmd_select)
    p = sub.add_parser("stats"); p.add_argument("--run", required=True)
    p.add_argument("--credits", type=int, default=0)
    p.set_defaults(fn=cmd_stats)
    p = sub.add_parser("status"); p.add_argument("--run", required=True)
    p.set_defaults(fn=cmd_status)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
