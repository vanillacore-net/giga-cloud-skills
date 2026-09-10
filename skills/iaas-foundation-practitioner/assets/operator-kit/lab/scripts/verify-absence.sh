#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -ne 3 ]; then
  printf 'usage: %s CLOUD {server|port|floating-ip|security-group|volume} ID\n' "$0" >&2
  exit 2
fi
CLOUD=$1
TYPE=$2
ID=$3
case "$TYPE" in
  server) command_group='server' ;;
  port) command_group='port' ;;
  floating-ip) command_group='floating ip' ;;
  security-group) command_group='security group' ;;
  volume) command_group='volume' ;;
  *) printf 'unsupported resource type: %s\n' "$TYPE" >&2; exit 2 ;;
esac
for _ in $(seq 1 60); do
  case "$command_group" in
    'floating ip') ids=$(openstack --os-cloud "$CLOUD" floating ip list -f value -c ID) || exit 1 ;;
    'security group') ids=$(openstack --os-cloud "$CLOUD" security group list -f value -c ID) || exit 1 ;;
    *) ids=$(openstack --os-cloud "$CLOUD" "$command_group" list -f value -c ID) || exit 1 ;;
  esac
  found=false
  for candidate in $ids; do
    [ "$candidate" = "$ID" ] && found=true
  done
  if [ "$found" = false ]; then
    printf 'Absent %s=%s\n' "$TYPE" "$ID"
    exit 0
  fi
  sleep 2
done
printf '%s still exists after 120 seconds: %s\n' "$TYPE" "$ID" >&2
exit 1
