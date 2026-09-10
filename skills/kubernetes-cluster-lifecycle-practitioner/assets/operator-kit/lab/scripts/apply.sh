#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CONTRACT=${1:?usage: apply.sh CONTRACT KUBECONFIG CONTEXT loadbalancer|service-a|all [OUTPUT_DIR]}
KUBECONFIG_FILE=${2:?missing kubeconfig}
CONTEXT=${3:?missing context}
TARGET=${4:?choose loadbalancer, service-a or all}
OUTPUT=${5:-$ROOT/rendered}
[[ "$TARGET" =~ ^(loadbalancer|service-a|all)$ ]] || { printf 'target must be loadbalancer, service-a or all\n' >&2; exit 2; }
CURRENT=$(kubectl --kubeconfig "$KUBECONFIG_FILE" config current-context)
[[ "$CURRENT" == "$CONTEXT" ]] || { printf 'current context %s does not match %s\n' "$CURRENT" "$CONTEXT" >&2; exit 2; }
[[ ${CONFIRM_MANAGEMENT_CONTEXT:-} == "$CONTEXT" ]] || { printf 'set CONFIRM_MANAGEMENT_CONTEXT=%s\n' "$CONTEXT" >&2; exit 2; }
"$ROOT/scripts/validate-manifests.sh" "$CONTRACT" "$KUBECONFIG_FILE" "$CONTEXT" "$OUTPUT"
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" create namespace capi-lab-blueprints --dry-run=client -o yaml | kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" apply -f - >/dev/null
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" apply -f "$ROOT/manifests/base/clusterclass.yaml"
if [[ "$TARGET" == all ]]; then manifests=("$OUTPUT/loadbalancer.yaml" "$OUTPUT/service-a.yaml"); else manifests=("$OUTPUT/$TARGET.yaml"); fi
for manifest in "${manifests[@]}"; do
  namespace=$(python3 - "$manifest" <<'PY'
import sys,yaml
print(yaml.safe_load(open(sys.argv[1]))['metadata']['namespace'])
PY
)
  kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" create namespace "$namespace" --dry-run=client -o yaml | kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" apply -f - >/dev/null
  addon_prefix="$OUTPUT/addons/$(basename "${manifest%.yaml}")"
  kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" apply -f "$addon_prefix-cert-manager.yaml"
  kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" apply -f "$addon_prefix-contour.yaml"
  kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" apply -f "$addon_prefix-storage.yaml"
  kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" apply -f "$manifest"
done
