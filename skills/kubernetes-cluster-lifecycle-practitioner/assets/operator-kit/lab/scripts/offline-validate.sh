#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

python3 "$ROOT/tests/test_lab.py"

# Check the declarative seed foundation when the local tools are available.
# No OpenStack credentials or live resources are required for these checks.
if command -v tofu >/dev/null 2>&1; then
  tofu fmt -check -recursive "$ROOT/foundation/opentofu"
  if [[ -d "$ROOT/foundation/opentofu/bootstrap/.terraform/providers" ]]; then
    tofu -chdir="$ROOT/foundation/opentofu/bootstrap" validate
  else
    printf 'OpenTofu provider cache absent; schema validation skipped after format check\n'
  fi
fi
if command -v ansible-playbook >/dev/null 2>&1; then
  ansible-playbook \
    -i "$ROOT/foundation/ansible/inventory.example.yaml" \
    "$ROOT/foundation/ansible/seed.yaml" --syntax-check
fi

python3 "$ROOT/scripts/render-manifests.py" \
  --contract "$ROOT/environment-contract.example.yaml" \
  --output "$TMP/rendered" \
  --allow-example
python3 - "$ROOT" "$TMP/rendered" <<'PY'
from pathlib import Path
import sys,yaml
paths=[Path(sys.argv[1])/'manifests/base/clusterclass.yaml',*Path(sys.argv[2]).rglob('*.yaml')]
for path in paths:
 docs=[doc for doc in yaml.safe_load_all(path.read_text()) if doc]
 if not docs: raise SystemExit(f'no YAML objects in {path}')
 for doc in docs:
  if not all(key in doc for key in ('apiVersion','kind','metadata')):
   raise SystemExit(f'incomplete Kubernetes object in {path}')
print(f'parsed {len(paths)} manifest files')
PY
printf 'offline validation passed\n'
