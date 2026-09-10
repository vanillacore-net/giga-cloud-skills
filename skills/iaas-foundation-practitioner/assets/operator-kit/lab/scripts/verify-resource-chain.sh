#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -ne 6 ]; then
  printf 'usage: %s CLOUD SERVER_ID PORT_ID SECURITY_GROUP_ID FLOATING_IP_ID VOLUME_ID\n' "$0" >&2
  exit 2
fi
CLOUD=$1
SERVER_ID=$2
PORT_ID=$3
SECURITY_GROUP_ID=$4
FIP_ID=$5
VOLUME_ID=$6

server_status=$(openstack --os-cloud "$CLOUD" server show "$SERVER_ID" -f value -c status)
[ "$server_status" = ACTIVE ] || { printf 'server is %s, not ACTIVE\n' "$server_status" >&2; exit 1; }

port_ids=$(openstack --os-cloud "$CLOUD" port list --server "$SERVER_ID" -f value -c ID)
read -r -a port_id_array <<< "$port_ids"
[ "${#port_id_array[@]}" -eq 1 ] || {
  printf 'expected one VM port, found %s\n' "${#port_id_array[@]}" >&2
  exit 1
}
[ "${port_id_array[0]}" = "$PORT_ID" ] || {
  printf 'recorded port does not match server port\n' >&2
  exit 1
}

port_json=$(openstack --os-cloud "$CLOUD" port show "$PORT_ID" \
  -f json -c device_id -c status -c security_group_ids)
floating_ip_json=$(openstack --os-cloud "$CLOUD" floating ip show "$FIP_ID" \
  -f json -c port_id -c status)
volume_json=$(openstack --os-cloud "$CLOUD" volume show "$VOLUME_ID" \
  -f json -c attachments -c status)

python3 - "$SERVER_ID" "$PORT_ID" "$SECURITY_GROUP_ID" \
  "$port_json" "$floating_ip_json" "$volume_json" <<'PY'
import json
import sys

server_id, port_id, security_group_id = sys.argv[1:4]
port, floating_ip, volume = (json.loads(value) for value in sys.argv[4:7])

if port.get('device_id') != server_id:
    raise SystemExit('port device_id does not match server')
if port.get('status') != 'ACTIVE':
    raise SystemExit('port is not ACTIVE')
if security_group_id not in (port.get('security_group_ids') or []):
    raise SystemExit('security group is not attached to the VM port')
if floating_ip.get('port_id') != port_id:
    raise SystemExit('floating IP does not reference the VM port')
if floating_ip.get('status') != 'ACTIVE':
    raise SystemExit('floating IP is not ACTIVE')
attachments = volume.get('attachments') or []
if not any(attachment.get('server_id') == server_id for attachment in attachments):
    raise SystemExit('volume attachment does not reference the server')
if volume.get('status') != 'in-use':
    raise SystemExit('volume is not in-use')
PY
printf 'Validated server=%s port=%s security_group=%s floating_ip=%s volume=%s\n' \
  "$SERVER_ID" "$PORT_ID" "$SECURITY_GROUP_ID" "$FIP_ID" "$VOLUME_ID"
