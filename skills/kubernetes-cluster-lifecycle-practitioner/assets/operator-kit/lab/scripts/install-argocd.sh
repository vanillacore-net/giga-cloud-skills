#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
KUBECONFIG_FILE=${1:?usage: install-argocd.sh MGMT_KUBECONFIG MGMT_CONTEXT}
CONTEXT=${2:?missing management context}
VERSIONS=${VERSIONS_FILE:-$ROOT/VERSIONS.yaml}

"$ROOT/scripts/require-context.sh" "$KUBECONFIG_FILE" "$CONTEXT"

readarray -t ARGO < <(python3 - "$VERSIONS" <<'PY'
import sys,yaml
v=yaml.safe_load(open(sys.argv[1]))['argocd']
print(v['version'])
print(v['install_manifest_sha256'])
print(v['linux_amd64_sha256'])
PY
)
VERSION=${ARGO[0]}
MANIFEST_SHA=${ARGO[1]}
CLI_SHA=${ARGO[2]}
DOWNLOAD_DIR="$ROOT/artifacts/downloads"
BIN_DIR="$ROOT/artifacts/bin"
mkdir -p "$DOWNLOAD_DIR" "$BIN_DIR"
chmod 700 "$ROOT/artifacts" "$DOWNLOAD_DIR" "$BIN_DIR"
MANIFEST="$DOWNLOAD_DIR/argocd-install-${VERSION}.yaml"
CLI="$BIN_DIR/argocd"

curl --fail --location --proto '=https' --tlsv1.2 \
  "https://raw.githubusercontent.com/argoproj/argo-cd/${VERSION}/manifests/install.yaml" \
  --output "$MANIFEST"
printf '%s  %s\n' "$MANIFEST_SHA" "$MANIFEST" | sha256sum --check --status

curl --fail --location --proto '=https' --tlsv1.2 \
  "https://github.com/argoproj/argo-cd/releases/download/${VERSION}/argocd-linux-amd64" \
  --output "$CLI"
printf '%s  %s\n' "$CLI_SHA" "$CLI" | sha256sum --check --status
chmod 700 "$CLI"

kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" \
  create namespace argocd --dry-run=client -o yaml |
  kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" apply -f -
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" \
  apply --server-side --force-conflicts -n argocd -f "$MANIFEST"
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" \
  -n argocd wait --for=condition=Available deployment --all --timeout=10m
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" \
  -n argocd rollout status statefulset/argocd-application-controller --timeout=10m
"$CLI" version --client
