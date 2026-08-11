#!/usr/bin/env python3
"""
board_item.py — Stage 7 (PUBLISHER) Wave-2: posting-board item helper.

Files the 🗓 posting-board ITEM that CHECKLIST.md step 0 asks for — lane =
Monthly comic / <property>, per-platform chips in their server-initialized
"todo" state — from a prepared bundle's posting/bundle/MANIFEST.json.
Board: https://3dmusclecomics.com/studio/posting.php (live state is the
server-side studio/data/posting.json; who-does-what is in
references/posting-board-alignment.md).

A SEPARATE, PER-ACTION, HUMAN-APPROVED ACT
  Creating a board item is state-tracking, not posting — but it WRITES to the
  live studio server, so per SKILL.md it stays outside bundle prep:
  prepare_post.py neither imports nor invokes this script, no workflow step
  auto-fires it, and the default mode is a WRITE-FREE dry run that prints the
  exact payload for review.  The --execute write refuses to run without
  --approved-by "<who/when>", which is to be passed only after the owner has
  approved THIS run.  The approval text is recorded in the receipt
  (posting/board-item.json, committed project text).

STRUCTURALLY UNABLE TO POST OR TOUCH CHIPS
  The only board actions this script can emit are `add` and `update`
  (ALLOWED_ACTIONS; the transport layer refuses anything else).  Neither can
  change per-platform chip state: posting.php initializes every chip to
  "todo" server-side on `add`, and its `update` merges text fields only.  The
  chip action (`plat`), art `upload`, and `del` are deliberately not
  implemented — chips move only when a human posts and flips them on the
  board.  Item status is restricted to draft|ready (never posted/skipped),
  and this script NEVER writes posting/posted.json.

READ BEFORE WRITE (live is truth)
  Every run first reads live board state via the wizard's read-only JSON
  endpoint (post/index.php?do=state) and validates the live vocabulary —
  lanes, property keys, chip keys — rather than trusting this checkout's copy
  of the PHP (the studio deploy-clobber hazard).  Updates start from the LIVE
  item and overlay only explicitly flagged fields, so edits a human made on
  the board (owner, caption, notes, uploaded art) survive; posting.php's
  `update` replaces every field it reads, so the full set is always re-sent
  (same contract the post/ wizard follows).

Auth: bridge key from ~/Documents/.3dmc-studio-bridge-key (the same key
posting.php/bridge.php accept), sent only as the X-Bridge-Key header — never
in a URL, never printed, never stored in the receipt.

Usage:
  # dry run (default — no write; live-state check + the exact payload):
  python3 skills/publisher/scripts/board_item.py --project projects/<p>

  # the approved write:
  python3 skills/publisher/scripts/board_item.py --project projects/<p> \
      --execute --approved-by "GG, in-session 2026-08-11"

  # adopt a card that already exists on the board (writes the local receipt
  # only — no server write, no approval needed):
  python3 skills/publisher/scripts/board_item.py --project projects/<p> --adopt po_xxxxxxxxxx

  # later: overlay ONLY flagged fields onto the live card (rest keeps live values):
  ... --slot 2026-09-28 --execute --approved-by "..."

Exit: 0 ok (incl. dry run) · 1 refusal / hard error · 2 network or API failure.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BOARD_BASE = "https://3dmusclecomics.com/studio/"
STATE_URL = BOARD_BASE + "post/index.php?do=state"
POST_URL = BOARD_BASE + "posting.php"
KEY_FILE = os.path.expanduser("~/Documents/.3dmc-studio-bridge-key")
LANE = "comic"  # this helper files Monthly-comic cards only (CHECKLIST.md step 0)
ALLOWED_ACTIONS = frozenset({"add", "update"})  # structural: no plat / upload / del
ALLOWED_STATUS = ("draft", "ready")             # never posted / skipped from here
PLATFORM_KEYS = ["site", "patreon", "deviantart", "twitter", "instagram"]
TIMEOUT = 30


def die(msg, code=1):
    print("REFUSED: %s" % msg if code == 1 else "ERROR: %s" % msg, file=sys.stderr)
    sys.exit(code)


def read_key(key_file):
    try:
        with open(key_file) as f:
            key = f.read().strip()
    except OSError:
        die("bridge key not readable at %s — every run (even dry) reads live board "
            "state, which needs it. See project_comic_studio_gui." % key_file)
    if len(key) < 16:
        die("bridge key at %s is too short to be the real key." % key_file)
    return key


def request_json(url, key, form=None):
    """GET (form=None) or POST (urlencoded form) with the key as a header only."""
    if form is not None:
        if form.get("action") not in ALLOWED_ACTIONS:
            raise AssertionError(
                "board_item.py tried to send action=%r — only %s are allowed. "
                "Chip states (plat), uploads, and deletes are out of scope BY DESIGN."
                % (form.get("action"), sorted(ALLOWED_ACTIONS)))
        if "plat" in form or form.get("status") not in (None,) + ALLOWED_STATUS:
            raise AssertionError("payload guard: chip fields or a non-draft/ready "
                                 "status slipped into the form: %r" % sorted(form))
    data = urllib.parse.urlencode(form).encode() if form is not None else None
    req = urllib.request.Request(url, data=data, headers={
        "X-Bridge-Key": key, "User-Agent": "publisher-board-item/1"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as e:
        die("board unreachable (%s): %s" % (url.split("?")[0], e), 2)
    try:
        j = json.loads(body)
    except ValueError:
        die("non-JSON from %s: %.200r" % (url.split("?")[0], body), 2)
    if not j.get("ok"):
        die("board said no: %s" % j.get("error", "(no error text)"), 2)
    return j


def fetch_live_state(key):
    """Read-only live-state fetch + vocabulary validation (live is truth)."""
    st = request_json(STATE_URL, key)
    lanes, plats = st.get("lanes") or {}, st.get("platforms") or {}
    if LANE not in lanes:
        die("live board has no %r lane (lanes=%s) — the board vocabulary moved; "
            "re-read studio/posting.php LIVE before trusting this helper." % (LANE, sorted(lanes)))
    if sorted(plats) != sorted(PLATFORM_KEYS):
        die("live chip keys %s != expected %s — board vocabulary moved; update this "
            "helper (and prepare_post.py PLATFORM_KEYS) from the LIVE files." % (sorted(plats), PLATFORM_KEYS))
    return st


def load_manifest(project):
    path = os.path.join(project, "posting", "bundle", "MANIFEST.json")
    if not os.path.exists(path):
        die("no bundle at %s — run prepare_post.py first; the board item is filed "
            "FROM a prepared bundle, never ahead of one." % path)
    with open(path) as f:
        m = json.load(f)
    for k in ("title", "property", "comic_id"):
        if not m.get(k):
            die("bundle MANIFEST.json lacks %r — re-prepare the bundle." % k)
    return m


def month_window():
    """Months the board's Monthly grid renders (current + next, UTC like the PHP)."""
    today = datetime.now(timezone.utc).date()
    y, mo = (today.year, today.month + 1) if today.month < 12 else (today.year + 1, 1)
    return today, ["%04d-%02d" % (today.year, today.month), "%04d-%02d" % (y, mo)]


