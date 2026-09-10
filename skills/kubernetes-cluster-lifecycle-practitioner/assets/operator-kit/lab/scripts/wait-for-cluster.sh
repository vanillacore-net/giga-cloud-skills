#!/usr/bin/env bash
set -euo pipefail
KUBECONFIG_FILE=${1:?usage: wait-for-cluster.sh KUBECONFIG CONTEXT NAMESPACE CLUSTER [TIMEOUT]}
CONTEXT=${2:?missing context}
NAMESPACE=${3:?missing namespace}
CLUSTER=${4:?missing cluster}
TIMEOUT=${5:-30m}
if ! kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" -n "$NAMESPACE" wait \
  --for=condition=Available "cluster/$CLUSTER" --timeout="$TIMEOUT"; then
  printf 'Cluster %s/%s did not reach Available before %s; showing management-cluster diagnostics.\n' \
    "$NAMESPACE" "$CLUSTER" "$TIMEOUT" >&2
  kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" -n "$NAMESPACE" get \
    cluster,machine,machinedeployment,kubeadmcontrolplane -o wide >&2 || true
  kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" -n "$NAMESPACE" get \
    openstackcluster,openstackmachine -o wide >&2 || true
  exit 1
fi
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" -n "$NAMESPACE" get \
  cluster,machine,machinedeployment,kubeadmcontrolplane -o wide
printf 'Cluster %s/%s reached Available; OpenStack state and child Node readiness were not checked.\n' \
  "$NAMESPACE" "$CLUSTER"
