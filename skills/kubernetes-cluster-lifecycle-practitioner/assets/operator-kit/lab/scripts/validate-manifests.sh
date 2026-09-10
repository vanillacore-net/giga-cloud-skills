#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CONTRACT=${1:?usage: validate-manifests.sh CONTRACT KUBECONFIG CONTEXT [OUTPUT_DIR]}
KUBECONFIG_FILE=${2:?usage: validate-manifests.sh CONTRACT KUBECONFIG CONTEXT [OUTPUT_DIR]}
CONTEXT=${3:?usage: validate-manifests.sh CONTRACT KUBECONFIG CONTEXT [OUTPUT_DIR]}
OUTPUT=${4:-$ROOT/rendered}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

"$ROOT/scripts/render-clusters.sh" "$CONTRACT" "$OUTPUT"
python3 - "$ROOT/manifests/base/clusterclass.yaml" "$OUTPUT" "$TMP" <<'PY'
from pathlib import Path
import sys,yaml
base=Path(sys.argv[1]); rendered=Path(sys.argv[2]); target=Path(sys.argv[3])
base_docs=[]
for doc in yaml.safe_load_all(base.read_text()):
 if not doc or doc.get('kind')=='Namespace': continue
 doc.setdefault('metadata',{})['namespace']='default'
 base_docs.append(doc)
(target/'base.yaml').write_text(yaml.safe_dump_all(base_docs,sort_keys=False))
for source in rendered.glob('*.yaml'):
 doc=yaml.safe_load(source.read_text())
 doc['metadata']['namespace']='default'
 doc['spec']['topology']['classRef']['namespace']='default'
 (target/source.name).write_text(yaml.safe_dump(doc,sort_keys=False))
for source in (rendered/'addons').glob('*.yaml'):
 docs=[]
 for doc in yaml.safe_load_all(source.read_text()):
  if not doc: continue
  doc.setdefault('metadata',{})['namespace']='default'
  docs.append(doc)
 (target/source.name).write_text(yaml.safe_dump_all(docs,sort_keys=False))
PY
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" apply \
  --server-side --dry-run=server -f "$TMP/base.yaml" >/dev/null
for manifest in "$TMP"/loadbalancer.yaml "$TMP"/service-a.yaml; do
  kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" apply \
    --server-side --dry-run=server -f "$manifest" >/dev/null
done
for manifest in "$TMP"/loadbalancer-*.yaml "$TMP"/service-a-*.yaml; do
  kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" apply \
    --server-side --dry-run=server -f "$manifest" >/dev/null
done
printf 'server-side manifest schema validation passed using a namespace-neutral temporary copy\n'
