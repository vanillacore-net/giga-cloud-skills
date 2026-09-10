#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
if [[ $# -eq 3 ]]; then
  CONTRACT=$1; CLUSTER=$2; REPLICAS=$3
elif [[ $# -eq 2 ]]; then
  CONTRACT=${CONTRACT_FILE:-$ROOT/environment-contract.yaml}; CLUSTER=$1; REPLICAS=$2
else
  printf 'usage: set-worker-replicas.sh [CONTRACT] CLUSTER REPLICAS\n' >&2
  exit 2
fi
[[ -f "$CONTRACT" ]] || { printf 'contract not found: %s\n' "$CONTRACT" >&2; exit 2; }
python3 - "$ROOT" "$CONTRACT" "$CLUSTER" "$REPLICAS" <<'PY'
from pathlib import Path
import sys,yaml
sys.path.insert(0, str(Path(sys.argv[1]) / 'scripts'))
from lablib import load_yaml, validate_environment
path=Path(sys.argv[2]); cluster_name=sys.argv[3]
try: replicas=int(sys.argv[4])
except ValueError: raise SystemExit('replicas must be an integer')
if cluster_name != 'service-a' or replicas not in (1,2):
    raise SystemExit('this exercise permits service-a replicas 1 or 2 only')
data=load_yaml(path)
cluster=next((x for x in data['clusters'] if x['name']==cluster_name),None)
if cluster is None: raise SystemExit(f'unknown cluster: {cluster_name}')
old=cluster['worker_replicas']; cluster['worker_replicas']=replicas
errors=validate_environment(data, require_live=True)
if errors: raise SystemExit('\n'.join(errors))
temporary=path.with_suffix(path.suffix+'.tmp')
temporary.write_text(yaml.safe_dump(data,sort_keys=False))
temporary.replace(path)
print(f'{cluster_name} worker replicas: {old} -> {replicas}')
PY
