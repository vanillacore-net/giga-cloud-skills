# Chapter 3 OpenTofu recipe

This directory declares the same IaaS request used in Chapter 3: one VM, an HTTPS-only security group, a separate Cinder data volume, and a floating IP. `terraform.tfvars.example` contains public-safe reference-lab values. They are test values, not production recommendations.

The files do not contain credentials or an OpenStack endpoint. Keep `clouds.yaml`, `terraform.tfvars`, state, and plans out of version control. Use this path in a clean project, with different resource names, or after importing existing resources. Do not apply it after creating same-named resources through Horizon or the CLI.

## Discover and approve the inputs

Obtain a working `clouds.yaml` profile for the target project. Do not copy it into this directory. Set the intended names, then run the service-specific checks:

```bash
set -euo pipefail

CLOUD=my-cloud
VM_NAME=web-01
SECURITY_GROUP_NAME=web-https
IMAGE_NAME=ubuntu
FLAVOR_NAME=m1.tiny
VM_NETWORK_NAME=demo-network
FLOATING_IP_NETWORK_NAME=external-network
VOLUME_TYPE=__DEFAULT__
COMPUTE_AZ=nova
VOLUME_AZ=nova
APPROVED_HTTPS_CIDR=198.51.100.0/24

openstack --os-cloud "$CLOUD" token issue -f value -c expires
IMAGE_ID=$(openstack --os-cloud "$CLOUD" image show \
  "$IMAGE_NAME" -f value -c id)
printf 'IMAGE_ID=%s\n' "$IMAGE_ID"

openstack --os-cloud "$CLOUD" flavor show "$FLAVOR_NAME" \
  -f json -c name -c vcpus -c ram -c disk
openstack --os-cloud "$CLOUD" network show "$VM_NETWORK_NAME" \
  -f json -c id -c status -c router:external
openstack --os-cloud "$CLOUD" network show "$FLOATING_IP_NETWORK_NAME" \
  -f json -c id -c status -c router:external
openstack --os-cloud "$CLOUD" quota show --network -f json
openstack --os-cloud "$CLOUD" volume type show "$VOLUME_TYPE" \
  -f json -c name -c is_public
openstack --os-cloud "$CLOUD" availability zone list --compute \
  -f value -c "Zone Name" -c "Zone Status"
openstack --os-cloud "$CLOUD" availability zone list --volume \
  -f value -c "Zone Name" -c "Zone Status"

# In a disposable practice project, prove that policy and pool capacity
# permit allocation, then release the probe before OpenTofu runs.
FLOATING_IP_NETWORK_ID=$(openstack --os-cloud "$CLOUD" network show \
  "$FLOATING_IP_NETWORK_NAME" -f value -c id)
PROBE_FIP_ID=
cleanup_probe() {
  [ -z "$PROBE_FIP_ID" ] || \
    openstack --os-cloud "$CLOUD" floating ip delete \
      "$PROBE_FIP_ID" >/dev/null 2>&1 || true
}
trap cleanup_probe EXIT
PROBE_FIP_ID=$(openstack --os-cloud "$CLOUD" floating ip create \
  "$FLOATING_IP_NETWORK_NAME" -f value -c id)
[ "$(openstack --os-cloud "$CLOUD" floating ip show "$PROBE_FIP_ID" \
  -f value -c floating_network_id)" = "$FLOATING_IP_NETWORK_ID" ]
openstack --os-cloud "$CLOUD" floating ip delete "$PROBE_FIP_ID"
for attempt in $(seq 1 60); do
  PROBE_IDS=$(openstack --os-cloud "$CLOUD" floating ip list \
    -f value -c ID) || exit 1
  case "$PROBE_IDS" in
    *"$PROBE_FIP_ID"*) ;;
    *) PROBE_FIP_ID=; trap - EXIT; break ;;
  esac
  [ "$attempt" -eq 60 ] && exit 1
  sleep 2
done
```

Proceed only when the VM network is `ACTIVE`, the floating-IP network is `ACTIVE` with `router:external` set to `true`, the project has capacity for another floating IP, the probe allocation is created and released successfully, the image and flavor match the request, and the selected Nova and Cinder zones are reported as `available`. Stop if discovery returns an error or an ambiguous selection. Skip the probe only when the operator supplies equivalent evidence that project policy and the selected pool permit allocation.

The reference lab calls both service-specific zones `nova`. Comparable clouds may use different names. `198.51.100.0/24` is a documentation range, not a production client range.

## Create the variable file

Create the local variable file from the values that were discovered and approved:

```bash
cp terraform.tfvars.example terraform.tfvars

printf '%s\n' \
  "openstack_cloud = \"$CLOUD\"" \
  "vm_name = \"$VM_NAME\"" \
  "security_group_name = \"$SECURITY_GROUP_NAME\"" \
  "image_id = \"$IMAGE_ID\"" \
  "flavor_name = \"$FLAVOR_NAME\"" \
  "vm_network_name = \"$VM_NETWORK_NAME\"" \
  "floating_ip_network_name = \"$FLOATING_IP_NETWORK_NAME\"" \
  "approved_https_cidr = \"$APPROVED_HTTPS_CIDR\"" \
  "volume_type = \"$VOLUME_TYPE\"" \
  'volume_size_gib = 1' \
  "compute_availability_zone = \"$COMPUTE_AZ\"" \
  "volume_availability_zone = \"$VOLUME_AZ\"" \
  > terraform.tfvars
```

Review `terraform.tfvars`. Do not commit it.

## Preview and apply

