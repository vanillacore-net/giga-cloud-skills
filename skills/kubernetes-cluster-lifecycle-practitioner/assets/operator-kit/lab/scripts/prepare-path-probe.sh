#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CONTRACT=${1:?usage: prepare-path-probe.sh HUB_SPOKE_CONTRACT}
readarray -t values < <(python3 - "$CONTRACT" <<'PY'
import sys,yaml
c=yaml.safe_load(open(sys.argv[1]))
errors=[]
def get(path):
    value=c
    for part in path.split('.'):
        if not isinstance(value,dict) or part not in value:
            errors.append(f'missing {path}')
            return ''
        value=value[part]
    if value in (None,'') or (isinstance(value,str) and 'REPLACE_' in value):
        errors.append(f'unresolved {path}')
    return value
for path in (
    'destination.cluster','destination.kubeconfig','destination.context','destination.api_server',
    'destination.envoy_service.namespace','destination.envoy_service.name',
    'destination.ingress.namespace','destination.ingress.host','destination.ingress.path'
):
    print(get(path))
if errors: raise SystemExit('\n'.join(dict.fromkeys(errors)))
PY
)
SPOKE_CLUSTER=${values[0]}; SPOKE_KUBECONFIG=${values[1]}; SPOKE_CONTEXT=${values[2]}; EXPECTED_API=${values[3]}
ENVOY_NAMESPACE=${values[4]}; ENVOY_SERVICE=${values[5]}; INGRESS_NAMESPACE=${values[6]}; HOST=${values[7]}; REQUEST_PATH=${values[8]}
"$ROOT/scripts/require-context.sh" "$SPOKE_KUBECONFIG" "$SPOKE_CONTEXT"
ACTUAL_API=$(kubectl --kubeconfig "$SPOKE_KUBECONFIG" --context "$SPOKE_CONTEXT" \
  config view --minify -o jsonpath='{.clusters[0].cluster.server}')
[[ "$ACTUAL_API" == "$EXPECTED_API" ]] || {
  printf 'destination API server is %s, expected %s\n' "$ACTUAL_API" "$EXPECTED_API" >&2
  exit 2
}
EXPECTED_CONFIRMATION="${SPOKE_CLUSTER}/${SPOKE_CONTEXT}"
[[ ${CONFIRM_PATH_DESTINATION:-} == "$EXPECTED_CONFIRMATION" ]] || {
  printf 'set CONFIRM_PATH_DESTINATION=%q after reviewing the bound destination\n' \
    "$EXPECTED_CONFIRMATION" >&2
  exit 2
}
kubectl --kubeconfig "$SPOKE_KUBECONFIG" --context "$SPOKE_CONTEXT" apply \
  -f "$ROOT/manifests/probe/destination.yaml"
kubectl --kubeconfig "$SPOKE_KUBECONFIG" --context "$SPOKE_CONTEXT" \
  -n "$INGRESS_NAMESPACE" rollout status deployment/destination --timeout=5m
kubectl --kubeconfig "$SPOKE_KUBECONFIG" --context "$SPOKE_CONTEXT" \
  -n projectcontour rollout status deployment/contour --timeout=5m
kubectl --kubeconfig "$SPOKE_KUBECONFIG" --context "$SPOKE_CONTEXT" \
  -n projectcontour rollout status daemonset/envoy --timeout=5m
SERVICE_TYPE=$(kubectl --kubeconfig "$SPOKE_KUBECONFIG" --context "$SPOKE_CONTEXT" \
  -n "$ENVOY_NAMESPACE" get "service/$ENVOY_SERVICE" -o jsonpath='{.spec.type}')
PUBLIC_INGRESS=$(kubectl --kubeconfig "$SPOKE_KUBECONFIG" --context "$SPOKE_CONTEXT" \
  -n "$ENVOY_NAMESPACE" get "service/$ENVOY_SERVICE" -o jsonpath='{.status.loadBalancer.ingress}')
ADDRESS=$(kubectl --kubeconfig "$SPOKE_KUBECONFIG" --context "$SPOKE_CONTEXT" \
  -n "$ENVOY_NAMESPACE" get "service/$ENVOY_SERVICE" -o jsonpath='{.spec.clusterIP}')
[[ "$SERVICE_TYPE" == ClusterIP && -z "$PUBLIC_INGRESS" ]] || {
  printf 'workload Envoy must remain private: type=%s loadBalancer.ingress=%s\n' \
    "$SERVICE_TYPE" "$PUBLIC_INGRESS" >&2
  exit 3
}
status=$(kubectl --kubeconfig "$SPOKE_KUBECONFIG" --context "$SPOKE_CONTEXT" \
  -n "$INGRESS_NAMESPACE" run chapter4-local-ingress-probe \
  --rm -i --quiet --restart=Never --image=curlimages/curl:8.12.1 \
  --command -- curl -sS --max-time 15 -H "Host: $HOST" -o /dev/null -w '%{http_code}' \
  "http://${ADDRESS}${REQUEST_PATH}")
[[ "$status" == 200 ]] || { printf 'workload ingress returned HTTP %s, expected 200\n' "$status" >&2; exit 3; }
printf 'WorkloadIngressReady: %s/%s via private Envoy %s, HTTP %s\n' \
  "$SPOKE_CLUSTER" "$SPOKE_CONTEXT" "$ADDRESS" "$status"
