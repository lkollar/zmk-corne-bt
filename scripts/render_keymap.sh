#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTDIR="$ROOT/debug/keymap-drawer"
CACHE_DIR="$ROOT/.uv-cache"
TOOL_DIR="$ROOT/.uv-tools"
XDG_CACHE_HOME="$ROOT/.cache"
KEYMAP_BIN="$ROOT/.uv-cache/archive-v0/OTNLxk7KYnhCcHYC-bEUb/bin/keymap"
KEYMAP_PY="$ROOT/.uv-cache/archive-v0/OTNLxk7KYnhCcHYC-bEUb/bin/python"

mkdir -p "$OUTDIR" "$CACHE_DIR" "$TOOL_DIR" "$XDG_CACHE_HOME/fontconfig"

export UV_CACHE_DIR="$CACHE_DIR"
export UV_TOOL_DIR="$TOOL_DIR"
export XDG_CACHE_HOME

KEYMAP="$ROOT/config/corne.keymap"
CFG="$ROOT/keymap-drawer-config.yaml"
RAW_YAML="$OUTDIR/corne-raw.yaml"
YAML="$OUTDIR/corne.yaml"
SVG="$OUTDIR/corne.svg"
PNG="$OUTDIR/corne.png"
PDF="$OUTDIR/corne.pdf"

"$KEYMAP_BIN" parse -z "$KEYMAP" -o "$RAW_YAML"
"$KEYMAP_PY" - "$RAW_YAML" "$YAML" <<'PY'
from pathlib import Path
import sys
import yaml

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
ghost = {0, 11, 12, 23, 24, 35}

data = yaml.safe_load(src.read_text())
for name, layer in data["layers"].items():
    out = []
    for i, key in enumerate(layer):
        if i in ghost and (key == "" or key is None):
            out.append({"type": "ghost"})
        else:
            out.append(key)
    data["layers"][name] = out

dst.write_text(yaml.safe_dump(data, sort_keys=False))
PY
"$KEYMAP_BIN" -c "$CFG" draw "$YAML" -o "$SVG"
rsvg-convert -f png -o "$PNG" "$SVG"
rsvg-convert -f pdf -o "$PDF" "$SVG"

cp "$SVG" "$ROOT/keymap.svg"
cp "$PNG" "$ROOT/keymap.png"
cp "$PDF" "$ROOT/keymap.pdf"

echo "Wrote:"
echo "  $RAW_YAML"
echo "  $YAML"
echo "  $SVG"
echo "  $PNG"
echo "  $PDF"
echo "  $ROOT/keymap.svg"
echo "  $ROOT/keymap.png"
echo "  $ROOT/keymap.pdf"
