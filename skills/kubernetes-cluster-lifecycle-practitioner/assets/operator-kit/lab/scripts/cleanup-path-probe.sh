#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
LOADBALANCER_KUBECONFIG=${1:?usage: cleanup-path-probe.sh LOADBALANCER_KUBECONFIG LOADBALANCER_CONTEXT SERVICE_A_KUBECONFIG SERVICE_A_CONTEXT}
LOADBALANCER_CONTEXT=${2:?missing LoadBalancer context}
SERVICE_A_KUBECONFIG=${3:?missing service-a kubeconfig}
SERVICE_A_CONTEXT=${4:?missing service-a context}
"$ROOT/scripts/require-context.sh" "$LOADBALANCER_KUBECONFIG" "$LOADBALANCER_CONTEXT"
"$ROOT/scripts/require-context.sh" "$SERVICE_A_KUBECONFIG" "$SERVICE_A_CONTEXT"
EXPECTED_CONFIRMATION="${LOADBALANCER_CONTEXT}->${SERVICE_A_CONTEXT}"
[[ ${CONFIRM_PATH_TEST_CLEANUP:-} == "$EXPECTED_CONFIRMATION" ]] || {
  printf 'set CONFIRM_PATH_TEST_CLEANUP=%q for the two confirmed contexts\n' \
    "$EXPECTED_CONFIRMATION" >&2
  exit 2
}
kubectl --kubeconfig "$LOADBALANCER_KUBECONFIG" --context "$LOADBALANCER_CONTEXT" \
  delete namespace chapter4-path-test --ignore-not-found --wait=true
kubectl --kubeconfig "$SERVICE_A_KUBECONFIG" --context "$SERVICE_A_CONTEXT" \
  delete namespace chapter4-path-test --ignore-not-found --wait=true
