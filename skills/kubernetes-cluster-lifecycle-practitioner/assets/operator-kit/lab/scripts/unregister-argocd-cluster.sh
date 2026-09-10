#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
MGMT_KUBECONFIG=${1:?usage: unregister-argocd-cluster.sh MGMT_KUBECONFIG MGMT_CONTEXT CHILD_KUBECONFIG CHILD_CONTEXT NAME [NAMESPACE]}
MGMT_CONTEXT=${2:?missing management context}
CHILD_KUBECONFIG=${3:?missing child kubeconfig}
CHILD_CONTEXT=${4:?missing child context}
NAME=${5:?missing registration name}
NAMESPACE=${6:-workload-demo}
[ "${CONFIRM_ARGOCD_UNREGISTER:-}" = "$NAME" ] || { echo "ERROR: run with CONFIRM_ARGOCD_UNREGISTER=$NAME" >&2; exit 2; }
"$ROOT/scripts/require-context.sh" "$MGMT_KUBECONFIG" "$MGMT_CONTEXT"
"$ROOT/scripts/require-context.sh" "$CHILD_KUBECONFIG" "$CHILD_CONTEXT"

kubectl --kubeconfig "$CHILD_KUBECONFIG" --context "$CHILD_CONTEXT" -n "$NAMESPACE" \
  delete rolebinding/argocd-chapter-4-manager role/argocd-chapter-4-manager --ignore-not-found
kubectl --kubeconfig "$CHILD_KUBECONFIG" --context "$CHILD_CONTEXT" -n kube-system \
  delete secret/argocd-chapter-4-token serviceaccount/argocd-chapter-4 --ignore-not-found
kubectl --kubeconfig "$MGMT_KUBECONFIG" --context "$MGMT_CONTEXT" -n argocd \
  delete secret "cluster-${NAME}" --ignore-not-found
