#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
KUBECONFIG_FILE=${1:?usage: install-management-ingress.sh KUBECONFIG CONTEXT}
CONTEXT=${2:?missing context}
CURRENT=$(kubectl --kubeconfig "$KUBECONFIG_FILE" config current-context)
[[ "$CURRENT" == "$CONTEXT" ]] || { printf 'current context %s does not match %s\n' "$CURRENT" "$CONTEXT" >&2; exit 2; }
[[ ${CONFIRM_MANAGEMENT_CONTEXT:-} == "$CONTEXT" ]] || { printf 'set CONFIRM_MANAGEMENT_CONTEXT=%s\n' "$CONTEXT" >&2; exit 2; }

# clusterctl already owns cert-manager on this cluster. Verify it; do not install a second copy.
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" \
  -n cert-manager rollout status deployment/cert-manager --timeout=5m

MANIFEST="$ROOT/addons/contour/v1.33.7.yaml"
EXPECTED=$(python3 - "$ROOT/VERSIONS.yaml" <<'PY'
import sys,yaml
print(yaml.safe_load(open(sys.argv[1]))['contour']['manifest_sha256'])
PY
)
printf '%s  %s\n' "$EXPECTED" "$MANIFEST" | sha256sum -c -
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" \
  apply --server-side -f "$MANIFEST"
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" \
  -n projectcontour rollout status deployment/contour --timeout=5m
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" \
  -n projectcontour rollout status daemonset/envoy --timeout=5m
SERVICE_TYPE=$(kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" \
  -n projectcontour get service/envoy -o jsonpath='{.spec.type}')
PUBLIC_INGRESS=$(kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" \
  -n projectcontour get service/envoy -o jsonpath='{.status.loadBalancer.ingress}')
[[ "$SERVICE_TYPE" == ClusterIP && -z "$PUBLIC_INGRESS" ]] || {
  printf 'management Envoy must remain private: type=%s loadBalancer.ingress=%s\n' \
    "$SERVICE_TYPE" "$PUBLIC_INGRESS" >&2
  exit 3
}