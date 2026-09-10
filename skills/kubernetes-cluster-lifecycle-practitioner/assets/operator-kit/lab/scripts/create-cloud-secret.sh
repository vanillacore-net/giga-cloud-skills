#!/usr/bin/env bash
set -euo pipefail
KUBECONFIG_FILE=${1:?usage: create-cloud-secret.sh KUBECONFIG CONTEXT NAMESPACE SECRET_NAME CLOUDS_YAML [CACERT]}
CONTEXT=${2:?missing context}
NAMESPACE=${3:?missing namespace}
SECRET_NAME=${4:?missing secret name}
CLOUDS_YAML=${5:?missing clouds.yaml path}
CACERT=${6:-}
CURRENT=$(kubectl --kubeconfig "$KUBECONFIG_FILE" config current-context)
[[ "$CURRENT" == "$CONTEXT" ]] || { printf 'current context %s does not match %s\n' "$CURRENT" "$CONTEXT" >&2; exit 2; }
[[ ${CONFIRM_MANAGEMENT_CONTEXT:-} == "$CONTEXT" ]] || { printf 'set CONFIRM_MANAGEMENT_CONTEXT=%s\n' "$CONTEXT" >&2; exit 2; }
[[ -f "$CLOUDS_YAML" ]] || { printf 'clouds.yaml not found\n' >&2; exit 2; }
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" apply -f - >/dev/null
args=(--from-file=clouds.yaml="$CLOUDS_YAML")
[[ -n "$CACERT" ]] && args+=(--from-file=cacert="$CACERT")
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" -n "$NAMESPACE" create secret generic "$SECRET_NAME" "${args[@]}" --dry-run=client -o yaml | kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" apply -f - >/dev/null
printf 'credential secret %s/%s applied without printing its content\n' "$NAMESPACE" "$SECRET_NAME"
