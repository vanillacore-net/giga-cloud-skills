#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
MGMT_KUBECONFIG=${1:?usage: verify-management-api-path.sh MGMT_KUBECONFIG MGMT_CONTEXT CHILD_KUBECONFIG CHILD_NAME}
MGMT_CONTEXT=${2:?missing management context}
CHILD_KUBECONFIG=${3:?missing child kubeconfig}
CHILD_NAME=${4:?missing child name}
[[ "$CHILD_NAME" =~ ^[a-z0-9]([-a-z0-9]*[a-z0-9])?$ ]] || { echo "ERROR: CHILD_NAME must be a DNS label" >&2; exit 2; }
[ "${CONFIRM_MANAGEMENT_PATH_TEST:-}" = yes ] || { echo "ERROR: run with CONFIRM_MANAGEMENT_PATH_TEST=yes" >&2; exit 2; }
"$ROOT/scripts/require-context.sh" "$MGMT_KUBECONFIG" "$MGMT_CONTEXT"

umask 077
TMP=$(mktemp -d)
NS="chapter4-control-probe-${CHILD_NAME}"
cleanup() {
  kubectl --kubeconfig "$MGMT_KUBECONFIG" --context "$MGMT_CONTEXT" delete namespace "$NS" --ignore-not-found --wait=false >/dev/null 2>&1 || true
  rm -rf "$TMP"
}
trap cleanup EXIT
kubectl --kubeconfig "$CHILD_KUBECONFIG" config view --minify --flatten --raw -o json > "$TMP/child.json"
python3 - "$TMP/child.json" "$TMP" <<'PY'
import base64,json,sys
cfg=json.load(open(sys.argv[1])); out=sys.argv[2]
c=cfg['clusters'][0]['cluster']; u=cfg['users'][0]['user']
required={'ca.crt':c.get('certificate-authority-data'),'client.crt':u.get('client-certificate-data'),'client.key':u.get('client-key-data')}
missing=[k for k,v in required.items() if not v]
if missing: raise SystemExit('ERROR: flattened child kubeconfig lacks '+', '.join(missing))
for name,value in required.items(): open(out+'/'+name,'wb').write(base64.b64decode(value))
open(out+'/server','w').write(c['server'])
PY
SERVER=$(<"$TMP/server")

kubectl --kubeconfig "$MGMT_KUBECONFIG" --context "$MGMT_CONTEXT" create namespace "$NS"
kubectl --kubeconfig "$MGMT_KUBECONFIG" --context "$MGMT_CONTEXT" -n "$NS" create secret generic child-api-client \
  --from-file=ca.crt="$TMP/ca.crt" --from-file=client.crt="$TMP/client.crt" --from-file=client.key="$TMP/client.key"
cat <<YAML | kubectl --kubeconfig "$MGMT_KUBECONFIG" --context "$MGMT_CONTEXT" apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: readyz-probe
  namespace: ${NS}
spec:
  restartPolicy: Never
  containers:
    - name: curl
      image: curlimages/curl:8.12.1
      command: ["curl"]
      args: ["--fail", "--silent", "--show-error", "--cacert", "/credentials/ca.crt", "--cert", "/credentials/client.crt", "--key", "/credentials/client.key", "${SERVER}/readyz"]
      volumeMounts:
        - name: credentials
          mountPath: /credentials
          readOnly: true
  volumes:
    - name: credentials
      secret:
        secretName: child-api-client
YAML
kubectl --kubeconfig "$MGMT_KUBECONFIG" --context "$MGMT_CONTEXT" -n "$NS" \
  wait pod/readyz-probe --for=jsonpath='{.status.phase}'=Succeeded --timeout=3m
RESULT=$(kubectl --kubeconfig "$MGMT_KUBECONFIG" --context "$MGMT_CONTEXT" -n "$NS" logs readyz-probe)
[ "$RESULT" = ok ] || { echo "ERROR: child /readyz returned unexpected body" >&2; exit 3; }
printf 'ManagementPathReady: %s /readyz returned ok from a Management-cluster Pod\n' "$CHILD_NAME"
