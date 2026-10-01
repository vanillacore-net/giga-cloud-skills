# OpenStack operations API

This is the local execution contract for the standalone `scripts/openstack_ops.py`.
It performs tenant operations through an installed OpenStackClient. Python 3.10+
and POSIX execution are required (Linux/macOS or Windows WSL). OpenStackClient
8.2.0 help was checked for every emitted command prefix and option; that check
makes no API call and does not prove backend behavior or policy authorization.

## Local context

Credentials stay in local OpenStack configuration. Use an existing profile and
an exact project UUID and region, never cloud names inferred from a teaching lab.
Create this file in a protected working copy, substituting actual discovered values:

```json
{
  "schema": "openstack-context/v1",
  "case_id": "your-case-id",
  "cloud": "your-existing-profile",
  "project_id": "REPLACE_WITH_REAL_PROJECT_UUID",
  "region": "your-selected-region",
  "ownership": "unknown",
  "timeout_seconds": 120
}
```

`case_id`, profile and region are short identifiers, not credential bodies.
`timeout_seconds` is an explicit per-call/postcondition budget from 1 to 300 seconds.
`ownership` is `direct`, `opentofu`, `capi`, `gitops` or `unknown`.
Use `unknown` for inspection unless ownership is established. `direct` is an
operator attestation after reviewing controller/state and resource records, not
proof derived from absent tags. Live controller markers override that attestation
for changes; an API cannot universally prove there is no external controller.
A single project may contain differently owned resources. Inspect managed targets
read-only and route their changes through the existing owner.

The helper selects profile, project and region explicitly, then checks the issued
token's project ID. It removes OS_* credential/project/region environment overrides
while retaining local client configuration-file locations. It never prints tokens,
configuration bodies, endpoints, raw client stderr or user-data content.

## Commands

First resolve the installed skill's path and copy the complete operator kit into
a new protected directory. Verify `MANIFEST.sha256` through `scripts/verify_kit.py`
before adding local input. All input, proposals, user-data, receipts and evidence
must remain inside this working root; symlinks, escapes and overwritten output
files are refused. The runtime must not write into an installed skill or source
repository. Keep protected files out of chat and version control.

```bash
cd "$WORK_DIR"
python3 scripts/openstack_ops.py actions
python3 scripts/openstack_ops.py inspect --context context.json \
  --domain environment --evidence inventory.json
python3 scripts/openstack_ops.py inspect --context context.json \
  --domain troubleshooting --resource-id "$SERVER_UUID" --evidence diagnosis.json
```

The global `--work-root "$WORK_DIR"` may be used before the subcommand when the
calling directory differs. For targeted troubleshooting, `--resource-id` is a
server UUID; the helper follows tenant-visible port/network/security/volume
relationships. Missing optional floating IPs or extra volumes are valid outcomes.
Inspection returns successful sanitized values and individual denied/unavailable
checks. Do not treat an authorized list as proof of change permission.

A request has exactly `action` and `parameters`, with the action-specific fields
listed below. It cannot supply arbitrary commands, shell arguments or extra keys.
Existing resource selectors must be UUIDs. Names for newly created resources are
short identifiers. Select images/flavors/networks from actual inspected values.

```json
{"action": "server-stop", "parameters": {"server_id": "REPLACE_WITH_REAL_SERVER_UUID"}}
```

```json
{"action": "subnet-create", "parameters": {"name": "app-subnet", "network_id": "REPLACE_WITH_REAL_NETWORK_UUID", "cidr": "REPLACE_WITH_APPROVED_CIDR"}}
```

```json
{"action": "volume-extend", "parameters": {"volume_id": "REPLACE_WITH_REAL_VOLUME_UUID", "size_gib": 100}}
```

These are input templates, not executable cloud evidence or approved values.
After setting direct ownership and actual selected parameters, prepare one action:

```bash
python3 scripts/openstack_ops.py prepare --context context.json \
  --request request.json --plan proposal.json
```

Prepare does real read-only preflight and creates an immutable proposal. Review
its local target, parameters, disruption/data effect and postconditions. The plan
binds request, identity context, working root, user-data bytes, relevant preflight
state and expiry. A plan is valid for at most 30 minutes; changed relevant state,
work root or user data requires a new proposal and new approval.

Only the operator-approved exact plan SHA-256 is execution authorization:

```bash
python3 scripts/openstack_ops.py execute --plan proposal.json \
  --approve "$OPERATOR_APPROVED_PLAN_SHA256" --evidence execution.json
```

Do not compute a digest yourself and call it operator approval. Execute rechecks
scope/ownership and preconditions before mutation, records an attempt receipt,
checkpoints newly returned IDs before waits, and verifies postconditions. Never
retry creation automatically after timeout or an unknown response. Reconcile the
existing resource IDs and actual cloud state, then prepare any next action.
Execution receipts prevent automatic reuse of the same plan in the approved root.
There is no automatic cross-service rollback guarantee.

## Action catalogue

