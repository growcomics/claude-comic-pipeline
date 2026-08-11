#!/usr/bin/env python3
"""Tests for the location-scout toolchain + the next_panel pack-index fallback.

Covers:
  - scout_city.allocate() rounding guarantees + guards
  - slugify
  - tag-vocabulary validation
  - cgi_convert.download_result URL-scheme + payload guards
  - cgi_convert variant emit (base-plate requirement, prompt/source switch)
  - cgi_convert.record_qa verdict validation
  - pack_index on fixture packs (both layouts) + --verify error detection
  - next_panel.find_pack_env_ref exact / pack-slug / no-match resolution
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "skills" / "location-scout" / "scripts"))
sys.path.insert(0, str(REPO / "skills" / "comic-production" / "scripts"))

import cgi_convert  # noqa: E402
import pack_index  # noqa: E402
import scout_city  # noqa: E402

PASSED = 0
FAILED = []


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASSED
    if cond:
        PASSED += 1
    else:
        FAILED.append(f"{name}: {detail}")
        print(f"FAIL {name} {detail}")


# 1x1 valid PNG
PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c62620001000000ffff03000006000557bfabd40000000049454e44ae426082"
)


def test_allocate():
    a = scout_city.allocate(11, ["street", "restaurant", "landmark", "specific"])
    check("allocate sums to count", sum(a.values()) == 11, str(a))
    check("allocate min 1 per type", all(v >= 1 for v in a.values()), str(a))
    a = scout_city.allocate(4, ["street", "restaurant", "landmark", "specific"])
    check("allocate count==types gives 1 each", list(a.values()) == [1, 1, 1, 1], str(a))
    try:
        scout_city.allocate(2, ["street", "restaurant", "landmark"])
        check("allocate raises when count<types", False)
    except ValueError:
        check("allocate raises when count<types", True)
    a = scout_city.allocate(40, ["street", "specific"])
    check("allocate scales large counts", sum(a.values()) == 40, str(a))


def test_slugify():
    check("slugify basic", scout_city.slugify("Las Vegas") == "las-vegas")
    check("slugify punctuation", scout_city.slugify("St. Paul's, MN!") == "st-pauls-mn")
    check("slugify collapse", scout_city.slugify("  a   b  ") == "a-b")


def test_tag_vocabulary():
    bad = scout_city.validate_tags()
    check("DEFAULT_SCOPE tags all in vocabulary", bad == [], str(bad))
    vocab = json.loads((REPO / "skills" / "location-scout" / "tag-vocabulary.json").read_text())
    allowed = set(vocab["framing"]) | set(vocab["setting"]) | set(vocab["mood_time"])
    check("vocabulary is deduplicated",
          len(allowed) == len(vocab["framing"]) + len(vocab["setting"]) + len(vocab["mood_time"]),
          "overlap between framing/setting/mood_time")


def _scaffold_scout_pack(root: Path) -> Path:
    """Minimal scout-layout pack with one completed slot."""
    pack = root / "testville"
    (pack / "source").mkdir(parents=True)
    (pack / "cgi").mkdir()
    (pack / "meta").mkdir()
    (pack / "source" / "street-01-main.jpg").write_bytes(b"\xff\xd8\xff" + b"x" * 64)
    (pack / "cgi" / "street-01-main.png").write_bytes(PNG_BYTES)
    plan = {
        "city": "Testville", "city_slug": "testville", "count": 1,
        "targets": [{
            "id": "street-01", "type": "street", "intent": "test street",
            "google_maps_query": "Main St Testville", "final_id": "street-01-main",
            "source_image": "source/street-01-main.jpg",
            "cgi_image": "cgi/street-01-main.png",
            "tags": ["downtown"],
        }],
    }
    (pack / "_targets.json").write_text(json.dumps(plan))
    return pack


def _scaffold_flat_pack(root: Path) -> Path:
    """Minimal flat-layout pack: sources + provenance + one renamed plate."""
    pack = root / "flat-town"
    (pack / "cgi").mkdir(parents=True)
    (pack / "flat-town-01.jpg").write_bytes(b"\xff\xd8\xff" + b"x" * 64)
    (pack / "_provenance.md").write_text(
        "# flat-town — provenance\n\n## flat-town-01.jpg\n"
        "- Source: test\n- QA: [WIDE] test plaza wide shot\n"
    )
    (pack / "cgi" / "plaza-daz.jpg").write_bytes(b"\xff\xd8\xff" + b"y" * 64)
    (pack / "cgi" / "_provenance.md").write_text(
        "# flat-town / cgi — provenance\n\n## Plates\n\n"
        "| file | shot | source photo | id |\n|---|---|---|---|\n"
        "| plaza-daz.jpg | wide aerial | town plaza | abc123 |\n"
    )
    return pack


def test_pack_index():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "locations"
        root.mkdir()
        _scaffold_scout_pack(root)
        _scaffold_flat_pack(root)

        idx = pack_index.build_index(root)
        check("index sees both packs", idx["pack_count"] == 2, str(idx["pack_count"]))
        by_slug = {p["slug"]: p for p in idx["packs"]}
        check("scout pack complete", by_slug["testville"]["status"] == "complete",
              by_slug["testville"]["status"])
        flat = by_slug["flat-town"]
        ids = {e["id"] for e in flat["locations"]}
        check("flat pack has source entry", "flat-town-01" in ids, str(ids))
        check("flat pack has renamed plate entry", "plaza-daz" in ids, str(ids))
        plate = next(e for e in flat["locations"] if e["id"] == "plaza-daz")
        check("plate tags from plates table", "wide" in plate["tags"], str(plate["tags"]))
        check("plate intent from plates table", plate["intent"] == "town plaza", str(plate["intent"]))

        errors, warnings = pack_index.verify(root, idx)
        check("verify clean fixtures no errors", errors == [], str(errors))

        # break a referenced file → verify must error
        (root / "testville" / "cgi" / "street-01-main.png").unlink()
        idx2 = pack_index.build_index(root)
        errors2, _ = pack_index.verify(root, idx2)
        check("verify catches missing file", any("missing" in e for e in errors2), str(errors2))


def test_download_guards():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "locations"
        root.mkdir()
        pack = _scaffold_scout_pack(root)
        try:
            cgi_convert.download_result(pack, "street-01", "file:///etc/hosts")
            check("download rejects file://", False)
        except ValueError:
            check("download rejects file://", True)
        try:
            cgi_convert.download_result(pack, "street-01", "http://example.com/x.png")
            check("download rejects plain http", False)
        except ValueError:
            check("download rejects plain http", True)

        # non-image payload rejected (mock urlopen)
        class FakeResp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self, n=-1): return b"<html>error page</html>"
        orig = cgi_convert.urllib.request.urlopen
        cgi_convert.urllib.request.urlopen = lambda *a, **k: FakeResp()
        try:
            cgi_convert.download_result(pack, "street-01", "https://x.test/a.png")
            check("download rejects non-image payload", False)
        except RuntimeError:
            check("download rejects non-image payload", True)
        finally:
            cgi_convert.urllib.request.urlopen = orig


def test_variants_and_qa():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "locations"
        root.mkdir()
        pack = _scaffold_scout_pack(root)

        params = cgi_convert.emit_prompt(pack, "street-01", "nano_banana_2", variant="night")
        check("variant re-renders day plate", params["source_path"] == "cgi/street-01-main.png",
              params["source_path"])
        check("variant prompt is night language", "NIGHT" in params["prompt"], params["prompt"][:60])

        base = cgi_convert.emit_prompt(pack, "street-01", "nano_banana_2")
        check("base prompt uses source photo", base["source_path"] == "source/street-01-main.jpg",
              base["source_path"])

        try:
            cgi_convert.emit_prompt(pack, "street-01", "nano_banana_2", variant="martian-noon")
            check("unknown variant rejected", False)
        except ValueError:
            check("unknown variant rejected", True)

        # variant requires a base plate
        plan = json.loads((pack / "_targets.json").read_text())
        plan["targets"][0]["cgi_image"] = None
        (pack / "_targets.json").write_text(json.dumps(plan))
        try:
            cgi_convert.emit_prompt(pack, "street-01", "nano_banana_2", variant="night")
            check("variant without base plate rejected", False)
        except RuntimeError:
            check("variant without base plate rejected", True)
        plan["targets"][0]["cgi_image"] = "cgi/street-01-main.png"
        (pack / "_targets.json").write_text(json.dumps(plan))

        slot = cgi_convert.record_qa(pack, "street-01", "pass", None)
        check("record_qa writes verdict", slot["qa"]["verdict"] == "pass", str(slot.get("qa")))
        try:
            cgi_convert.record_qa(pack, "street-01", "excellent", None)
            check("record_qa rejects bad verdict", False)
        except ValueError:
            check("record_qa rejects bad verdict", True)

        manifest = cgi_convert.emit_manifest(pack)
        check("manifest carries qa", manifest["locations"][0]["qa"]["verdict"] == "pass")


def test_find_pack_env_ref():
    import next_panel
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        root = repo / "references" / "locations"
        root.mkdir(parents=True)
        _scaffold_scout_pack(root)
        idx = pack_index.build_index(root)
        (root / "index.json").write_text(json.dumps(idx))

        p = next_panel.find_pack_env_ref("street-01-main", repo_root=repo)
        check("pack fallback exact id", p is not None and p.name == "street-01-main.png",
              str(p))
        p = next_panel.find_pack_env_ref("testville", repo_root=repo)
        check("pack fallback by pack slug", p is not None, str(p))
        p = next_panel.find_pack_env_ref("moon-base", repo_root=repo)
        check("pack fallback no match → None", p is None, str(p))

        # QA-failed plates are never returned
        for pk in idx["packs"]:
            for e in pk["locations"]:
                e["qa"] = {"verdict": "fail"}
        (root / "index.json").write_text(json.dumps(idx))
        p = next_panel.find_pack_env_ref("street-01-main", repo_root=repo)
        check("pack fallback skips QA-fail plates", p is None, str(p))

        # malformed index → defensive None
        (root / "index.json").write_text("{not json")
        p = next_panel.find_pack_env_ref("street-01-main", repo_root=repo)
        check("pack fallback survives malformed index", p is None, str(p))


if __name__ == "__main__":
    test_allocate()
    test_slugify()
    test_tag_vocabulary()
    test_pack_index()
    test_download_guards()
    test_variants_and_qa()
    test_find_pack_env_ref()
    total = PASSED + len(FAILED)
    print(f"\n{PASSED}/{total} passed")
    if FAILED:
        sys.exit(1)
