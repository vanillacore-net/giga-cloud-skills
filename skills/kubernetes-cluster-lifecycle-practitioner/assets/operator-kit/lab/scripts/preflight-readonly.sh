#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CONTRACT=${1:?usage: preflight-readonly.sh CONTRACT OS_CLOUD}
OS_CLOUD_NAME=${2:?usage: preflight-readonly.sh CONTRACT OS_CLOUD}

for command in python3 openstack; do
  command -v "$command" >/dev/null || { printf 'missing command: %s\n' "$command" >&2; exit 2; }
done
python3 - "$ROOT" "$CONTRACT" <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path(sys.argv[1]) / 'scripts'))
from lablib import load_yaml, validate_environment
errors = validate_environment(load_yaml(Path(sys.argv[2])), require_live=True)
if errors:
    print('\n'.join(f'ERROR: {item}' for item in errors), file=sys.stderr)
    raise SystemExit(2)
PY

openstack --os-cloud "$OS_CLOUD_NAME" token issue -f value -c expires
readarray -t facts < <(python3 - "$CONTRACT" <<'PY'
import sys,yaml
c=yaml.safe_load(open(sys.argv[1]))
o=c['openstack']
print('image\t'+o['image_id'])
print('flavor\t'+o['control_plane_flavor'])
print('flavor\t'+o['worker_flavor'])
for x in c['clusters']:
 print('network\t'+x['network_id'])
 print('subnet\t'+x['subnet_id'])
PY
)
for fact in "${facts[@]}"; do
  kind=${fact%%$'\t'*}; value=${fact#*$'\t'}
  openstack --os-cloud "$OS_CLOUD_NAME" "$kind" show "$value" -f value -c id >/dev/null
done
AZ=$(python3 - "$CONTRACT" <<'PY'
import sys,yaml
print(yaml.safe_load(open(sys.argv[1]))['openstack']['availability_zone'])
PY
)
AZ_LIST=$(mktemp)
trap 'rm -f "$AZ_LIST"' EXIT
openstack --os-cloud "$OS_CLOUD_NAME" availability zone list --compute -f value -c 'Zone Name' > "$AZ_LIST"
python3 - "$AZ_LIST" "$AZ" <<'PY'
import sys
zones={line.strip() for line in open(sys.argv[1]) if line.strip()}
if sys.argv[2] not in zones: raise SystemExit(f'configured availability zone is unavailable: {sys.argv[2]}')
PY
openstack --os-cloud "$OS_CLOUD_NAME" limits show --absolute
openstack --os-cloud "$OS_CLOUD_NAME" quota show --network
if ! openstack --os-cloud "$OS_CLOUD_NAME" loadbalancer list -f value -c id >/dev/null; then
  printf 'Octavia API or client support is unavailable; the lab API endpoint design requires it.\n' >&2
  exit 3
fi
printf 'read-only OpenStack inventory checks passed; quota sufficiency still requires operator review\n'
