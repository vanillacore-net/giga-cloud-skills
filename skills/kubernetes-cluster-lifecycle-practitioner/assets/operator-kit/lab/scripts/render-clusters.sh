#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CONTRACT=${1:-$ROOT/environment-contract.yaml}
OUTPUT=${2:-$ROOT/rendered}
[[ -f "$CONTRACT" ]] || { printf 'contract not found: %s\n' "$CONTRACT" >&2; exit 2; }
python3 "$ROOT/scripts/render-manifests.py" --contract "$CONTRACT" --output "$OUTPUT"
