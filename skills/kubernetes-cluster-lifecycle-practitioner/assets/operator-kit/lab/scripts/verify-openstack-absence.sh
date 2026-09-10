#!/usr/bin/env bash
set -euo pipefail
RECORD=${1:?usage: verify-openstack-absence.sh RESOURCE_IDS_JSON OS_CLOUD}
OS_CLOUD_NAME=${2:?missing OS_CLOUD}
[[ -f "$RECORD" ]] || { printf 'resource ID record not found: %s\n' "$RECORD" >&2; exit 2; }
python3 - "$RECORD" <<'PY'
import json,sys
record=json.load(open(sys.argv[1]))
ids=sum((record.get(key,[]) for key in ('server_ids','port_ids','volume_ids','loadbalancer_ids')),[])
if record.get('captured_before_deletion') is not True or not ids:
 raise SystemExit('resource record must be captured before deletion and contain at least one stable ID')
PY
remaining=0
while IFS=$'\t' read -r kind identifier; do
  [[ -n "$identifier" ]] || continue
  error=$(mktemp)
  if openstack --os-cloud "$OS_CLOUD_NAME" "$kind" show "$identifier" -f value -c id >/dev/null 2>"$error"; then
    printf 'still present: %s %s\n' "$kind" "$identifier" >&2
    remaining=1
  elif ! grep -Eqi 'not found|no .* found|404' "$error"; then
    printf 'absence check failed for %s %s: ' "$kind" "$identifier" >&2
    python3 - "$error" <<'PY'
import sys
print(open(sys.argv[1]).read().strip())
PY
    rm -f "$error"
    exit 3
  fi
  rm -f "$error"
done < <(python3 - "$RECORD" <<'PY'
import json,sys
record=json.load(open(sys.argv[1]))
for key,kind in [('server_ids','server'),('port_ids','port'),('volume_ids','volume'),('loadbalancer_ids','loadbalancer')]:
 for identifier in record.get(key,[]): print(kind+'\t'+identifier)
PY
)
[[ "$remaining" -eq 0 ]] || exit 4
printf 'all captured OpenStack resource IDs are absent\n'
