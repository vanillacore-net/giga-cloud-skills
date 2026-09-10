#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CONTRACT=${1:?usage: scale-workers.sh CONTRACT REPLICAS KUBECONFIG CONTEXT CHILD_KUBECONFIG OS_CLOUD [OUTPUT_DIR]}
REPLICAS=${2:?missing replicas}
KUBECONFIG_FILE=${3:?missing kubeconfig}
CONTEXT=${4:?missing context}
CHILD_KUBECONFIG=${5:?missing child kubeconfig}
OS_CLOUD_NAME=${6:?missing OS_CLOUD}
OUTPUT=${7:-$ROOT/rendered}
[[ ${CONFIRM_MANAGEMENT_CONTEXT:-} == "$CONTEXT" ]] || { printf 'set CONFIRM_MANAGEMENT_CONTEXT=%s\n' "$CONTEXT" >&2; exit 2; }
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
cp "$CONTRACT" "$TMP/contract.yaml"

kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" -n service-a get openstackmachines.infrastructure.cluster.x-k8s.io \
  -l cluster.x-k8s.io/cluster-name=service-a -o json > "$TMP/before.json"
"$ROOT/scripts/set-worker-replicas.sh" "$TMP/contract.yaml" service-a "$REPLICAS"
"$ROOT/scripts/validate-manifests.sh" "$TMP/contract.yaml" "$KUBECONFIG_FILE" "$CONTEXT" "$OUTPUT"
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" diff -f "$OUTPUT/service-a.yaml" || status=$?
[[ ${status:-0} -le 1 ]] || exit "$status"
[[ ${CONFIRM_APPLY:-} == "$CONTEXT" ]] || { printf 'diff shown; set CONFIRM_APPLY=%s to update the contract and apply\n' "$CONTEXT" >&2; exit 3; }
cp "$TMP/contract.yaml" "$CONTRACT"
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" apply -f "$OUTPUT/service-a.yaml"

expected=$(python3 - "$CONTRACT" <<'PY'
import sys,yaml
c=yaml.safe_load(open(sys.argv[1])); x=next(x for x in c['clusters'] if x['name']=='service-a')
print(x['control_plane_replicas']+x['worker_replicas'])
PY
)
deadline=$(( $(date +%s) + ${SCALE_TIMEOUT_SECONDS:-1800} ))
while true; do
  kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" -n service-a get openstackmachines.infrastructure.cluster.x-k8s.io \
    -l cluster.x-k8s.io/cluster-name=service-a -o json > "$TMP/after.json"
  observed=$(python3 - "$TMP/after.json" <<'PY'
import json,sys
items=json.load(open(sys.argv[1]))['items']
ids=[x.get('status',{}).get('instanceID') for x in items]
print(len(ids) if items and all(ids) and all(x.get('status',{}).get('ready') is True for x in items) else -1)
PY
)
  [[ "$observed" == "$expected" ]] && break
  (( $(date +%s) < deadline )) || { printf 'timed out waiting for %s ready OpenStackMachines\n' "$expected" >&2; exit 3; }
  sleep 10
done

"$ROOT/scripts/verify-resource-chain.sh" "$KUBECONFIG_FILE" "$CONTEXT" service-a service-a "$CHILD_KUBECONFIG" "$OS_CLOUD_NAME"
python3 - "$TMP/before.json" "$TMP/after.json" <<'PY' > "$TMP/change"
import json,sys
def ids(path): return {x.get('status',{}).get('instanceID') for x in json.load(open(path))['items']} - {None}
before,after=ids(sys.argv[1]),ids(sys.argv[2])
for value in sorted(after-before): print('ADDED\t'+value)
for value in sorted(before-after): print('REMOVED\t'+value)
PY
while IFS=$'\t' read -r change identifier; do
  if [[ "$change" == ADDED ]]; then
    openstack --os-cloud "$OS_CLOUD_NAME" server show "$identifier" -f value -c id >/dev/null
    printf 'scale-out server present: %s\n' "$identifier"
  elif [[ "$change" == REMOVED ]]; then
    while true; do
      error="$TMP/openstack-error"
      if openstack --os-cloud "$OS_CLOUD_NAME" server show "$identifier" -f value -c id >/dev/null 2>"$error"; then
        (( $(date +%s) < deadline )) || { printf 'server still present after scale-in: %s\n' "$identifier" >&2; exit 4; }
        sleep 10
      elif grep -Eqi 'not found|no .* found|404' "$error"; then
        printf 'scale-in server absent: %s\n' "$identifier"
        break
      else
        printf 'OpenStack absence check failed for %s\n' "$identifier" >&2
        exit 4
      fi
    done
  fi
done < "$TMP/change"