def derive_slot(explicit, release_date):
    today, window = month_window()
    if explicit:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", explicit):
            die("--slot must be YYYY-MM-DD (got %r)." % explicit)
        note = "" if explicit[:7] in window else (
            "⚠ slot %s is outside the board's visible months (%s) — the card will "
            "exist but render in NO Monthly cell until its month arrives." % (explicit, "/".join(window)))
        return explicit, note
    if release_date and re.match(r"^\d{4}-\d{2}-\d{2}$", release_date) and release_date[:7] in window:
        return release_date, "slot = bundle release_date"
    return today.isoformat(), (
        "slot = today (bundle release_date %s is %s the board's visible months %s)"
        % (release_date, "outside" if release_date else "absent —", "/".join(window)))


def notes_line(manifest, slug):
    pages = (manifest.get("pages") or {}).get("count")
    bits = ["📦 bundle: projects/%s/posting/bundle (CHECKLIST + captions + crop specs)" % slug]
    if pages:
        bits.append("%dpp" % pages)
    if manifest.get("release_date"):
        bits.append("release %s" % manifest["release_date"])
    bits.append("board_item.py %s" % datetime.now(timezone.utc).date().isoformat())
    return " · ".join(bits)


def find_by_id(items, item_id):
    return next((it for it in items if it.get("id") == item_id), None)


