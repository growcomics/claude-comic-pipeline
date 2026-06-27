#!/bin/bash
# push-env-refs.sh — land real-photo-derived LOCATION plates into a Comic Studio
# project as kind=scene references, via the bridge's `ingest_ref` verb.
#
# WHY: AI-only backgrounds read as "too AI" (samey crowds, invented geometry). The
# fix the owner wants: source REAL photos of the location, restyle them to the
# project's CGI / DAZ3D look, and use THOSE as the env reference attached to every
# panel at that location (the env-ref-every-panel lesson). This script is the last
# mile of that pipeline — it pushes the plates into the studio so refs.php shows
# them and shots.php attaches them.
#
# PIPELINE (see studio/docs/REAL-PHOTO-ENV-REFS.md for the full SOP):
#   1. reference-gathering skill  -> references/locations/<slug>/<slug>-NN.jpg  (+ _provenance.md)
#   2. DAZ/CGI restyle each plate -> references/locations/<slug>/cgi/<name>-daz.jpg
#   3. THIS SCRIPT                 -> studio project, kind=scene, approved + locked
#   4. shots.php match_scene()     -> attaches the plate to every panel at that location
#   5. worker / Flow               -> composites the character INTO the CGI plate
#
# USAGE
#   Folder mode (recommended — push a gathered location folder):
#     push-env-refs.sh --project muller --location "Commercial gym" \
#         --dir references/locations/commercial-gym/ --lock
#       -> pushes cgi/*  as approved scene plates (the ones attached to panels).
#          Add --include-source to ALSO push the raw photos as *pending* scene refs
#          (visible context + provenance; NOT attached unless you approve them).
#
#   Explicit-file mode (push specific images):
#     push-env-refs.sh --project muller --location "Commercial gym" \
#         --status approved --lock plate1.jpg plate2.jpg
#
# OPTIONS
#   --project ID        studio project id (required)        e.g. muller
#   --location "NAME"   location label -> ref.char (required; shots.php matches on it)
#   --dir DIR           folder mode: a references/locations/<slug>/ folder
#   --include-source    (folder mode) also push raw photos as pending real-source refs
#   --kind K            ref kind (default: scene)           scene|face|body|view|prop
#   --status S          approved|pending (default: approved for plates / explicit files)
#   --role R            cgi-plate|real-source (provenance tag; folder mode sets it)
#   --label "L"         label override (default: filename stem)
#   --prov "TEXT"       provenance (default: contents of the folder's _provenance.md)
#   --lock              if the project is already locked, make the plate live NOW
#   --bridge URL        bridge endpoint (default 3dmusclecomics.com/studio/bridge.php)
#   --key KEY           bridge key (default: ~/.3dmc-studio-bridge-key or $STUDIO_BRIDGE_KEY)
#   --dry-run           print what WOULD be pushed, send nothing
#
# Provenance/copyright: these are REFERENCES for derivative CGI work, not assets to
# republish. Prefer CC0 / Wikimedia / press-kit sources; the prov field travels with
# every ref so the source + license stay attached. (See the skill's hard rules.)
set -u

BRIDGE="https://3dmusclecomics.com/studio/bridge.php"
KEY="${STUDIO_BRIDGE_KEY:-}"
[ -z "$KEY" ] && [ -f "$HOME/Documents/.3dmc-studio-bridge-key" ] && KEY="$(tr -d '[:space:]' < "$HOME/Documents/.3dmc-studio-bridge-key")"
PROJECT=""; LOCATION=""; DIR=""; KIND="scene"; STATUS=""; ROLE=""; LABEL=""; PROV=""
LOCK=""; DRYRUN=""; INCLUDE_SOURCE=""
FILES=()

while [ $# -gt 0 ]; do
  case "$1" in
    --project) PROJECT="$2"; shift 2;;
    --location) LOCATION="$2"; shift 2;;
    --dir) DIR="$2"; shift 2;;
    --include-source) INCLUDE_SOURCE=1; shift;;
    --kind) KIND="$2"; shift 2;;
    --status) STATUS="$2"; shift 2;;
    --role) ROLE="$2"; shift 2;;
    --label) LABEL="$2"; shift 2;;
    --prov) PROV="$2"; shift 2;;
    --lock) LOCK=1; shift;;
    --bridge) BRIDGE="$2"; shift 2;;
    --key) KEY="$2"; shift 2;;
    --dry-run) DRYRUN=1; shift;;
    -h|--help) sed -n '2,60p' "$0"; exit 0;;
    -*) echo "unknown option: $1" >&2; exit 2;;
    *) FILES+=("$1"); shift;;
  esac
done