```bash
set -euo pipefail

tofu init
tofu fmt -check
tofu validate
tofu plan -out web-01.tfplan
tofu apply web-01.tfplan
```

`tofu plan` is the review point. It shows the VM, Neutron security group and rule, Cinder volume, attachment, floating IP, and association before the API receives a create request. `tofu apply` creates only the resources shown in the reviewed plan. A failed allocation, error state or non-zero command stops this shell sequence.

Commit the `.tf` files, the lock file and a non-secret example variable file to Git. Do not commit live state. Team use requires a protected remote state backend with access control, encryption and locking. Git plus protected state, credentials and a tested validation procedure provides stronger recovery evidence than dashboard history alone. Git by itself does not report live platform status.

## Validate the applied resources

Use the stable identifiers exported by OpenTofu. The checks reject zero or multiple VM ports and compare the Nova, Neutron and Cinder relationships directly:

```bash
set -euo pipefail

CLOUD=$(tofu output -raw openstack_cloud)
SERVER_ID=$(tofu output -raw server_id)
PORT_ID=$(tofu output -raw port_id)
SECURITY_GROUP_ID=$(tofu output -raw security_group_id)
FIP_ID=$(tofu output -raw floating_ip_id)
FIP=$(tofu output -raw floating_ip_address)
VOLUME_ID=$(tofu output -raw volume_id)

PORT_IDS=$(openstack --os-cloud "$CLOUD" port list \
  --server "$SERVER_ID" -f value -c ID)
set -- $PORT_IDS
[ "$#" -eq 1 ] || {
  printf 'Expected one VM port, found %s\n' "$#" >&2
  exit 1
}
[ "$1" = "$PORT_ID" ] || {
  printf 'OpenTofu port ID does not match the VM port\n' >&2
  exit 1
}

[ "$(openstack --os-cloud "$CLOUD" server show "$SERVER_ID" \
  -f value -c status)" = ACTIVE ] || exit 1
[ "$(openstack --os-cloud "$CLOUD" port show "$PORT_ID" \
  -f value -c device_id)" = "$SERVER_ID" ] || exit 1
case "$(openstack --os-cloud "$CLOUD" port show "$PORT_ID" \
  -f value -c security_group_ids)" in
  *"$SECURITY_GROUP_ID"*) ;;
  *) printf 'Security group is not attached to the VM port\n' >&2; exit 1 ;;
esac
[ "$(openstack --os-cloud "$CLOUD" floating ip show "$FIP_ID" \
  -f value -c port_id)" = "$PORT_ID" ] || exit 1
[ "$(openstack --os-cloud "$CLOUD" floating ip show "$FIP_ID" \
  -f value -c status)" = ACTIVE ] || exit 1
case "$(openstack --os-cloud "$CLOUD" volume show "$VOLUME_ID" \
  -f value -c attachments)" in
  *"$SERVER_ID"*) ;;
  *) printf 'Volume is not attached to the OpenTofu server\n' >&2; exit 1 ;;
esac
[ "$(openstack --os-cloud "$CLOUD" volume show "$VOLUME_ID" \
  -f value -c status)" = in-use ] || exit 1

printf 'Validated server=%s port=%s security_group=%s floating_ip=%s volume=%s\n' \
  "$SERVER_ID" "$PORT_ID" "$SECURITY_GROUP_ID" "$FIP" "$VOLUME_ID"
```

The floating address is an input to the later workload-layer test. It does not establish administrative access to the VM or prove that a service is running.

## Change and removal

Change the declared inputs, create a new plan, review it, then apply it. The data volume has `prevent_destroy = true`, so a routine destruction plan cannot delete it with the VM.

For a disposable practice deployment, first confirm that the volume contains no data that must be retained. Change `prevent_destroy` to `false` in a reviewed working copy, then run:

```bash
set -euo pipefail

CLOUD=$(tofu output -raw openstack_cloud)
SERVER_ID=$(tofu output -raw server_id)
PORT_ID=$(tofu output -raw port_id)
SECURITY_GROUP_ID=$(tofu output -raw security_group_id)
FIP_ID=$(tofu output -raw floating_ip_id)
VOLUME_ID=$(tofu output -raw volume_id)

tofu plan -destroy -out cleanup.tfplan
tofu apply cleanup.tfplan

wait_for_absence() {
  label=$1
  id=$2
  shift 2
  for attempt in $(seq 1 60); do
    if ! ids=$("$@" -f value -c ID); then
      printf 'Failed to query %s during cleanup\n' "$label" >&2
      return 1
    fi
    case "$ids" in
      *"$id"*) ;;
      *) return 0 ;;
    esac
    sleep 2
  done
  printf '%s still exists after 120 seconds\n' "$label" >&2
  return 1
}

wait_for_absence "server $SERVER_ID" "$SERVER_ID" \
  openstack --os-cloud "$CLOUD" server list || exit 1
wait_for_absence "port $PORT_ID" "$PORT_ID" \
  openstack --os-cloud "$CLOUD" port list || exit 1
wait_for_absence "security group $SECURITY_GROUP_ID" "$SECURITY_GROUP_ID" \
  openstack --os-cloud "$CLOUD" security group list || exit 1
wait_for_absence "floating IP $FIP_ID" "$FIP_ID" \
  openstack --os-cloud "$CLOUD" floating ip list || exit 1
wait_for_absence "volume $VOLUME_ID" "$VOLUME_ID" \
  openstack --os-cloud "$CLOUD" volume list || exit 1
```

Do not weaken lifecycle protection when the volume must be retained. DNS records, certificates, filesystem creation, application data, monitoring, backup policy, and service recovery belong to the workload design and are not created here.
