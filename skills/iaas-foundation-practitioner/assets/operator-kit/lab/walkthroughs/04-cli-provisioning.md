# 04: Provision the request with OpenStackClient

**Starting state:** Walkthrough 01 is accepted. No same-named resources from the Horizon or OpenTofu path exist.

**End state:** The server, port, security group, floating IP and volume exist, and their stable identifiers are saved in an ignored evidence file.

**Companion video:** [C3-P4](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/VIDEO_SCOPES.md#user-content-c3-p4-provision-the-request-with-openstackclient)

## Establish the shell

Use a fresh shell from `$GIGA_OPERATOR_KIT`. Substitute only values approved in the local environment contract:

```bash
set -euo pipefail
umask 077
CLOUD=my-cloud
VM_NAME=web-01
SECURITY_GROUP_NAME=web-https
VOLUME_NAME=web-01-data
IMAGE_ID=369e53e4-081a-4b74-94af-1b9f5dffda75
FLAVOR_NAME=m1.tiny
VM_NETWORK_NAME=demo-network
FLOATING_IP_NETWORK_NAME=external-network
VOLUME_TYPE=__DEFAULT__
COMPUTE_AZ=nova
VOLUME_AZ=nova
APPROVED_HTTPS_CIDR=198.51.100.0/24
```

Run the discovery commands from Walkthrough 01 again in this shell. Continue only when they still match the approved contract.

## Create policy and volume

```bash
openstack --os-cloud "$CLOUD" security group create \
  --description "Allow HTTPS from the documentation client range" \
  "$SECURITY_GROUP_NAME"
SECURITY_GROUP_ID=$(openstack --os-cloud "$CLOUD" security group show \
  "$SECURITY_GROUP_NAME" -f value -c id)

openstack --os-cloud "$CLOUD" security group rule create \
  --ingress --ethertype IPv4 --protocol tcp --dst-port 443:443 \
  --remote-ip "$APPROVED_HTTPS_CIDR" "$SECURITY_GROUP_ID"

openstack --os-cloud "$CLOUD" volume create --size 1 \
  --type "$VOLUME_TYPE" --availability-zone "$VOLUME_AZ" "$VOLUME_NAME"
VOLUME_ID=$(openstack --os-cloud "$CLOUD" volume show "$VOLUME_NAME" -f value -c id)
```

Use a bounded wait. Query failures and terminal error states fail the step:

```bash
for attempt in $(seq 1 60); do
  status=$(openstack --os-cloud "$CLOUD" volume show "$VOLUME_ID" -f value -c status) || exit 1
  case "$status" in
    available) break ;;
    error|error_*) exit 1 ;;
  esac
  [ "$attempt" -eq 60 ] && exit 1
  sleep 2
done
```

## Create the server and attach storage

```bash
timeout 180 openstack --os-cloud "$CLOUD" server create --wait \
  --image "$IMAGE_ID" --flavor "$FLAVOR_NAME" \
  --network "$VM_NETWORK_NAME" --availability-zone "$COMPUTE_AZ" \
  --security-group "$SECURITY_GROUP_ID" "$VM_NAME"
SERVER_ID=$(openstack --os-cloud "$CLOUD" server show "$VM_NAME" -f value -c id)

openstack --os-cloud "$CLOUD" server add volume "$SERVER_ID" "$VOLUME_ID"
for attempt in $(seq 1 60); do
  status=$(openstack --os-cloud "$CLOUD" volume show "$VOLUME_ID" -f value -c status) || exit 1
  case "$status" in
    in-use) break ;;
    error|error_*) exit 1 ;;
  esac
  [ "$attempt" -eq 60 ] && exit 1
  sleep 2
done
```

## Allocate and associate the floating IP

```bash
FIP_ID=$(openstack --os-cloud "$CLOUD" floating ip create \
  "$FLOATING_IP_NETWORK_NAME" -f value -c id)
FIP=$(openstack --os-cloud "$CLOUD" floating ip show "$FIP_ID" \
  -f value -c floating_ip_address)
openstack --os-cloud "$CLOUD" server add floating ip "$SERVER_ID" "$FIP"

for attempt in $(seq 1 60); do
  status=$(openstack --os-cloud "$CLOUD" floating ip show "$FIP_ID" -f value -c status) || exit 1
  port_id=$(openstack --os-cloud "$CLOUD" floating ip show "$FIP_ID" -f value -c port_id) || exit 1
  [ "$status" = ACTIVE ] && [ -n "$port_id" ] && break
  case "$status" in ERROR|ERROR_*) exit 1 ;; esac
  [ "$attempt" -eq 60 ] && exit 1
  sleep 2
done
PORT_ID=$port_id
```

Persist identifiers without credentials:

```bash
mkdir -p evidence
python3 - "$CLOUD" "$SERVER_ID" "$PORT_ID" "$SECURITY_GROUP_ID" "$FIP_ID" "$VOLUME_ID" <<'PY'
import json, pathlib, sys
keys = ['cloud', 'server_id', 'port_id', 'security_group_id', 'floating_ip_id', 'volume_id']
pathlib.Path('evidence/resource-ids.json').write_text(json.dumps(dict(zip(keys, sys.argv[1:])), indent=2) + '\n')
PY
```

**Stop when:** any create command fails, a resource enters an error state, a wait times out or more than one VM port exists.

**Evidence for the next step:** `evidence/resource-ids.json` plus successful API read-back for every recorded ID.
