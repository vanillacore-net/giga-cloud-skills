#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
KUBECONFIG_FILE=${1:?usage: cleanup.sh KUBECONFIG CONTEXT NAMESPACE CLUSTER RESOURCE_IDS_JSON OS_CLOUD}
CONTEXT=${2:?missing context}
NAMESPACE=${3:?missing namespace}
CLUSTER=${4:?missing cluster}
RECORD=${5:?missing resource ID record}
OS_CLOUD_NAME=${6:?missing OS_CLOUD}
[[ "$CLUSTER" =~ ^(service-a|loadbalancer)$ ]] || { printf 'cleanup is limited to the disposable service-a and loadbalancer clusters\n' >&2; exit 2; }
[[ ${CONFIRM_MANAGEMENT_CONTEXT:-} == "$CONTEXT" ]] || { printf 'set CONFIRM_MANAGEMENT_CONTEXT=%s\n' "$CONTEXT" >&2; exit 2; }
[[ ${CONFIRM_DELETE_CLUSTER:-} == "$NAMESPACE/$CLUSTER" ]] || { printf 'set CONFIRM_DELETE_CLUSTER=%s/%s\n' "$NAMESPACE" "$CLUSTER" >&2; exit 2; }
[[ -s "$RECORD" ]] || { printf 'capture the OpenStack resource IDs before deletion\n' >&2; exit 2; }
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" -n "$NAMESPACE" delete cluster "$CLUSTER"
"$ROOT/scripts/wait-for-cluster-absence.sh" "$KUBECONFIG_FILE" "$CONTEXT" "$NAMESPACE" "$CLUSTER"
"$ROOT/scripts/verify-openstack-absence.sh" "$RECORD" "$OS_CLOUD_NAME"
