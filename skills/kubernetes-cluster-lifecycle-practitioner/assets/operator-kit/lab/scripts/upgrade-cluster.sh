#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CONTRACT=${1:?usage: upgrade-cluster.sh CONTRACT NAMESPACE CLUSTER TARGET_VERSION TARGET_IMAGE_ID MGMT_KUBECONFIG CONTEXT CHILD_KUBECONFIG OS_CLOUD WORKLOAD_NAMESPACE WORKLOAD_DEPLOYMENT [OUTPUT_DIR]}
NAMESPACE=${2:?missing namespace}
CLUSTER=${3:?missing cluster}
TARGET_VERSION=${4:?missing target Kubernetes version}
TARGET_IMAGE_ID=${5:?missing target Glance image UUID}
KUBECONFIG_FILE=${6:?missing management kubeconfig}
CONTEXT=${7:?missing management context}
CHILD_KUBECONFIG=${8:?missing child kubeconfig}
OS_CLOUD_NAME=${9:?missing OS_CLOUD}
WORKLOAD_NAMESPACE=${10:?missing workload namespace}
WORKLOAD_DEPLOYMENT=${11:?missing workload deployment}
OUTPUT=${12:-$ROOT/evidence/upgrade}
TIMEOUT=${UPGRADE_TIMEOUT:-45m}

[[ ${CONFIRM_MANAGEMENT_CONTEXT:-} == "$CONTEXT" ]] || {
  printf 'set CONFIRM_MANAGEMENT_CONTEXT=%s\n' "$CONTEXT" >&2
  exit 2
}
"$ROOT/scripts/require-context.sh" "$KUBECONFIG_FILE" "$CONTEXT"
test -r "$CHILD_KUBECONFIG"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
cp "$CONTRACT" "$TMP/contract.yaml"
"$ROOT/scripts/set-cluster-upgrade.py" \
  "$TMP/contract.yaml" "$CLUSTER" "$TARGET_VERSION" "$TARGET_IMAGE_ID"
readarray -t selected < <(python3 - "$TMP/contract.yaml" "$CLUSTER" <<'PY'
import sys,yaml
contract=yaml.safe_load(open(sys.argv[1]))
cluster=next(item for item in contract['clusters'] if item['name']==sys.argv[2])
print(cluster['namespace'])
print(cluster['image_id'])
PY
)
CONTRACT_NAMESPACE=${selected[0]}
TARGET_IMAGE_ID=${selected[1]}
[[ "$NAMESPACE" == "$CONTRACT_NAMESPACE" ]] || {
  printf 'namespace mismatch: argument=%s contract=%s\n' "$NAMESPACE" "$CONTRACT_NAMESPACE" >&2
  exit 2
}

# Bind the child kubeconfig to this CAPI Cluster and require a complete current
# ownership chain before that child can authorize an availability gate.
"$ROOT/scripts/verify-resource-chain.sh" \
  "$KUBECONFIG_FILE" "$CONTEXT" "$NAMESPACE" "$CLUSTER" \
  "$CHILD_KUBECONFIG" "$OS_CLOUD_NAME"