| Action | Required parameters | Optional parameters |
|---|---|---|
| `server-create` | `name`, `image_id`, `flavor_id`, `network_id`, `security_group_id` | `key_name`, `user_data_file` |
| `server-start` | `server_id` | None |
| `server-stop` | `server_id` | None |
| `server-reboot` | `server_id` | None |
| `server-resize` | `server_id`, `flavor_id` | None |
| `server-resize-confirm` | `server_id` | None |
| `server-resize-revert` | `server_id` | None |
| `server-delete` | `server_id`, `confirm_delete`, `data_policy` | None |
| `network-create` | `name` | None |
| `subnet-create` | `name`, `network_id`, `cidr` | `gateway` |
| `router-create` | `name` | None |
| `router-add-subnet` | `router_id`, `subnet_id` | None |
| `router-set-external` | `router_id`, `external_network_id`, `allow_external` | None |
| `security-group-create` | `name` | None |
| `security-rule-create` | `security_group_id`, `protocol`, `port_min`, `port_max`, `remote_cidr` | `allow_world` |
| `security-rule-delete` | `rule_id`, `confirm_delete` | None |
| `floating-ip-create` | `external_network_id`, `allow_external` | None |
| `floating-ip-associate` | `floating_ip_id`, `port_id`, `fixed_ip`, `allow_external` | None |
| `floating-ip-disassociate` | `floating_ip_id` | None |
| `floating-ip-delete` | `floating_ip_id`, `confirm_delete` | None |
| `volume-create` | `name`, `size_gib` | None |
| `volume-attach` | `server_id`, `volume_id`, `data_policy` | None |
| `volume-detach` | `server_id`, `volume_id`, `data_policy` | None |
| `volume-extend` | `volume_id`, `size_gib` | None |
| `volume-snapshot` | `volume_id`, `name` | None |
| `volume-from-snapshot` | `snapshot_id`, `name`, `size_gib` | None |
| `volume-delete` | `volume_id`, `confirm_delete`, `data_policy` | None |

Protocol support for the security-rule helper is bounded to TCP/UDP. IPv4 and
IPv6 CIDRs are validated; world-wide ranges require explicit `allow_world: true`.
External router/FIP operations require `allow_external: true`. Removal requires
`confirm_delete: true`, and data-bearing deletion requires `data_policy: delete`.
Attach/detach uses `data_policy: retain`. Attachment explicitly disables deletion
on server termination, which OpenStackClient documents as requiring Nova compute
API microversion 2.79 or later. Configure `compute_api_version` in the selected
local cloud profile after checking target support; OS_* version overrides are not
forwarded. If that capability is unavailable, hand off a separately reviewed
attachment workflow rather than silently dropping the retention guarantee.
Boolean acknowledgement fields are part
of a reviewed request; they do not replace the separate approved plan digest.

`user_data_file` is a protected local file inside the work root, not inline
credentials. Its bytes are digest-bound; never publish them. Server creation may
omit key/user-data and floating IPs if the approved workload does not need them.
Resize confirmation/revert are separate plans, allowed only in VERIFY_RESIZE.

This first catalogue extends/deletes/snapshots only available, unattached volumes;
it does not auto-detach active data or boot disks. In-use extension and online
quiesced snapshots need a separate cloud-specific owner workflow. Snapshot restore
creates a new volume; it does not overwrite the source. Guest partition/LVM,
filesystem growth, application quiescing and recovery validation remain separate
approved work. Server deletion refuses attached Cinder volumes so their data
policy cannot be silently changed underneath the workload.

The catalogue does not implement arbitrary port editing, tenant network/router
teardown, Cinder backups or control-plane operations. Route unsupported requests
to an authorized owner rather than inventing request fields or raw mutations.
Use `actions` to inspect the executable inventory; unsupported requests fail closed.

## Result record

The helper produces `openstack-operation-record/v1` with `case_id`, `domain`,
`action`, `project_id`, `region`, `execution_level`, `checks`, `resource_ids`,
`findings`, `status`, `next_action` and optional `plan_hash`. Execution level is
`read-only` or `mutation`. `prepared` is a proposal, not a cloud change; `complete`
means the stated API checks passed, not guest/application acceptance. `partial`
records remaining denied checks or post-change failure. `pending`/`validating`
are persisted checkpoints. `blocked` reports a gate failure. Early malformed
input can yield only schema/status/code/next_action because no valid case exists;
do not fabricate target IDs to fill an invalid context.

Checks identify their actual scope. Inspection findings contain sanitized values
and per-API limitations; operation findings contain bounded failure codes, never
raw stderr. API readiness is not packet-flow, guest health, filesystem usability,
application availability or recovery proof. A private-only VM and no Cinder volume
are legitimate. Keep a stable resource ledger and pass it to the next focused
skill with the case and prior chapter handoff unchanged.

Return code 0 indicates completed inspection or preparation, or verified execution.
Partial mutation and blocked inputs return 2. An inspection can return 0 with
`status: partial`: examine the record, not just the exit code. CLI help and offline
fixtures are separate evidence classes from actual tenant operations.
