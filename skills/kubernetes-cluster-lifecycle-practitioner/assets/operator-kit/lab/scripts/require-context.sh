#!/usr/bin/env bash
set -euo pipefail
KUBECONFIG_FILE=${1:?usage: require-context.sh KUBECONFIG CONTEXT}
EXPECTED_CONTEXT=${2:?missing expected context}
[ -r "$KUBECONFIG_FILE" ] || { printf 'ERROR: kubeconfig is not readable: %s\n' "$KUBECONFIG_FILE" >&2; exit 2; }
ACTUAL_CONTEXT=$(kubectl --kubeconfig "$KUBECONFIG_FILE" config current-context)
[ "$ACTUAL_CONTEXT" = "$EXPECTED_CONTEXT" ] || {
  printf 'ERROR: kubeconfig current context is %s, expected %s\n' "$ACTUAL_CONTEXT" "$EXPECTED_CONTEXT" >&2
  exit 2
}
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$EXPECTED_CONTEXT" auth can-i get pods --namespace kube-system >/dev/null
