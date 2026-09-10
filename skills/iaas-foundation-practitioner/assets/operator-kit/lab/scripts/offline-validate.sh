#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
python3 scripts/preflight.py --allow-example environment-contract.example.yaml
python3 -m py_compile scripts/preflight.py
for script in scripts/*.sh; do
  bash -n "$script"
done
python3 -m unittest discover -s tests -p 'test_*.py'
printf 'Chapter 3 lab offline validation passed\n'
