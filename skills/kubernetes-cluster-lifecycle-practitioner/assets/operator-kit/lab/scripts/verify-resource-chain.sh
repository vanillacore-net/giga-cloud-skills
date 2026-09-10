#!/usr/bin/env bash
set -euo pipefail
KUBECONFIG_FILE=${1:?usage: verify-resource-chain.sh MGMT_KUBECONFIG CONTEXT NAMESPACE CLUSTER CHILD_KUBECONFIG OS_CLOUD}
CONTEXT=${2:?missing context}
NAMESPACE=${3:?missing namespace}
CLUSTER=${4:?missing cluster}
CHILD_KUBECONFIG=${5:?missing child kubeconfig}
OS_CLOUD_NAME=${6:?missing OS_CLOUD}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" -n "$NAMESPACE" get cluster "$CLUSTER" -o wide
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" -n "$NAMESPACE" get machines \
  -l "cluster.x-k8s.io/cluster-name=$CLUSTER" -o json > "$TMP/machines.json"
kubectl --kubeconfig "$KUBECONFIG_FILE" --context "$CONTEXT" -n "$NAMESPACE" get openstackmachines.infrastructure.cluster.x-k8s.io \
  -l "cluster.x-k8s.io/cluster-name=$CLUSTER" -o json > "$TMP/openstackmachines.json"
kubectl --kubeconfig "$CHILD_KUBECONFIG" get nodes -o json > "$TMP/nodes.json"

python3 - "$TMP" "$NAMESPACE" "$CLUSTER" <<'PY' > "$TMP/instance-ids"
import json, pathlib, sys
root=pathlib.Path(sys.argv[1])
namespace=sys.argv[2]
cluster_name=sys.argv[3]
load=lambda name: json.loads((root/name).read_text())
def normalise(value):
    if not value: return None
    return value.rsplit('/',1)[-1]
machines=load('machines.json')['items']
infra=load('openstackmachines.json')['items']
nodes=load('nodes.json')['items']
if not machines or not infra or not nodes:
    raise SystemExit('Machine, OpenStackMachine and Node lists must all be non-empty')
infra_by_name={item['metadata']['name']:item for item in infra}
node_by_id={normalise(item.get('spec',{}).get('providerID')):item for item in nodes}
if None in node_by_id or len(node_by_id)!=len(nodes):
    raise SystemExit('every Kubernetes Node must have a unique providerID')
referenced=set()
verified=[]
for machine in machines:
    meta=machine['metadata']
    if meta.get('namespace') != namespace or meta.get('labels',{}).get('cluster.x-k8s.io/cluster-name') != cluster_name:
        raise SystemExit(f"Machine has wrong namespace or cluster label: {meta.get('name')}")
    ref=machine.get('spec',{}).get('infrastructureRef') or {}
    api_group=ref.get('apiGroup') or ref.get('apiVersion') or ''
    if ref.get('kind') != 'OpenStackMachine' or api_group.split('/')[0] != 'infrastructure.cluster.x-k8s.io' or not ref.get('name'):
        raise SystemExit(f"Machine has invalid infrastructureRef: {meta.get('name')}")
    openstack_machine=infra_by_name.get(ref['name'])
    if not openstack_machine:
        raise SystemExit(f"Machine references missing OpenStackMachine: {meta.get('name')} -> {ref['name']}")
    referenced.add(ref['name'])
    infra_meta=openstack_machine['metadata']
    if infra_meta.get('namespace') != namespace or infra_meta.get('labels',{}).get('cluster.x-k8s.io/cluster-name') != cluster_name:
        raise SystemExit(f"OpenStackMachine has wrong namespace or cluster label: {ref['name']}")
    owners=infra_meta.get('ownerReferences',[])
    owner_ok=any(
        owner.get('kind')=='Machine' and owner.get('name')==meta.get('name')
        and owner.get('uid')==meta.get('uid') and owner.get('controller') is True
        for owner in owners
    )
    if not owner_ok:
        raise SystemExit(f"OpenStackMachine lacks the expected controller ownerReference: {ref['name']}")
    machine_id=normalise(machine.get('spec',{}).get('providerID'))
    instance_id=normalise(openstack_machine.get('status',{}).get('instanceID'))
    if not machine_id or machine_id != instance_id:
        raise SystemExit(f"provider-ID mismatch for {meta.get('name')}: Machine={machine_id} OpenStackMachine={instance_id}")
    node=node_by_id.get(instance_id)
    if not node:
        raise SystemExit(f"no Kubernetes Node has providerID {instance_id}")
    ready=next((condition.get('status') for condition in node.get('status',{}).get('conditions',[]) if condition.get('type')=='Ready'),None)
    if ready!='True':
        raise SystemExit(f"Node is not Ready: {node['metadata']['name']}")
    verified.append(instance_id)
if referenced != set(infra_by_name):
    raise SystemExit(f"unpaired OpenStackMachines: {sorted(set(infra_by_name)-referenced)}")
if len(set(verified)) != len(verified):
    raise SystemExit('provider IDs are not unique across Machine ownership chains')
for identifier in sorted(verified): print(identifier)
PY

while IFS= read -r identifier; do
  openstack --os-cloud "$OS_CLOUD_NAME" server show "$identifier" -f value -c id >/dev/null
  printf 'verified Machine -> OpenStack server -> Ready Node: %s\n' "$identifier"
done < "$TMP/instance-ids"