current_version=$(kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" \
  -n "$NAMESPACE" get cluster "$CLUSTER" -o jsonpath='{.spec.topology.version}')
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" -n "$NAMESPACE" \
  get machines -l "cluster.x-k8s.io/cluster-name=$CLUSTER" -o json > "$TMP/baseline-machines.json"
kubectl --kubeconfig "$CHILD_KUBECONFIG" get nodes -o json > "$TMP/baseline-nodes.json"
python3 - "$TMP/baseline-machines.json" "$TMP/baseline-nodes.json" "$current_version" <<'PY'
import json,re,sys
machines=json.load(open(sys.argv[1])).get('items',[])
nodes=json.load(open(sys.argv[2])).get('items',[])
expected=sys.argv[3]
pattern=re.compile(r'^v[1-9][0-9]*\.[0-9]+\.[0-9]+')
def canonical(value):
    match=pattern.match(value or '')
    return match.group(0) if match else None
def provider(value):
    return value.rsplit('/',1)[-1] if value else None
if not machines:
    raise SystemExit('pre-upgrade convergence requires at least one CAPI Machine')
nodes_by_provider={provider(item.get('spec',{}).get('providerID')):item for item in nodes}
for machine in machines:
    name=machine.get('metadata',{}).get('name','<unnamed>')
    machine_version=canonical(machine.get('spec',{}).get('version'))
    if machine_version != expected:
        raise SystemExit(f'Machine {name} has not converged to topology version {expected}: {machine_version}')
    identifier=provider(machine.get('spec',{}).get('providerID'))
    node=nodes_by_provider.get(identifier)
    if not node:
        raise SystemExit(f'no child Node matches Machine {name}')
    node_version=canonical(node.get('status',{}).get('nodeInfo',{}).get('kubeletVersion'))
    if node_version != expected:
        raise SystemExit(f'Node for Machine {name} has not converged to topology version {expected}: {node_version}')
PY
python3 - "$current_version" "$TARGET_VERSION" <<'PY'
import re,sys
pattern=re.compile(r'^v([1-9][0-9]*)\.([0-9]+)\.([0-9]+)$')
current_match=pattern.fullmatch(sys.argv[1])
target_match=pattern.fullmatch(sys.argv[2])
if not current_match or not target_match:
    raise SystemExit(f'explicit current and target versions required: {sys.argv[1]} -> {sys.argv[2]}')
current=tuple(map(int,current_match.groups()))
target=tuple(map(int,target_match.groups()))
if target <= current:
    raise SystemExit(f'target must be newer than current version: {sys.argv[1]} -> {sys.argv[2]}')
if target[0] != current[0] or target[1] > current[1] + 1:
    raise SystemExit(f'upgrade cannot change major version or skip a minor release: {sys.argv[1]} -> {sys.argv[2]}')
PY

observed_image=$(openstack --os-cloud "$OS_CLOUD_NAME" image show \
  "$TARGET_IMAGE_ID" -f value -c id)
[[ "$observed_image" == "$TARGET_IMAGE_ID" ]] || {
  printf 'Glance returned image %s instead of requested %s\n' \
    "$observed_image" "$TARGET_IMAGE_ID" >&2
  exit 2
}

mkdir -p "$OUTPUT"
"$ROOT/scripts/validate-manifests.sh" \
  "$TMP/contract.yaml" "$KUBECONFIG_FILE" "$CONTEXT" "$OUTPUT"
MANIFEST="$OUTPUT/$CLUSTER.yaml"

# kubectl diff returns 1 when a valid difference exists. Any other non-zero
# status is an execution failure, and a zero status means there is no upgrade.
diff_status=0
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" \
  diff -f "$MANIFEST" || diff_status=$?
if [[ "$diff_status" -gt 1 ]]; then
  exit "$diff_status"
fi
if [[ "$diff_status" -eq 0 ]]; then
  printf 'no upgrade difference found for %s/%s\n' "$NAMESPACE" "$CLUSTER" >&2
  exit 3
fi

confirmation="$NAMESPACE/$CLUSTER:$TARGET_VERSION:$TARGET_IMAGE_ID"
printf 'reviewed upgrade confirmation: %s\n' "$confirmation"
if [[ ${PREPARE_ONLY:-no} == yes ]]; then
  printf 'prepare-only complete; no Cluster object or contract was changed\n'
  exit 0
fi
[[ ${CONFIRM_UPGRADE:-} == "$confirmation" ]] || {
  printf 'diff shown; set CONFIRM_UPGRADE=%s to apply this exact version and image pair\n' \
    "$confirmation" >&2
  exit 3
}

# Establish workload availability before changing any cluster machine.
kubectl --kubeconfig "$CHILD_KUBECONFIG" -n "$WORKLOAD_NAMESPACE" \
  rollout status "deployment/$WORKLOAD_DEPLOYMENT" --timeout=5m

cp "$TMP/contract.yaml" "$CONTRACT"
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" \
  apply -f "$MANIFEST"

show_diagnostics() {
  set +e
  clusterctl --kubeconfig "$KUBECONFIG_FILE" describe cluster "$CLUSTER" \
    --namespace "$NAMESPACE" --show-conditions all >&2
  kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" -n "$NAMESPACE" \
    get cluster,kubeadmcontrolplane,machinedeployment,machine,openstackmachine -o wide >&2
}
run_or_diagnose() {
  if ! "$@"; then
    show_diagnostics
    exit 4
  fi
}
selector="cluster.x-k8s.io/cluster-name=$CLUSTER"

# Observe the control-plane stage first. Require the new spec and v1beta2
# rollout conditions before accepting worker completion.
run_or_diagnose kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" \
  -n "$NAMESPACE" wait kubeadmcontrolplane -l "$selector" \
  --for=jsonpath='{.spec.version}'="$TARGET_VERSION" --timeout="$TIMEOUT"
for condition in MachinesUpToDate MachinesReady Available; do
  run_or_diagnose kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" \
    -n "$NAMESPACE" wait kubeadmcontrolplane -l "$selector" \
    --for="condition=$condition" --timeout="$TIMEOUT"
done

# The worker MachineDeployment follows only after the control plane reports
# the target version as ready and up to date.
run_or_diagnose kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" \
  -n "$NAMESPACE" wait machinedeployment -l "$selector" \
  --for=jsonpath='{.spec.template.spec.version}'="$TARGET_VERSION" --timeout="$TIMEOUT"
for condition in MachinesUpToDate MachinesReady Available; do
  run_or_diagnose kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" \
    -n "$NAMESPACE" wait machinedeployment -l "$selector" \
    --for="condition=$condition" --timeout="$TIMEOUT"
done

kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" -n "$NAMESPACE" \
  get machines -l "$selector" -o json > "$TMP/machines.json"
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" -n "$NAMESPACE" \
  get openstackmachines.infrastructure.cluster.x-k8s.io -l "$selector" \
  -o json > "$TMP/openstackmachines.json"
python3 - "$TMP/machines.json" "$TMP/openstackmachines.json" \
  "$TARGET_VERSION" "$TARGET_IMAGE_ID" <<'PY'
import json,sys
machines=json.load(open(sys.argv[1]))['items']
infrastructure=json.load(open(sys.argv[2]))['items']
target_version=sys.argv[3]
target_image=sys.argv[4]
if not machines or not infrastructure:
    raise SystemExit('upgrade verification requires Machines and OpenStackMachines')
wrong_versions=[item['metadata']['name'] for item in machines if item.get('spec',{}).get('version') != target_version]
wrong_images=[item['metadata']['name'] for item in infrastructure if item.get('spec',{}).get('image',{}).get('id') != target_image]
not_ready=[item['metadata']['name'] for item in infrastructure if item.get('status',{}).get('ready') is not True]
if wrong_versions:
    raise SystemExit(f'Machines not on {target_version}: {wrong_versions}')
if wrong_images:
    raise SystemExit(f'OpenStackMachines not on image {target_image}: {wrong_images}')
if not_ready:
    raise SystemExit(f'OpenStackMachines not Ready: {not_ready}')
PY

"$ROOT/scripts/verify-resource-chain.sh" \
  "$KUBECONFIG_FILE" "$CONTEXT" "$NAMESPACE" "$CLUSTER" \
  "$CHILD_KUBECONFIG" "$OS_CLOUD_NAME"
kubectl --kubeconfig "$CHILD_KUBECONFIG" get nodes -o wide
kubectl --kubeconfig "$CHILD_KUBECONFIG" -n "$WORKLOAD_NAMESPACE" \
  rollout status "deployment/$WORKLOAD_DEPLOYMENT" --timeout=5m
clusterctl --kubeconfig "$KUBECONFIG_FILE" describe cluster "$CLUSTER" \
  --namespace "$NAMESPACE" --show-conditions all
printf 'upgrade verified: %s/%s version=%s image=%s workload=%s/%s\n' \
  "$NAMESPACE" "$CLUSTER" "$TARGET_VERSION" "$TARGET_IMAGE_ID" \
  "$WORKLOAD_NAMESPACE" "$WORKLOAD_DEPLOYMENT"
