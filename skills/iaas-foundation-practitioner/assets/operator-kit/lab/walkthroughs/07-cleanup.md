# 07: Cleanup and absence proof

**Starting state:** Walkthrough 06 passed, stable IDs are preserved and the operator has decided whether `web-01-data` is disposable or must be retained.

**End state:** Disposable resources are absent. A retained volume is `available` and unattached. Every result is checked by stable ID.

**Companion video:** [C3-P7](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/VIDEO_SCOPES.md#user-content-c3-p7-clean-up-without-losing-owned-data)

## Horizon path

1. Open **Project -> Network -> Floating IPs**, disassociate the recorded address, wait for the mapping to clear, then release it.
2. Open **Project -> Volumes -> Volumes**, detach `web-01-data` and wait up to two minutes for **Available**.
3. Open **Project -> Compute -> Instances**, delete `web-01` and wait up to three minutes for its row to disappear.
4. Delete `web-https`.
5. Delete `web-01-data` only when its data owner approved deletion. Otherwise retain it as **Available** and unattached.
6. Refresh the Instances, Ports, Floating IPs, Volumes and Security Groups views. Confirm the named resources are absent or intentionally retained.

Stop immediately on **Error**, timeout or a conflicting ownership decision. Use the stable IDs with OpenStackClient for the final absence proof.

## OpenStackClient path

Load IDs from `evidence/resource-ids.json` before deleting dependencies. This block is valid in a fresh Bash session from `$GIGA_OPERATOR_KIT` and rejects an incomplete evidence file:

```bash
set -euo pipefail
readarray -t evidence_values < <(python3 - <<'PY'
import json
values = json.load(open('evidence/resource-ids.json'))
for key in ('cloud', 'server_id', 'port_id', 'security_group_id', 'floating_ip_id', 'volume_id'):
    value = str(values.get(key, '')).strip()
    if not value:
        raise SystemExit(f'missing evidence value: {key}')
    print(value)
PY
)
[ "${#evidence_values[@]}" -eq 6 ] || exit 1
CLOUD=${evidence_values[0]}
SERVER_ID=${evidence_values[1]}
PORT_ID=${evidence_values[2]}
SECURITY_GROUP_ID=${evidence_values[3]}
FIP_ID=${evidence_values[4]}
VOLUME_ID=${evidence_values[5]}
```

Disassociate the floating IP, detach the volume, then wait for `available` before deleting the server. Delete the floating IP and security group. Delete the volume only when approved.

```bash
FIP=$(openstack --os-cloud "$CLOUD" floating ip show "$FIP_ID" -f value -c floating_ip_address)
openstack --os-cloud "$CLOUD" server remove floating ip "$SERVER_ID" "$FIP"
openstack --os-cloud "$CLOUD" server remove volume "$SERVER_ID" "$VOLUME_ID"

for attempt in $(seq 1 60); do
  status=$(openstack --os-cloud "$CLOUD" volume show "$VOLUME_ID" -f value -c status) || exit 1
  case "$status" in available) break ;; error|error_*) exit 1 ;; esac
  [ "$attempt" -eq 60 ] && exit 1
  sleep 2
done

timeout 180 openstack --os-cloud "$CLOUD" server delete --wait "$SERVER_ID"
openstack --os-cloud "$CLOUD" floating ip delete "$FIP_ID"
openstack --os-cloud "$CLOUD" security group delete "$SECURITY_GROUP_ID"
# Run only after explicit approval:
# openstack --os-cloud "$CLOUD" volume delete "$VOLUME_ID"
```

Use `scripts/verify-absence.sh` with each deleted resource type and stable ID. For a retained volume, query it directly and require `available` with an empty attachment list.

## OpenTofu path

Return to `$GIGA_OPERATOR_KIT/opentofu`. The declaration protects the volume with `prevent_destroy = true`, so a full destroy plan must refuse to delete it.

When the volume must be retained, capture its stable ID in `../evidence/resource-ids.json` and back up the current state to the ignored evidence directory. We then remove only the volume address from OpenTofu state. This makes OpenTofu forget the retained object without deleting it. The attachment remains managed and is removed by the destroy plan.

```bash
set -euo pipefail
umask 077
GIGA_OPERATOR_KIT="${GIGA_OPERATOR_KIT:-$PWD}"
cd "$GIGA_OPERATOR_KIT/opentofu"
mkdir -p ../evidence
readarray -t cleanup_values < <(python3 - <<'PY'
import json
values = json.load(open('../evidence/resource-ids.json'))
for key in ('cloud', 'server_id', 'port_id', 'security_group_id', 'floating_ip_id', 'volume_id'):
    value = str(values.get(key, '')).strip()
    if not value:
        raise SystemExit(f'missing evidence value: {key}')
    print(value)
PY
)
[ "${#cleanup_values[@]}" -eq 6 ] || exit 1
CLOUD=${cleanup_values[0]}
SERVER_ID=${cleanup_values[1]}
PORT_ID=${cleanup_values[2]}
SECURITY_GROUP_ID=${cleanup_values[3]}
FIP_ID=${cleanup_values[4]}
VOLUME_ID=${cleanup_values[5]}
tofu state pull > ../evidence/pre-retain-cleanup.tfstate

tofu state show openstack_blockstorage_volume_v3.data
# Compare its ID with VOLUME_ID in the preserved evidence file.
tofu state rm openstack_blockstorage_volume_v3.data

tofu plan -destroy -out cleanup-retain-volume.tfplan
# Confirm that the Cinder volume is absent from the destroy set.
tofu apply cleanup-retain-volume.tfplan
```

After apply, `tofu state list` must contain none of the managed resource addresses from this recipe:

```bash
tofu state list > ../evidence/post-retain-cleanup-state.txt
python3 - <<'PY'
from pathlib import Path
addresses = Path('../evidence/post-retain-cleanup-state.txt').read_text().splitlines()
managed = [address for address in addresses if not address.startswith('data.')]
if managed:
    raise SystemExit(f'managed resources remain in state: {managed}')
PY

openstack --os-cloud "$CLOUD" volume show "$VOLUME_ID" \
  -f json -c status -c attachments > ../evidence/retained-volume.json
python3 - <<'PY'
import json
volume = json.load(open('../evidence/retained-volume.json'))
if volume.get('status') != 'available':
    raise SystemExit(f"retained volume status is {volume.get('status')!r}")
if volume.get('attachments') not in (None, '', [], {}):
    raise SystemExit('retained volume is still attached')
PY
```

Run the final absence checks below for the server, port, floating IP and security group. Keep the protected state backup until the retained volume has been handed to its owner or imported into its next approved state.

For disposable data only, change `prevent_destroy` to `false` in a reviewed working copy, then run:

```bash
set -euo pipefail
GIGA_OPERATOR_KIT="${GIGA_OPERATOR_KIT:-$PWD}"
cd "$GIGA_OPERATOR_KIT/opentofu"
tofu plan -destroy -out cleanup-delete-volume.tfplan
# Confirm every object and the approved volume deletion.
tofu apply cleanup-delete-volume.tfplan
```

Do not run a fresh normal plan after retaining the volume. The unchanged declaration would propose recreating the disposed compute and network resources. Record the retained-volume state and hand it to its owner before changing or removing the declaration and state under the local state procedure.

## Final proof

```bash
./scripts/verify-absence.sh "$CLOUD" server "$SERVER_ID"
./scripts/verify-absence.sh "$CLOUD" port "$PORT_ID"
./scripts/verify-absence.sh "$CLOUD" floating-ip "$FIP_ID"
./scripts/verify-absence.sh "$CLOUD" security-group "$SECURITY_GROUP_ID"
# Only when deletion was approved:
./scripts/verify-absence.sh "$CLOUD" volume "$VOLUME_ID"
```

For a retained volume on the Horizon or OpenStackClient path, capture and evaluate the same two Cinder fields from `$GIGA_OPERATOR_KIT`:

```bash
openstack --os-cloud "$CLOUD" volume show "$VOLUME_ID" \
  -f json -c status -c attachments > evidence/retained-volume.json
python3 - <<'PY'
import json
volume = json.load(open('evidence/retained-volume.json'))
if volume.get('status') != 'available' or volume.get('attachments') not in (None, '', [], {}):
    raise SystemExit('retained volume is not available and unattached')
print('retained volume is available and unattached')
PY
```

**Stop when:** an API query fails, deletion times out, a resource remains, or the data decision is unresolved. An empty name-based list is not sufficient evidence.
