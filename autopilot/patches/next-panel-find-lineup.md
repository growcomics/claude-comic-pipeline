# Patch: `skills/comic-production/scripts/next_panel.py` — `find_lineup()` config awareness

Today `find_lineup()` looks for hard-coded `muscle-size-lineup.png` / `muscle-size-lineup-4-9.png`. To support BE / glute / MMG runs, it needs to read `lineup_files.tier_low` and `lineup_files.tier_high` from `production-config.json`.

This patch is OPTIONAL but recommended. Without it, BE / glute / MMG users have to either:
- Symlink their lineup file to the FMG filename (e.g. `ln -s breast-size-lineup.png muscle-size-lineup.png`), or
- Rename their lineup file to `muscle-size-lineup.png`

With the patch, the lineup filename per project comes from the config — no symlinks needed.

## Find this function in `next_panel.py`

```python
def find_lineup(root: Path, tier: int | None) -> Path | None:
    """Locate the muscle-size lineup PNG. Tries multiple paths in order:
    project-local override, repo-bundled, user-installed, plugin-installed.
    Returns None if not found anywhere — caller MUST handle this (per L11
    no-phantom-refs rule). Returns the 1-6 lineup for tier <= 6 and the 4-9
    lineup for tier >= 7.
    """
    if tier is not None and tier >= 7:
        filename = "muscle-size-lineup-4-9.png"
    else:
        filename = "muscle-size-lineup.png"

    # ... rest of function searches the paths and returns ...
```

(Exact function body varies — just find the part where `filename` is hard-coded.)

## Replace with (only the lineup-filename-selection part)

```python
def _read_config(root: Path) -> dict | None:
    """Read production-config.json at project root. Returns None if missing
    or malformed (caller falls back to FMG defaults)."""
    cfg_path = root / "production-config.json"
    if not cfg_path.is_file():
        return None
    try:
        return json.loads(cfg_path.read_text())
    except Exception:
        return None


def find_lineup(root: Path, tier: int | None) -> Path | None:
    """Locate the size-anchor lineup PNG. Reads filenames from
    production-config.json's `lineup_files` block when present; falls back to
    the FMG defaults (`muscle-size-lineup.png` / `muscle-size-lineup-4-9.png`)
    when the config is missing. Searches multiple paths in order: project-local
    override, repo-bundled, user-installed, plugin-installed. Returns None if
    not found anywhere — caller MUST handle this (per L11 no-phantom-refs rule).
    """
    cfg = _read_config(root)
    lineup_cfg = (cfg or {}).get("lineup_files", {})
    tier_low_name = lineup_cfg.get("tier_low", "muscle-size-lineup.png")
    tier_high_name = lineup_cfg.get("tier_high", "muscle-size-lineup-4-9.png")
    active_range = lineup_cfg.get("active_range", "auto")

    # Pick filename per active_range and tier
    if active_range == "low":
        filename = tier_low_name
    elif active_range == "high":
        filename = tier_high_name
    else:  # auto
        if tier is not None and tier >= 7:
            filename = tier_high_name
        else:
            filename = tier_low_name

    # ... rest of the function (path search) stays IDENTICAL ...
```

The path-search logic in the existing function (project-local → repo-bundled → user-installed → plugin-installed) is unchanged. Only the `filename` selection at the top of the function changes.

## What it enables

Before: `find_lineup()` always looks for `muscle-size-lineup.png`. A BE comic with `breast-size-lineup.png` would emit `MISSING_lineup` even though the right file exists in `references/style/`.

After: the config tells `find_lineup()` which filename to look for. The BE project's `lineup_files.tier_low = "breast-size-lineup.png"` resolves to the right file. Same path search, different filename.

Per-type defaults baked in the schema:

| transformation_type | tier_low | tier_high |
|---|---|---|
| fmg | `muscle-size-lineup.png` | `muscle-size-lineup-4-9.png` |
| be | `breast-size-lineup.png` | `breast-size-lineup-4-9.png` |
| glute | `glute-size-lineup.png` | `glute-size-lineup-4-9.png` |
| mmg | `male-muscle-lineup.png` | `male-muscle-lineup-4-9.png` |
| mixed | `muscle-size-lineup.png` | `muscle-size-lineup-4-9.png` (override per-project as needed) |

The actual lineup PNGs for BE / glute / MMG are NOT bundled with the pipeline — you create them once per type (numbered 1-6 figures in identical pose, progressive growth of the target attribute, same outfit / hair / background) and drop them in `<project>/references/style/`. The pipeline picks them up automatically once the config points to the filename.

## Backward compatibility

A project without `production-config.json` still works exactly as before — `_read_config()` returns None, and `find_lineup()` uses the hard-coded FMG defaults via the `.get()` fallback. No regression for legacy projects.

## Lines changed

~15 lines added (the `_read_config()` helper + the lineup-filename-selection block). Path-search logic untouched. `json` import probably already present at the top of the file.

## Skip this patch?

If you don't want to touch `next_panel.py`, the workaround is:

```bash
# In any BE/glute/MMG project, symlink your actual lineup to the FMG filename:
cd <project>/references/style/
ln -s breast-size-lineup.png muscle-size-lineup.png

# Repeat for tier_high if you have one:
ln -s breast-size-lineup-4-9.png muscle-size-lineup-4-9.png
```

`find_lineup()` will pick up the symlink the same as a real file. Less clean than the patch, but works without code changes.
