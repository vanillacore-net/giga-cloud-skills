#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CONTRACT=${1:?usage: verify-hub-spoke.sh HUB_SPOKE_CONTRACT}

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
if c.get('example_only') is not False: errors.append('example contract cannot drive a path test')
if c.get('execution_approved') is not True: errors.append('execution_approved must be true')
paths=[
 'source.cluster','source.kubeconfig','source.context','source.api_server','source.namespace',
 'destination.cluster','destination.kubeconfig','destination.context','destination.api_server',
 'destination.envoy_service.namespace','destination.envoy_service.name',
 'destination.ingress.namespace','destination.ingress.name','destination.ingress.class',
 'destination.ingress.host','destination.ingress.path','destination.ingress.backend_service',
 'destination.expected_status','network_contract.edge_entry','network_contract.transit_route',
 'network_contract.return_route','network_contract.policy_reference','network_contract.dns_requirement',
 'network_contract.mtu_requirement','status.evidence_file'
]
result=[get(path) for path in paths]
if errors: raise SystemExit('\n'.join(dict.fromkeys(errors)))
for value in result: print(value)
PY
)
SRC_CLUSTER=${values[0]}; SRC_KUBECONFIG=${values[1]}; SRC_CONTEXT=${values[2]}; SRC_API=${values[3]}; SRC_NAMESPACE=${values[4]}
DST_CLUSTER=${values[5]}; DST_KUBECONFIG=${values[6]}; DST_CONTEXT=${values[7]}; DST_API=${values[8]}
ENVOY_NAMESPACE=${values[9]}; ENVOY_SERVICE=${values[10]}
INGRESS_NAMESPACE=${values[11]}; INGRESS_NAME=${values[12]}; INGRESS_CLASS=${values[13]}
HOST_HEADER=${values[14]}; REQUEST_PATH=${values[15]}; BACKEND_SERVICE=${values[16]}; EXPECTED=${values[17]}

"$ROOT/scripts/require-context.sh" "$SRC_KUBECONFIG" "$SRC_CONTEXT"
"$ROOT/scripts/require-context.sh" "$DST_KUBECONFIG" "$DST_CONTEXT"
ACTUAL_SRC_API=$(kubectl --kubeconfig "$SRC_KUBECONFIG" --context "$SRC_CONTEXT" \
  config view --minify -o jsonpath='{.clusters[0].cluster.server}')
ACTUAL_DST_API=$(kubectl --kubeconfig "$DST_KUBECONFIG" --context "$DST_CONTEXT" \
  config view --minify -o jsonpath='{.clusters[0].cluster.server}')
[[ "$ACTUAL_SRC_API" == "$SRC_API" ]] || { printf 'source API server is %s, expected %s\n' "$ACTUAL_SRC_API" "$SRC_API" >&2; exit 2; }
[[ "$ACTUAL_DST_API" == "$DST_API" ]] || { printf 'destination API server is %s, expected %s\n' "$ACTUAL_DST_API" "$DST_API" >&2; exit 2; }
EXPECTED_CONFIRMATION="${SRC_CLUSTER}/${SRC_CONTEXT}->${DST_CLUSTER}/${DST_CONTEXT}"
[[ ${CONFIRM_PATH_TEST:-} == "$EXPECTED_CONFIRMATION" ]] || {
  printf 'set CONFIRM_PATH_TEST=%q after reviewing both confirmed targets and the network contract\n' \
    "$EXPECTED_CONFIRMATION" >&2
  exit 2
}

SERVICE_TYPE=$(kubectl --kubeconfig "$DST_KUBECONFIG" --context "$DST_CONTEXT" \
  -n "$ENVOY_NAMESPACE" get "service/$ENVOY_SERVICE" -o jsonpath='{.spec.type}')
PUBLIC_INGRESS=$(kubectl --kubeconfig "$DST_KUBECONFIG" --context "$DST_CONTEXT" \
  -n "$ENVOY_NAMESPACE" get "service/$ENVOY_SERVICE" -o jsonpath='{.status.loadBalancer.ingress}')
ADDRESS=$(kubectl --kubeconfig "$DST_KUBECONFIG" --context "$DST_CONTEXT" \
  -n "$ENVOY_NAMESPACE" get "service/$ENVOY_SERVICE" -o jsonpath='{.spec.clusterIP}')
[[ "$SERVICE_TYPE" == ClusterIP && -z "$PUBLIC_INGRESS" && -n "$ADDRESS" && "$ADDRESS" != None ]] || {
  printf 'destination Envoy is not a private ClusterIP: type=%s address=%s loadBalancer.ingress=%s\n' \
    "$SERVICE_TYPE" "$ADDRESS" "$PUBLIC_INGRESS" >&2
  exit 3
}

ACTUAL_CLASS=$(kubectl --kubeconfig "$DST_KUBECONFIG" --context "$DST_CONTEXT" \
  -n "$INGRESS_NAMESPACE" get "ingress/$INGRESS_NAME" -o jsonpath='{.spec.ingressClassName}')
ACTUAL_HOST=$(kubectl --kubeconfig "$DST_KUBECONFIG" --context "$DST_CONTEXT" \
  -n "$INGRESS_NAMESPACE" get "ingress/$INGRESS_NAME" -o jsonpath='{.spec.rules[0].host}')
ACTUAL_BACKEND=$(kubectl --kubeconfig "$DST_KUBECONFIG" --context "$DST_CONTEXT" \
  -n "$INGRESS_NAMESPACE" get "ingress/$INGRESS_NAME" -o jsonpath='{.spec.rules[0].http.paths[0].backend.service.name}')
[[ "$ACTUAL_CLASS" == "$INGRESS_CLASS" && "$ACTUAL_HOST" == "$HOST_HEADER" && "$ACTUAL_BACKEND" == "$BACKEND_SERVICE" ]] || {
  printf 'destination Ingress does not match the approved class, host and backend\n' >&2
  exit 3
}
URL="http://${ADDRESS}${REQUEST_PATH}"

kubectl --kubeconfig "$SRC_KUBECONFIG" --context "$SRC_CONTEXT" \
  create namespace "$SRC_NAMESPACE" --dry-run=client -o yaml | \
  kubectl --kubeconfig "$SRC_KUBECONFIG" --context "$SRC_CONTEXT" apply -f - >/dev/null
status=$(kubectl --kubeconfig "$SRC_KUBECONFIG" --context "$SRC_CONTEXT" \
  -n "$SRC_NAMESPACE" run chapter4-source-probe \
  --rm -i --quiet --restart=Never --image=curlimages/curl:8.12.1 \
  --command -- curl -sS --max-time 15 -H "Host: $HOST_HEADER" -o /dev/null -w '%{http_code}' "$URL")
[[ "$status" == "$EXPECTED" ]] || { printf 'path test returned HTTP %s, expected %s\n' "$status" "$EXPECTED" >&2; exit 3; }
printf 'PathReady: %s/%s -> %s/%s via private Envoy %s, HTTP %s\n' \
  "$SRC_CLUSTER" "$SRC_CONTEXT" "$DST_CLUSTER" "$DST_CONTEXT" "$ADDRESS" "$status"
