# OpenStack compute: provision and change tenant servers

Operate existing tenant compute services; do not install Nova or administer hosts.
Use Linux/macOS CLI or Windows through WSL. The toolkit syntax baseline is
python-openstackclient 8.2.0; cloud policy, microversions, image behavior, and
available features still need local verification.

## Choose the task and teach only the needed distinction

For a new server, ask for workload needs rather than an arbitrary flavor name:
CPU/RAM, boot disk, architecture, image, network, access path, and availability needs.
Explain image versus flavor when it changes the choice; show accepted IDs and
resulting evidence instead of substituting a tutorial for the requested operation.
A private VM with no floating IP and no extra volume is a valid complete result.
An extra Cinder volume or a public address is optional, never a readiness gate.
In review mode, challenge reachability, persistence, quota, and ownership claims.

## Before: scope, capacity, and selected identities

1. Load local `references/operations-api.md`; use only its supported request fields.
   Reuse the coordinator's `openstack-context/v1` case ID, profile, project UUID,
   region, owner, and timeout. Corroborate scope before any server mutation.
2. Resolve resources to UUIDs using permitted tenant reads or caller-supplied IDs.
   The caller selects image, flavor, network/port, keypair, and server identities;
   never take the first item in a list or trust a non-unique display name.
3. Check image architecture, boot source, minimum disk/RAM, guest initialization,
   login user, and supported access method. Flavor capacity alone is not enough.
4. Check selected network/port ownership and addressing, security-group intent,
   availability-zone constraints when required, and boot-volume lifecycle if used.
5. Inspect quotas if permitted. If quota reads return 403, ask for an approved
   capacity budget or flag uncertainty; do not conclude server creation is forbidden.
6. Corroborate ownership per existing server and dependency. A supplied `direct`
   context is not proof. Route OpenTofu, CAPI, or GitOps resources to their owner;
   unknown ownership blocks manual mutations, including “repair” actions.
7. Record stable IDs and baseline state. For changes, agree the maintenance window,
   downtime tolerance, application checks, and realistic recovery path.

Read-only examples after resolving the profile's scope:

```sh
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" image show "$IMAGE_ID" -f json
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" flavor show "$FLAVOR_ID" -f json
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" server show "$SERVER_ID" -f json
```

A denied image/flavor list does not preclude showing an allowed supplied ID.
Do not require service-catalog listing or admin access for these tenant checks.
Never capture user-data secrets, private keys, console credentials, or auth traces.

## Change: private VM, with optional dependencies

Example task: create one small application VM on a supplied private network,
using a caller-approved image/flavor and existing VPN or bastion access.
Decide boot-from-image versus boot-from-volume from persistence requirements.
The helper supports image-backed creation on a network with automatically created
ports only. If boot-from-volume or a precreated port is required, stop and hand off
to the authorized owner workflow; do not silently substitute an image or network.
Decide whether the guest needs SSH keys, configuration data, or neither; keypair
registration stores a public key, not an agent-generated private-key handoff.
If a new network is required, complete networking first and reuse its UUIDs.
If no Cinder service exists, an image-backed VM may still meet the request; explain
local/ephemeral disk lifecycle rather than describing it as persistent storage.

Use the packaged helper copied into the protected operator work directory:

```sh
WORK="$WORK_DIR"
cd "$WORK"
OPS="$WORK/scripts/openstack_ops.py"
python3 "$OPS" inspect --context "$WORK/context.json" --domain "$DOMAIN" --evidence "$WORK/compute-before.json"
python3 "$OPS" prepare --context "$WORK/context.json" --request "$WORK/request.json" --plan "$WORK/compute-plan.json"
python3 "$OPS" execute --plan "$WORK/compute-plan.json" --approve "$APPROVAL_SHA256" --evidence "$WORK/compute-after.json"
```

`DOMAIN`, actions, and request structure come from `references/operations-api.md`.
Review dependency UUIDs, scope, ownership proof, accepted cost, and cleanup impact.
Approve the generated plan's exact SHA256. Reprepare on a changed target or state;
do not bypass an unsupported action with an unreviewed raw CLI mutation.
Poll within `timeout_seconds`; on timeout, reconcile before considering a retry.

## Resize: VERIFY_RESIZE is a decision boundary

Example task: move an owned VM to a larger caller-selected flavor.
Before resize, record old flavor, server/volume/port UUIDs, application health,
and target image/flavor compatibility. Confirm downtime and capacity expectations.
Check whether the cloud and workload support the requested resize; do not assume
live resize, a host change, or an available target from the client syntax alone.
Prepare and approve the resize separately from its later confirmation or reversion.
Nova may enter `VERIFY_RESIZE`; this is neither an error nor a final acceptance.
At that state, verify target flavor, guest boot, network paths, mounted storage,
and application health. Some guest checks require the application owner.
If checks pass, prepare the supported confirm action and obtain its own approval.
If checks fail, prepare the supported revert action while reversion is available;
verify the old flavor and workload afterward. Do not auto-confirm on a timer.
Once confirmed, revert is not a guaranteed rollback; recovery needs a new plan.
If confirmation/reversion is unsupported by this runtime, hand off with exact
server UUID/state and required decision rather than claiming resize is complete.

## After: prove the requested result

- Show the server UUID, expected flavor, boot source, and final lifecycle state.
- Verify ports and fixed addresses using network evidence; `ACTIVE` is not proof
  of SSH reachability, cloud-init success, or application health.
- Test only the agreed VPN/bastion route; no public IP is needed for a private VM.
- Obtain guest/application checks through an approved channel without logging keys.
- Record absent checks explicitly, with their owner and next step.
- Keep full IDs in protected case state; sanitize tenant details for public reports.

## Failure: inspect before another change

For `ERROR`, inspect tenant-visible fault data and instance actions if allowed;
retain sanitized request IDs. A 403 on action/event history does not invalidate
an allowed server read. Escalate only the unavailable diagnostic detail.
For stuck build/resize, capture state and timestamps, and reconcile all returned
UUIDs; a client timeout does not mean no server or migration exists.
For boot/access failure, separate scheduling, guest initialization, routing,
security groups, and guest firewall. Do not resize as a guess at a network fault.
Avoid delete/recreate as an automatic fix: it can destroy boot disks and identity.
Cleanup requires a separately approved owned-resource plan and absence evidence.

## Official documentation

- OpenStackClient Compute v2 Commands: https://docs.openstack.org/python-openstackclient/latest/cli/command-objects/compute/v2/index.html
- Nova Resize: https://docs.openstack.org/nova/latest/user/resize.html
- Nova Server Concepts: https://docs.openstack.org/api-guide/compute/server_concepts.html
