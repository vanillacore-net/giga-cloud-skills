#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
MGMT_KUBECONFIG=${1:?usage: register-argocd-cluster.sh MGMT_KUBECONFIG MGMT_CONTEXT CHILD_KUBECONFIG CHILD_CONTEXT NAME ROLE [NAMESPACE]}
MGMT_CONTEXT=${2:?missing management context}
CHILD_KUBECONFIG=${3:?missing child kubeconfig}
CHILD_CONTEXT=${4:?missing child context}
NAME=${5:?missing registration name}
ROLE=${6:?missing role: workload or edge}
NAMESPACE=${7:-workload-demo}
[[ "$NAME" =~ ^[a-z0-9]([-a-z0-9]*[a-z0-9])?$ ]] || { echo "ERROR: NAME must be a DNS label" >&2; exit 2; }
[[ "$NAMESPACE" =~ ^[a-z0-9]([-a-z0-9]*[a-z0-9])?$ ]] || { echo "ERROR: NAMESPACE must be a DNS label" >&2; exit 2; }
case "$ROLE" in workload) WORKLOADS_ENABLED=true;; edge) WORKLOADS_ENABLED=false;; *) echo "ERROR: ROLE must be workload or edge" >&2; exit 2;; esac
"$ROOT/scripts/require-context.sh" "$MGMT_KUBECONFIG" "$MGMT_CONTEXT"
"$ROOT/scripts/require-context.sh" "$CHILD_KUBECONFIG" "$CHILD_CONTEXT"

REGISTRATION_EXISTED=false
if kubectl --kubeconfig "$MGMT_KUBECONFIG" --context "$MGMT_CONTEXT" -n argocd \
  get secret "cluster-${NAME}" >/dev/null 2>&1; then
  REGISTRATION_EXISTED=true
fi
REGISTRATION_COMMITTED=false
TMP=""
cleanup_on_exit() {
  status=$?
  set +e
  [ -z "$TMP" ] || rm -rf "$TMP"
  if [ "$status" -ne 0 ] && [ "$REGISTRATION_EXISTED" = false ] && [ "$REGISTRATION_COMMITTED" = false ]; then
    kubectl --kubeconfig "$MGMT_KUBECONFIG" --context "$MGMT_CONTEXT" -n argocd \
      delete secret "cluster-${NAME}" --ignore-not-found >/dev/null 2>&1
    kubectl --kubeconfig "$CHILD_KUBECONFIG" --context "$CHILD_CONTEXT" -n "$NAMESPACE" \
      delete rolebinding/argocd-chapter-4-manager role/argocd-chapter-4-manager --ignore-not-found >/dev/null 2>&1
    kubectl --kubeconfig "$CHILD_KUBECONFIG" --context "$CHILD_CONTEXT" -n kube-system \
      delete secret/argocd-chapter-4-token serviceaccount/argocd-chapter-4 --ignore-not-found >/dev/null 2>&1
  fi
  exit "$status"
}
trap cleanup_on_exit EXIT

kubectl --kubeconfig "$CHILD_KUBECONFIG" --context "$CHILD_CONTEXT" \
  create namespace "$NAMESPACE" --dry-run=client -o yaml |
  kubectl --kubeconfig "$CHILD_KUBECONFIG" --context "$CHILD_CONTEXT" apply -f -

cat <<YAML | kubectl --kubeconfig "$CHILD_KUBECONFIG" --context "$CHILD_CONTEXT" apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: argocd-chapter-4
  namespace: kube-system
---
apiVersion: v1
kind: Secret
metadata:
  name: argocd-chapter-4-token
  namespace: kube-system
  annotations:
    kubernetes.io/service-account.name: argocd-chapter-4
type: kubernetes.io/service-account-token
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: argocd-chapter-4-manager
  namespace: ${NAMESPACE}
rules:
  - apiGroups: ["*"]
    resources: ["*"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: argocd-chapter-4-manager
  namespace: ${NAMESPACE}
subjects:
  - kind: ServiceAccount
    name: argocd-chapter-4
    namespace: kube-system
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: argocd-chapter-4-manager
YAML

for _ in $(seq 1 60); do
  TOKEN_B64=$(kubectl --kubeconfig "$CHILD_KUBECONFIG" --context "$CHILD_CONTEXT" \
    -n kube-system get secret argocd-chapter-4-token -o jsonpath='{.data.token}' 2>/dev/null || true)
  [ -n "$TOKEN_B64" ] && break
  sleep 1
done
[ -n "${TOKEN_B64:-}" ] || { echo "ERROR: service-account token was not issued within 60 seconds" >&2; exit 1; }

umask 077
TMP=$(mktemp -d)
kubectl --kubeconfig "$CHILD_KUBECONFIG" --context "$CHILD_CONTEXT" config view \
  --minify --flatten --raw -o json > "$TMP/child.json"
printf '%s' "$TOKEN_B64" | base64 --decode > "$TMP/token"
export ARGO_CLUSTER_NAME="$NAME" ARGO_CLUSTER_ROLE="$ROLE" ARGO_WORKLOADS_ENABLED="$WORKLOADS_ENABLED" ARGO_NAMESPACE="$NAMESPACE"
python3 - "$TMP/child.json" "$TMP/token" "$TMP/registration.yaml" <<'PY'
import base64,json,os,sys,yaml
cfg=json.load(open(sys.argv[1]))
cluster=cfg['clusters'][0]['cluster']
server=cluster['server']
ca=cluster.get('certificate-authority-data')
if not ca:
    raise SystemExit('ERROR: flattened child kubeconfig has no certificate-authority-data')
token=open(sys.argv[2]).read()
config=json.dumps({'bearerToken':token,'tlsClientConfig':{'insecure':False,'caData':ca}},separators=(',',':'))
obj={'apiVersion':'v1','kind':'Secret','metadata':{'name':'cluster-'+os.environ['ARGO_CLUSTER_NAME'],'namespace':'argocd','labels':{'argocd.argoproj.io/secret-type':'cluster','platform.vanillacore.net/role':os.environ['ARGO_CLUSTER_ROLE'],'platform.vanillacore.net/workloads-enabled':os.environ['ARGO_WORKLOADS_ENABLED']}},'stringData':{'name':os.environ['ARGO_CLUSTER_NAME'],'server':server,'namespaces':os.environ['ARGO_NAMESPACE'],'project':'chapter-4-platform','config':config}}
open(sys.argv[3],'w').write(yaml.safe_dump(obj,sort_keys=False))
PY
kubectl --kubeconfig "$MGMT_KUBECONFIG" --context "$MGMT_CONTEXT" apply -f "$TMP/registration.yaml"
kubectl --kubeconfig "$MGMT_KUBECONFIG" --context "$MGMT_CONTEXT" -n argocd \
  get secret "cluster-${NAME}" \
  -l "platform.vanillacore.net/role=${ROLE},platform.vanillacore.net/workloads-enabled=${WORKLOADS_ENABLED}" \
  -o name >/dev/null
REGISTRATION_COMMITTED=true
printf 'registered cluster %s with role=%s and workloads-enabled=%s\n' "$NAME" "$ROLE" "$WORKLOADS_ENABLED"