def load_receipt(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (ValueError, OSError) as e:
        die("receipt %s unreadable (%s) — fix or remove it before running." % (path, e))


def write_receipt(path, receipt, entry):
    receipt = receipt or {
        "_note": "Receipt for this project's 🗓 posting-board card — written ONLY by "
                 "skills/publisher/scripts/board_item.py (dry runs never write it). "
                 "Chip states live on the board, never here (posting-board-alignment.md). "
                 "This is NOT posting/posted.json and never becomes it.",
        "board": POST_URL,
        "history": [],
    }
    receipt.update({k: entry[k] for k in ("item_id", "lane", "property", "last_action", "executed_at")})
    receipt["history"].append(entry)
    with open(path, "w") as f:
        json.dump(receipt, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return path


def show(payload):
    for k in ("action", "id", "title", "property", "lane", "slot", "status", "owner",
              "caption", "notes", "assets"):
        if k in payload:
            v = payload[k]
            print("  %-9s %s" % (k, ("(empty)" if v == "" else
                                     v if len(str(v)) < 100 else str(v)[:97] + "…")))


def main():
    ap = argparse.ArgumentParser(description="File/refresh the posting-board card for a "
                                 "prepared publish bundle. DRY RUN by default; the write "
                                 "is a separate owner-approved act.")
    ap.add_argument("--project", required=True, help="projects/<p> directory")
    ap.add_argument("--slot", help="Target date YYYY-MM-DD (default: bundle release_date "
                                   "if in the board's visible months, else today)")
    ap.add_argument("--status", choices=ALLOWED_STATUS,
                    help="Item status (add default: draft). posted/skipped are impossible "
                         "from here by design.")
    ap.add_argument("--owner", help="Who fires it (board 'owner' field)")
    ap.add_argument("--refresh-text", action="store_true",
                    help="update only: re-derive title + notes from the bundle MANIFEST")
    ap.add_argument("--adopt", metavar="PO_ID",
                    help="Record an existing board card as this project's item "
                         "(local receipt only — no server write)")
    ap.add_argument("--execute", action="store_true",
                    help="Perform the write. Refuses without --approved-by.")
    ap.add_argument("--approved-by", metavar="WHO_WHEN",
                    help='Owner approval for THIS run, e.g. "GG, in-session 2026-08-11". '
                         "Pass only after the owner actually approved; recorded in the receipt.")
    ap.add_argument("--key-file", default=KEY_FILE, help="Bridge-key file (default: %(default)s)")
    args = ap.parse_args()

    project = os.path.abspath(args.project)
    if not os.path.isdir(project):
        die("no such project dir: %s" % project)
    slug = os.path.basename(project.rstrip("/"))

    if os.path.exists(os.path.join(project, "posting", "posted.json")):
        die("posting/posted.json exists — this comic is already posted; the board card "
            "is history now and any change to it is the human's, on the board.")

    manifest = load_manifest(project)
    receipt_path = os.path.join(project, "posting", "board-item.json")
    receipt = load_receipt(receipt_path)

    key = read_key(args.key_file)
    state = fetch_live_state(key)
    items = state.get("items") or []
    props = state.get("props") or {}

    prop = manifest["property"]
    if prop not in props:
        die("property %r has no lane on the live board (live: %s) — posting.php would "
            "SILENTLY re-lane it to growgetter, which is exactly the wrong-lane card "
            "this check exists to prevent. (3dmc and transferred properties have no "
            "Monthly-comic lane.)" % (prop, sorted(props)))

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ---- adopt: local-only bookkeeping ------------------------------------
    if args.adopt:
        live = find_by_id(items, args.adopt)
        if not live:
            die("no live card with id %r (archived posted/skipped cards are not "
                "adoptable — the comic would be posted; deleted ones are gone)." % args.adopt)
        if live.get("lane") != LANE or live.get("property") != prop:
            die("card %s is lane=%s property=%s — this project's bundle is Monthly comic "
                "/ %s; refusing to adopt a mismatched card." % (
                    args.adopt, live.get("lane"), live.get("property"), prop))
        write_receipt(receipt_path, receipt, {
            "item_id": live["id"], "lane": LANE, "property": prop,
            "last_action": "adopt", "executed_at": now,
            "approved_by": None, "payload": None,
            "server_response": {"adopted_title": live.get("title")},
            "manifest": {"comic_id": manifest["comic_id"], "title": manifest["title"],
                         "prepared_at": manifest.get("prepared_at")},
        })
        print("Adopted live card %s (%r) → %s" % (live["id"], live.get("title"),
                                                  os.path.relpath(receipt_path)))
        print("No server write happened. Future runs of this helper will UPDATE that card.")
        return

    # ---- decide add vs update ---------------------------------------------
    live = None
    if receipt and receipt.get("item_id"):
        live = find_by_id(items, receipt["item_id"])
        if not live:
            die("receipt names card %s but the live board doesn't show it — either it "
                "was archived (status posted/skipped: the human's business, leave it) "
                "or deleted (then remove %s and re-run to create fresh)."
                % (receipt["item_id"], os.path.relpath(receipt_path)))
        if live.get("lane") != LANE or live.get("property") != prop:
            die("receipt card %s is now lane=%s property=%s (expected %s/%s) — someone "
                "re-laned it on the board; sort that out there, not from here." % (
                    receipt["item_id"], live.get("lane"), live.get("property"), LANE, prop))
        mode = "update"
    else:
        title_key = manifest["title"].strip().casefold()
        clash = next((it for it in items
                      if it.get("lane") == LANE and it.get("property") == prop
                      and str(it.get("title", "")).strip().casefold() == title_key), None)
        if clash:
            die("live card %s already carries this title in Monthly comic / %s but no "
                "receipt links it to this project. If it IS this comic: --adopt %s. "
                "If not, retitle one of them first — two identical cards helps nobody."
                % (clash["id"], prop, clash["id"]))
        mode = "add"

    # ---- build payload -----------------------------------------------------
    if mode == "add":
        slot, slot_note = derive_slot(args.slot, manifest.get("release_date"))
        payload = {
            "action": "add",
            "title": manifest["title"],
            "property": prop,
            "lane": LANE,
            "slot": slot,
            "status": args.status or "draft",
            "owner": args.owner or "",
            "caption": "",  # captions live in the bundle; the board stays thin
            "notes": notes_line(manifest, slug),
            "assets": "",
        }
    else:
        overlay = {}
        if args.slot:
            overlay["slot"], slot_note = derive_slot(args.slot, None)
        else:
            slot_note = ""
        if args.status:
            overlay["status"] = args.status
        if args.owner is not None:
            overlay["owner"] = args.owner
        if args.refresh_text:
            overlay["title"] = manifest["title"]
            overlay["notes"] = notes_line(manifest, slug)
        if not overlay:
            print("Nothing to update — card %s exists and no overlay flag was given "
                  "(--slot/--status/--owner/--refresh-text). Live card untouched." % live["id"])
            return
        # posting.php `update` replaces every field it reads → re-send the full
        # LIVE field set (human edits + uploaded-art assets survive), overlay last.
        payload = {
            "action": "update", "id": live["id"],
            "title": live.get("title", ""), "property": prop, "lane": LANE,
            "slot": live.get("slot", ""), "status": live.get("status", "draft"),
            "owner": live.get("owner", ""), "caption": live.get("caption", ""),
            "notes": live.get("notes", ""),
            "assets": "\n".join(live.get("assets") or []),
        }
        if payload["status"] not in ALLOWED_STATUS:
            # a live card can be in a state this helper must not re-assert
            die("live card status is %r — this helper only handles draft/ready cards; "
                "posted/skipped are the human's." % payload["status"])
        payload.update(overlay)

    # ---- report ------------------------------------------------------------
    print("Board:   %s" % POST_URL)
    print("Project: %s (comic_id=%s)" % (slug, manifest["comic_id"]))
    print("Mode:    %s%s" % (mode.upper(),
                             " → card %s" % live["id"] if live else
                             " (no matching live card; %d live items checked)" % len(items)))
    if slot_note:
        print("Note:    %s" % slot_note)
    print("Chips:   %s" % ("initialized to 'todo' by the server on add — this helper "
                           "cannot arm or flip them" if mode == "add"
                           else "untouched (update cannot reach chip state)"))
    print("Payload:")
    show(payload)

    if not args.execute:
        print("\nDRY RUN — nothing was written. The write is a separate, per-action,")
        print("owner-approved act (SKILL.md). Once the owner approves THIS payload:")
        print("  ... --execute --approved-by \"<who, how/when approved>\"")
        return

    if not (args.approved_by or "").strip():
        die("--execute without --approved-by. The board write needs the owner's "
            "per-action approval first; then pass e.g. --approved-by \"GG, in-session %s\"."
            % now[:10])

    print("\nEXECUTING (approved by: %s)" % args.approved_by)
    resp = request_json(POST_URL, key, form=payload)
    item_id = resp.get("id") or (live or {}).get("id") or ""
    write_receipt(receipt_path, receipt, {
        "item_id": item_id, "lane": LANE, "property": prop,
        "last_action": mode, "executed_at": now,
        "approved_by": args.approved_by.strip(),
        "payload": payload,
        "server_response": resp,
        "manifest": {"comic_id": manifest["comic_id"], "title": manifest["title"],
                     "prepared_at": manifest.get("prepared_at")},
    })
    print("OK — card %s %s. Receipt: %s (commit it — it's project text)." % (
        item_id, "created" if mode == "add" else "updated", os.path.relpath(receipt_path)))
    print("Chips are all 'todo' until a human posts and flips them on the board.")


if __name__ == "__main__":
    main()
