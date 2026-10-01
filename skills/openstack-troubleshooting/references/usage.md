# OpenStack troubleshooting: diagnose tenant failures with evidence

Find the failing layer, preserve resource state, and propose the smallest owned
change. Do not install services, repair control-plane nodes, or request broad admin
credentials. Linux/macOS CLI or Windows WSL uses the same tenant workflow.
The toolkit syntax baseline is python-openstackclient 8.2.0; cloud services,
API behavior, permissions, and microversions must still be checked locally.

## Start from the symptom and desired outcome

Ask for the exact failing action, affected resource UUID, expected result, first
observed time, and any recent change. Prefer these facts over “the cloud is down.”
For “SSH does not work,” clarify VPN/bastion/private versus floating-IP path.
For “volume still small,” clarify API size versus guest block device/filesystem.
For “resize stuck,” distinguish `VERIFY_RESIZE` from a failed or timed-out migration.
Teach the relevant layer distinction as it is needed; do not require a lab exercise
before diagnosing a real incident. In review mode, challenge unsupported conclusions.

## Before: scope, ownership, and observation budget

1. Load local `references/operations-api.md` for supported diagnostic domains/actions.
   Reuse `openstack-context/v1`: stable case ID, caller-selected profile, project UUID,
   region, ownership claim, and timeout. Corroborate scope before any mutation.
2. Record the exact resource identities and current lifecycle states from permitted
   tenant reads. Reconcile returned IDs before guessing what a timed-out action did.
3. Corroborate ownership using controller/state records and resource metadata.
   `unknown` blocks repair mutations; OpenTofu/CAPI/GitOps objects must be repaired
   through their owner. Observation is not authorization to take over resources.
4. Agree what diagnostics are permitted: tenant reads, guest checks, VPN tests,
   and operator escalation. Keep a bounded timeout and stop condition for each.
5. Preserve baseline evidence and sanitized request IDs/timestamps. Do not collect
   credentials, full auth/config dumps, raw debug logs, or secret-bearing user-data.

## Inspect: separate authentication, policy, and object state

Use the selected resource's permitted show, rather than demanding global listing:

```sh
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" server show "$SERVER_ID" -f json
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" port show "$PORT_ID" -f json
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" volume show "$VOLUME_ID" -f json
```

- Local command/parameter error: check `openstack --version` and that command's help
  before diagnosing a service failure. CLI presence is not cloud API verification.
- 401/auth failure: check approved secret source, selected profile, scope, and expiry;
  never print a token to prove authentication or switch identities silently.
- 403: name the denied action and resource. Try only another relevant permitted read.
  Denied action history, catalog, or list access does not block all tenant inspection.
- 404: check UUID, project/region, and policy visibility; absence may be masked access,
  not proof that an object never existed or is safe to recreate.
- 409/conflict: inspect lifecycle/attachment state and concurrent ownership activity;
  repeating a mutation is not a diagnostic strategy.
- Transport timeout/5xx: record timing and request ID where available; correlate
  object state. Do not conclude global outage from one failing request.

No assumption of `endpoint list` or service-catalog listing permission is needed.
If service discovery itself fails, request approved profile/endpoint information
from the operator. Keep the caller's selected identity and least-privilege scope.

## Adaptive diagnostic paths

### VM is ACTIVE but SSH fails

Check compute state, selected port/fixed IP, expected security-group rules, and the
actual VPN/bastion route. A private VM may correctly have no floating IP.
Check source address after VPN NAT, allowed TCP/22 source, return route, and guest
firewall/listener through an approved guest owner. IPv4 success says nothing about
IPv6 rules. Never “test” by opening SSH to the world or rebuilding the VM.
When guest access is unavailable, report the boundary and provide specific checks
for its owner; do not equate API `ACTIVE` with guest or application readiness.

### Resize reaches VERIFY_RESIZE

This state awaits a choice, not an automatic repair. Verify target flavor, guest
boot, attached storage, routes, and application health with the compute owner.
Prepare confirm only after successful checks, or prepare revert while supported
when checks fail. Each mutation needs its own plan and digest approval.
If already confirmed, a revert is not an available guaranteed rollback.

### Volume extended but filesystem unchanged

Compare volume API size, guest device capacity, partition/LVM layer, then filesystem.
If API size is correct, stop repeating Cinder extension. Hand the guest owner a
separate growth/verification task appropriate to the actual OS and filesystem.
An attached disk does not prove safe detach, and a snapshot does not prove a backup.

### Network or server create timed out

Inspect resources by returned UUID and relevant case evidence before retrying.
If no ID was returned, use permitted scoped reads and approved correlation metadata;
if reconciliation is impossible, stop duplicate creation and request operator help.
Record partial success and dependency IDs, not just the client's exit status.
Missing list permission is a bounded visibility gap, not license to create again.

## Change: evidence-backed repairs only

Write a short hypothesis with the observation that supports it and the check that
could disprove it. Prefer a read or authorized traffic test before changing state.
For a supported repair, use the helper copied into protected operator work storage:

```sh
WORK="$WORK_DIR"
cd "$WORK"
OPS="$WORK/scripts/openstack_ops.py"
python3 "$OPS" inspect --context "$WORK/context.json" --domain "$DOMAIN" --resource-id "$RESOURCE_ID" --evidence "$WORK/incident-before.json"
python3 "$OPS" prepare --context "$WORK/context.json" --request "$WORK/request.json" --plan "$WORK/repair-plan.json"
python3 "$OPS" execute --plan "$WORK/repair-plan.json" --approve "$APPROVAL_SHA256" --evidence "$WORK/incident-after.json"
```

Choose `DOMAIN` and supported request/action fields from `references/operations-api.md`.
Review impact, scope, ownership proof, preconditions, and recovery before approving
the exact generated SHA256. Changed state/targets require fresh preparation.
Route controller-managed fixes through the owning tool with stable resource IDs.
Do not force state resets, detach disks, rebuild, or delete/recreate as generic fixes.
If a repair is unsupported, hand off the evidence and required authorized action;
do not invent helper fields or claim an unexecuted operation succeeded.

## After: demonstrate recovery, or make the unresolved boundary actionable

Repeat the originally failing action or authorized equivalent; compare before/after.
Verify API state separately from network reachability, guest state, and application.
State the hypothesis confirmed/refuted, actions actually taken, resulting UUID/state,
missing checks and their owner, and any retained partial resources or recovery risk.
If escalated, provide case ID, project/region, relevant UUIDs, sanitized request IDs,
time window, denied action, observations, and a specific operator question.
Keep detailed identifiers in approved private case state; sanitize public summaries.
Do not label an incident resolved from an unrelated successful list or a quiet log.

## Official documentation

- Nova Compute API Faults: https://docs.openstack.org/api-guide/compute/faults.html
- Nova Resize: https://docs.openstack.org/nova/latest/user/resize.html
- Neutron Introduction to Networking: https://docs.openstack.org/neutron/latest/admin/intro-os-networking.html
- OpenStackClient Command List: https://docs.openstack.org/python-openstackclient/latest/cli/command-list.html
