#!/usr/bin/env bash
set -euo pipefail
KUBECONFIG_FILE=${1:?usage: wait-for-cluster-absence.sh KUBECONFIG CONTEXT NAMESPACE CLUSTER [TIMEOUT_SECONDS]}
CONTEXT=${2:?missing context}
NAMESPACE=${3:?missing namespace}
CLUSTER=${4:?missing cluster}
TIMEOUT=${5:-1800}
deadline=$(( $(date +%s) + TIMEOUT ))
while true; do
  error=$(mktemp)
  if kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" -n "$NAMESPACE" get cluster "$CLUSTER" -o name >/dev/null 2>"$error"; then
    rm -f "$error"
  elif grep -Eqi 'not found|NotFound' "$error"; then
    rm -f "$error"
    printf 'cluster %s/%s is absent from the management API\n' "$NAMESPACE" "$CLUSTER"
    exit 0
  else
    printf 'management API check failed: ' >&2
    python3 - "$error" <<'PY'
import sys
print(open(sys.argv[1]).read().strip())
PY
    rm -f "$error"
    exit 4
  fi
  if (( $(date +%s) >= deadline )); then
    printf 'timed out waiting for cluster %s/%s deletion\n' "$NAMESPACE" "$CLUSTER" >&2
    kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" -n "$NAMESPACE" get cluster "$CLUSTER" -o yaml >&2
    exit 3
  fi
  sleep 10
done
