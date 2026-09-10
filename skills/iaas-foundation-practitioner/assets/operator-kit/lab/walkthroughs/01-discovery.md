# 01: Discovery and environment contract

**Starting state:** We have an approved disposable project and a protected `clouds.yaml` profile. No Chapter 3 resources exist in the project.

**End state:** Every input has been discovered through the service that owns it, the project has enough quota for the request, and `../environment-contract.yaml` records approved values.

**Companion video:** [C3-P1](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/VIDEO_SCOPES.md#user-content-c3-p1-discover-and-approve-the-lab-inputs)

## Prepare the local contract

From `$GIGA_OPERATOR_KIT`:

```bash
cp environment-contract.example.yaml environment-contract.yaml
chmod 600 environment-contract.yaml
```

Replace the example profile and catalogue values with values from the target cloud. Set `example_only: false` only after the checks below pass.

## Verify identity and quota

Set the local profile name without printing credentials:

```bash
set -euo pipefail
CLOUD=my-cloud

openstack --os-cloud "$CLOUD" token issue -f json -c expires -c project_id
PROJECT_ID=$(openstack --os-cloud "$CLOUD" token issue -f value -c project_id)
[ -n "$PROJECT_ID" ] || exit 1
ACTIVE_PROJECT_NAME=$(openstack --os-cloud "$CLOUD" project show "$PROJECT_ID" -f value -c name)
CONTRACT_PROJECT_NAME=$(python3 - <<'PY'
from pathlib import Path
from scripts.preflight import parse_flat_yaml
print(parse_flat_yaml(Path('environment-contract.yaml'))['project_name'])
PY
)
[ "$ACTIVE_PROJECT_NAME" = "$CONTRACT_PROJECT_NAME" ] || {
  printf 'active project %s does not match contract project %s\n' \
    "$ACTIVE_PROJECT_NAME" "$CONTRACT_PROJECT_NAME" >&2
  exit 1
}
printf 'PROJECT_ID=%s PROJECT_NAME=%s\n' "$PROJECT_ID" "$ACTIVE_PROJECT_NAME"
openstack --os-cloud "$CLOUD" quota show --compute --usage
openstack --os-cloud "$CLOUD" quota show --volume --usage
openstack --os-cloud "$CLOUD" quota show --network --usage
```

The comparison stops when the project returned by the token differs from the approved disposable project recorded in the contract. We then need remaining allowance for one instance, one virtual CPU, 512 MiB RAM, one 1 GiB volume, one port, one security group, its default and custom rules, and one floating IP. Quota is only a configured limit. It does not prove placement capacity.

In Horizon, select the intended project, open **Project -> Compute -> Overview**, then inspect **Project -> Volumes -> Volumes** and **Project -> Network -> Floating IPs**. The reference view is shown in [Figure 2](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/chapter-3.md#user-content-project-identity-and-quota).

## Discover service-specific inputs

```bash
IMAGE_NAME=ubuntu
FLAVOR_NAME=m1.tiny
VM_NETWORK_NAME=demo-network
FLOATING_IP_NETWORK_NAME=external-network
VOLUME_TYPE=__DEFAULT__

openstack --os-cloud "$CLOUD" image show "$IMAGE_NAME" \
  -f json -c id -c status
IMAGE_ID=$(openstack --os-cloud "$CLOUD" image show \
  "$IMAGE_NAME" -f value -c id)
printf 'IMAGE_ID=%s\n' "$IMAGE_ID"

openstack --os-cloud "$CLOUD" flavor show "$FLAVOR_NAME" \
  -f json -c name -c vcpus -c ram -c disk
openstack --os-cloud "$CLOUD" network show "$VM_NETWORK_NAME" \
  -f json -c id -c status -c "router:external"
openstack --os-cloud "$CLOUD" network show "$FLOATING_IP_NETWORK_NAME" \
  -f json -c id -c status -c "router:external"
openstack --os-cloud "$CLOUD" volume type show "$VOLUME_TYPE" \
  -f json -c name -c is_public
openstack --os-cloud "$CLOUD" availability zone list --compute \
  -f value -c "Zone Name" -c "Zone Status"
openstack --os-cloud "$CLOUD" availability zone list --volume \
  -f value -c "Zone Name" -c "Zone Status"
```

Continue only when the image is active and approved, the flavor matches the request, the VM network is active, and the floating-IP network is active with `router:external` set to `true`. Select the Nova and Cinder zones independently even when both labels are `nova`.

A live allocation probe changes cloud state and therefore requires project approval. When authorised, allocate one floating IP from the selected pool, verify its `floating_network_id`, delete it and confirm absence before continuing. Otherwise record equivalent operator-supplied evidence that the pool and policy permit allocation.

## Validate the contract

Edit `environment-contract.yaml`, retain no credentials or endpoints, set `example_only: false`, then run:

```bash
python3 scripts/preflight.py environment-contract.yaml
```

**Stop when:** discovery is ambiguous, a service reports an error, quota is insufficient, the network is not external, or either service-specific zone is unavailable.

**Evidence for the next step:** approved local contract, scoped project identity, current quota output, immutable image ID, flavor properties, network properties, volume type and both availability-zone results.
