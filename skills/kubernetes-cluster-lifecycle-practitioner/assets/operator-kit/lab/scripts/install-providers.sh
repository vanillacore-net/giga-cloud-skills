#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
KUBECONFIG_FILE=${1:?usage: install-providers.sh KUBECONFIG CONTEXT}
CONTEXT=${2:?missing context}
CURRENT=$(kubectl --kubeconfig "$KUBECONFIG_FILE" config current-context)
[[ "$CURRENT" == "$CONTEXT" ]] || { printf 'current context %s does not match %s\n' "$CURRENT" "$CONTEXT" >&2; exit 2; }
[[ ${CONFIRM_MANAGEMENT_CONTEXT:-} == "$CONTEXT" ]] || { printf 'set CONFIRM_MANAGEMENT_CONTEXT=%s\n' "$CONTEXT" >&2; exit 2; }
[[ $(uname -m) == x86_64 ]] || { printf 'the checked binary lock covers linux amd64 only\n' >&2; exit 2; }
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$ROOT/artifacts"
CLUSTERCTL="$ROOT/artifacts/clusterctl"
readarray -t lock < <(python3 - "$ROOT/VERSIONS.yaml" <<'PY'
import sys,yaml
v=yaml.safe_load(open(sys.argv[1]))
print(v['cluster_api'])
print(v['openstack_provider'])
print(v['openstack_resource_controller']['version'])
print(v['clusterctl']['linux_amd64_sha256'])
print(v['openstack_resource_controller']['install_sha256'])
print(v['openstack_provider_components_sha256'])
print(v['cert_manager'])
print(v['cert_manager_manifest_sha256'])
PY
)
CAPI=${lock[0]}; CAPO=${lock[1]}; ORC=${lock[2]}
curl -fsSL "https://github.com/kubernetes-sigs/cluster-api/releases/download/$CAPI/clusterctl-linux-amd64" -o "$TMP/clusterctl"
printf '%s  %s\n' "${lock[3]}" "$TMP/clusterctl" | sha256sum -c -
chmod 0755 "$TMP/clusterctl"
mv "$TMP/clusterctl" "$CLUSTERCTL"
curl -fsSL "https://github.com/k-orc/openstack-resource-controller/releases/download/$ORC/install.yaml" -o "$TMP/orc-install.yaml"
printf '%s  %s\n' "${lock[4]}" "$TMP/orc-install.yaml" | sha256sum -c -
curl -fsSL "https://github.com/kubernetes-sigs/cluster-api-provider-openstack/releases/download/$CAPO/infrastructure-components.yaml" -o "$TMP/capo-components.yaml"
printf '%s  %s\n' "${lock[5]}" "$TMP/capo-components.yaml" | sha256sum -c -
CERT_MANAGER_MANIFEST="$ROOT/addons/cert-manager/${lock[6]}.yaml"
printf '%s  %s\n' "${lock[7]}" "$CERT_MANAGER_MANIFEST" | sha256sum -c -
printf 'cert-manager:\n  url: "%s"\n  version: "%s"\n' \
  "$CERT_MANAGER_MANIFEST" "${lock[6]}" > "$TMP/clusterctl.yaml"
"$CLUSTERCTL" version -o short
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" apply -f "$TMP/orc-install.yaml"
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" wait --for=condition=Established --timeout=3m crd/images.openstack.k-orc.cloud
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" -n orc-system rollout status deployment/orc-controller-manager --timeout=5m
export CLUSTER_TOPOLOGY=true
"$CLUSTERCTL" init --config "$TMP/clusterctl.yaml" \
  --kubeconfig "$KUBECONFIG_FILE" --kubeconfig-context "$CONTEXT" \
  --core "cluster-api:$CAPI" \
  --bootstrap "kubeadm:$CAPI" \
  --control-plane "kubeadm:$CAPI" \
  --infrastructure "openstack:$CAPO"
for namespace in cert-manager capi-system capi-kubeadm-bootstrap-system capi-kubeadm-control-plane-system capo-system; do
  readarray -t deployments < <(kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" -n "$namespace" get deployment -o name)
  (( ${#deployments[@]} > 0 )) || { printf 'no provider deployment found in %s\n' "$namespace" >&2; exit 3; }
  for deployment in "${deployments[@]}"; do
    kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" -n "$namespace" rollout status "$deployment" --timeout=10m
  done
done
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" get providers -A -o wide