[ -z "$PROJECT" ]  && { echo "ERROR: --project is required" >&2; exit 2; }
[ -z "$LOCATION" ] && { echo "ERROR: --location is required" >&2; exit 2; }
[ -z "$KEY" ]      && { echo "ERROR: no bridge key (set --key, \$STUDIO_BRIDGE_KEY, or ~/Documents/.3dmc-studio-bridge-key)" >&2; exit 2; }

mime_of() { case "${1##*.}" in jpg|jpeg|JPG|JPEG) echo image/jpeg;; png|PNG) echo image/png;; webp|WEBP) echo image/webp;; gif|GIF) echo image/gif;; *) echo application/octet-stream;; esac; }
stem()    { local b; b="$(basename "$1")"; b="${b%.*}"; echo "$b" | tr '_-' '  ' | sed 's/  */ /g'; }

# one push. args: file kind status role label prov lock
push_one() {
  local f="$1" k="$2" s="$3" r="$4" l="$5" p="$6" lk="$7"
  if [ ! -f "$f" ]; then echo "  ✗ missing: $f" >&2; return 1; fi
  if [ -n "$DRYRUN" ]; then
    printf '  WOULD push %-42s kind=%-6s status=%-8s role=%-11s label="%s"\n' "$(basename "$f")" "$k" "$s" "${r:-–}" "$l"
    return 0
  fi
  local args=(-s -X POST "$BRIDGE"
    -F "key=$KEY" -F "do=ingest_ref" -F "p=$PROJECT"
    -F "file=@$f;type=$(mime_of "$f")" -F "orig=$(basename "$f")"
    -F "kind=$k" -F "char=$LOCATION" -F "label=$l" -F "status=$s")
  [ -n "$r" ]  && args+=(-F "role=$r")
  [ -n "$p" ]  && args+=(-F "prov=$p")
  [ -n "$lk" ] && args+=(-F "lock=1")
  curl "${args[@]}" | python3 -c "
import sys,json
try: d=json.load(sys.stdin)
except Exception: print('  ✗ $(basename "$f"): non-JSON ->', sys.stdin.read()[:120]); sys.exit(1)
if d.get('ok'): print('  ✓ $(basename "$f") -> %s/%s (refsTotal=%s%s)' % (d.get('kind'),d.get('status'),d.get('refsTotal'),', locked' if d.get('lockedNow') else ''))
else: print('  ✗ $(basename "$f"):', d.get('error')); sys.exit(1)
"
}

echo "Pushing env refs -> project '$PROJECT'  location '$LOCATION'  (bridge: ${BRIDGE})"
[ -n "$DRYRUN" ] && echo "  (DRY RUN — nothing sent)"

if [ -n "$DIR" ]; then
  DIR="${DIR%/}"
  [ -d "$DIR" ] || { echo "ERROR: --dir not found: $DIR" >&2; exit 2; }
  # default provenance = the folder's _provenance.md (so source URLs + license travel with each ref)
  if [ -z "$PROV" ] && [ -f "$DIR/_provenance.md" ]; then PROV="$(head -c 1100 "$DIR/_provenance.md")"; fi
  # 1) CGI plates (the attachable env refs) — cgi/*.jpg|png|webp
  cgi_n=0
  if [ -d "$DIR/cgi" ]; then
    shopt -s nullglob
    for f in "$DIR"/cgi/*.{jpg,jpeg,png,webp,JPG,JPEG,PNG,WEBP}; do
      [ -e "$f" ] || continue
      push_one "$f" "$KIND" "${STATUS:-approved}" "${ROLE:-cgi-plate}" "${LABEL:-$(stem "$f")}" "$PROV" "${LOCK}"
      cgi_n=$((cgi_n+1))
    done
    shopt -u nullglob
  fi
  [ "$cgi_n" -eq 0 ] && echo "  (no CGI plates in $DIR/cgi/ — convert the photos to your CGI look first, or pass --include-source / explicit files)"
  # 2) optional: raw source photos as PENDING context refs (not attached unless approved)
  if [ -n "$INCLUDE_SOURCE" ]; then
    shopt -s nullglob
    for f in "$DIR"/*.{jpg,jpeg,png,webp,JPG,JPEG,PNG,WEBP}; do
      [ -e "$f" ] || continue
      push_one "$f" "$KIND" "pending" "real-source" "real-source: ${LABEL:-$(stem "$f")}" "$PROV" ""
    done
    shopt -u nullglob
  fi
else
  [ "${#FILES[@]}" -eq 0 ] && { echo "ERROR: give --dir DIR or one or more image files" >&2; exit 2; }
  for f in "${FILES[@]}"; do
    push_one "$f" "$KIND" "${STATUS:-approved}" "$ROLE" "${LABEL:-$(stem "$f")}" "${PROV:-}" "${LOCK}"
  done
fi

echo "Done. Review in the studio: ${BRIDGE%/bridge.php}/refs.php?p=${PROJECT}  (lock the plates, then the production guide attaches them to every panel at this location)"
