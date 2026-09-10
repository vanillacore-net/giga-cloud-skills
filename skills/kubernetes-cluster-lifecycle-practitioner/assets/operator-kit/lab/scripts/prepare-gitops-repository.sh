#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CONFIG_REPO=${1:?usage: prepare-gitops-repository.sh CONFIG_REPO}
CONFIG_REPO=$(cd "$CONFIG_REPO" && pwd)

[ -d "$CONFIG_REPO/.git" ] || { echo "ERROR: CONFIG_REPO must be the root of a Git clone" >&2; exit 2; }
for name in service-a loadbalancer; do
  [ -s "$ROOT/rendered/${name}.yaml" ] || {
    echo "ERROR: render $ROOT/rendered/${name}.yaml from the reviewed environment contract first" >&2
    exit 2
  }
  for addon in cert-manager contour storage; do
    [ -s "$ROOT/rendered/addons/${name}-${addon}.yaml" ] || {
      echo "ERROR: render $ROOT/rendered/addons/${name}-${addon}.yaml first" >&2
      exit 2
    }
  done
done
mkdir -p "$CONFIG_REPO/clusters" "$CONFIG_REPO/workloads/demo"
cp "$ROOT/manifests/base/clusterclass.yaml" "$CONFIG_REPO/clusters/clusterclass.yaml"
cp "$ROOT/rendered/service-a.yaml" "$CONFIG_REPO/clusters/service-a.yaml"
cp "$ROOT/rendered/loadbalancer.yaml" "$CONFIG_REPO/clusters/loadbalancer.yaml"
for name in service-a loadbalancer; do
  for addon in cert-manager contour storage; do
    cp "$ROOT/rendered/addons/${name}-${addon}.yaml" "$CONFIG_REPO/clusters/${name}-${addon}.yaml"
  done
done
cp "$ROOT/gitops/repository-template/workloads/demo/"*.yaml "$CONFIG_REPO/workloads/demo/"

python3 - "$CONFIG_REPO/clusters" "$CONFIG_REPO/workloads" <<'PY'
from pathlib import Path
import sys,yaml
sensitive_keys={'password','token','client-key-data','client-certificate-data','application_credential_secret'}
def inspect(value,path):
    if isinstance(value,dict):
        for key,item in value.items():
            key_text=str(key).lower()
            if key_text in sensitive_keys:
                raise SystemExit(f"ERROR: sensitive key {key!r} found in {path}")
            inspect(item,path)
    elif isinstance(value,list):
        for item in value: inspect(item,path)
for root in map(Path,sys.argv[1:]):
    for path in root.rglob('*.yaml'):
        for obj in yaml.safe_load_all(path.read_text()):
            if not obj: continue
            if obj.get('kind') == 'Secret':
                raise SystemExit(f"ERROR: Secret object is forbidden in the GitOps repository: {path}")
            if 'clouds.yaml' in path.read_text().lower():
                raise SystemExit(f"ERROR: clouds.yaml reference found in {path}")
            inspect(obj,path)
print('Repository payload contains no Secret objects or credential fields')
PY

git -C "$CONFIG_REPO" diff --check
git -C "$CONFIG_REPO" status --short -- clusters workloads
