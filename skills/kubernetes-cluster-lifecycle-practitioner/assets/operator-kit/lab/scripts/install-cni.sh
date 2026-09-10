#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CHILD_KUBECONFIG=${1:?usage: install-cni.sh CHILD_KUBECONFIG POD_CIDR}
POD_CIDR=${2:?missing pod CIDR}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
readarray -t lock < <(python3 - "$ROOT/VERSIONS.yaml" <<'PY'
import sys,yaml
v=yaml.safe_load(open(sys.argv[1]))['calico']
print(v['version']); print(v['operator_manifest_sha256'])
PY
)
curl -fsSL "https://raw.githubusercontent.com/projectcalico/calico/${lock[0]}/manifests/tigera-operator.yaml" -o "$TMP/tigera-operator.yaml"
printf '%s  %s\n' "${lock[1]}" "$TMP/tigera-operator.yaml" | sha256sum -c -
kubectl --kubeconfig "$CHILD_KUBECONFIG" apply -f "$TMP/tigera-operator.yaml"
cat > "$TMP/custom-resources.yaml" <<EOF
apiVersion: operator.tigera.io/v1
kind: Installation
metadata:
  name: default
spec:
  calicoNetwork:
    ipPools:
      - blockSize: 26
        cidr: $POD_CIDR
        encapsulation: VXLAN
        natOutgoing: Enabled
        nodeSelector: all()
---
apiVersion: operator.tigera.io/v1
kind: APIServer
metadata:
  name: default
spec: {}
EOF
kubectl --kubeconfig "$CHILD_KUBECONFIG" wait --for=condition=Established --timeout=3m crd/installations.operator.tigera.io
kubectl --kubeconfig "$CHILD_KUBECONFIG" apply -f "$TMP/custom-resources.yaml"
kubectl --kubeconfig "$CHILD_KUBECONFIG" wait --for=condition=Ready node --all --timeout=15m
kubectl --kubeconfig "$CHILD_KUBECONFIG" get nodes -o wide
