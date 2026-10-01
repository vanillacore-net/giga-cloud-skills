# OpenStack storage: provision, extend, and protect tenant volumes

Use existing Cinder services and tenant permissions; do not configure backends.
Linux/macOS CLI or Windows WSL is supported. The toolkit's CLI syntax baseline
is python-openstackclient 8.2.0, not a guarantee of backend or cloud feature support.
A private VM without an extra volume is valid; storage work starts only when needed.

## Frame the data task before choosing an operation

For “add a data disk,” ask for size in GiB, persistence, volume type, target server,
encryption requirement, and guest/application owner. Explain block device versus
filesystem only where it changes the next step.
For “make the disk bigger,” separate Cinder capacity from partition/filesystem growth.
For “protect this database,” ask for recovery point, downtime, consistency, retention,
and restore testing; do not automatically substitute a snapshot for a backup.
Work mode delivers state evidence and an explicit guest handoff, not a generic lab.
Review/challenge mode tests persistence, consistency, and recovery claims.

## Before: service, scope, and supported capability

1. Read local `references/operations-api.md` and use only supported request fields.
   Reuse the corroborated `openstack-context/v1` case/project/region/profile and
   timeout. Keep context, plans, and evidence in protected local case storage.
2. Resolve caller-selected server, volume, snapshot, and type identities. Use UUIDs
   for existing resources; type/name ambiguity must be resolved before preparation.
3. Corroborate ownership through controller/state records and metadata; a supplied
   `direct` value is not sufficient. Unknown owner blocks changes; controller-managed
   volumes and attachment declarations go through OpenTofu, CAPI, or GitOps.
4. Record volume size, type, status, attachments, boot role, and deletion policy.
   Check available quota if permitted, otherwise record the operator-approved budget.
5. Verify whether the cloud supports the specific operation: creation, attach,
   in-use extension, snapshot, backup, or restore. One success is not proof of others.
6. Agree guest/application owner, maintenance window, backup/recovery prerequisites,
   and encryption handling. Do not print keys, passphrases, or guest credentials.

Read-only examples after validating profile scope:

```sh
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" volume show "$VOLUME_ID" -f json
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" server show "$SERVER_ID" -f json
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" volume snapshot show "$SNAPSHOT_ID" -f json
```

A denied volume-type or snapshot list may still allow a supplied ID to be shown.
A 403 is per action, not evidence that all storage reads or mutations are blocked.
If Cinder is unavailable and only ephemeral compute storage is needed, complete
that compute task without pretending equivalent persistence or backup capability.
Do not require service-catalog access or administer the backend to continue.

## Change example: attach one data volume

Select a size based on durability/performance requirements. The helper creates
volumes with the cloud-default type only, and only when the caller explicitly
accepts that default and its verified semantics. If a custom volume type or
encryption requirement exists, stop and hand off to the authorized owner workflow;
do not silently omit it or invent a type/encryption request field.
Never select “fast” or “encrypted” from a name without verified semantics.
Prepare create, wait for the expected available state, capture the volume UUID,
then separately prepare attachment to the corroborated server if required.
After attachment, verify API attachment IDs and obtain guest block-device evidence.
Guest device names may change; use stable identifiers confirmed by the guest owner.
Formatting/mounting is a separate, destructive guest action requiring its own scope
and approval. Do not format an existing disk because it lacks a known mount point.
Record detach/delete policy: deleting a server must not silently imply deleting data.

## Change example: extend a volume, then hand off filesystem growth

Choose a larger absolute target size in GiB after recording current size; Cinder
extension does not support shrinking. Confirm quota and backup/recovery posture.
Determine whether extension while attached is supported by this cloud/backend.
If not, agree application stop/unmount/detach with the guest owner before a new plan;
never auto-detach a mounted or boot volume to make the API operation succeed.
Prepare and approve the supported extension, then inspect until target API capacity
and expected status are verified within the bounded timeout.
Now hand off separate guest steps: rescan device capacity, inspect partition/LVM
layout, grow the appropriate layer, and grow the filesystem with OS-specific tools.
Ask the guest owner to identify device, partition scheme, filesystem, encryption,
and LVM before choosing commands; do not blindly recommend a Linux grow command.
Verify guest-visible capacity, filesystem size/free space, mount, and application I/O.
Report “Cinder extension complete; guest growth pending” when only API work is done.
No automatic shrink or rollback exists; further recovery needs an explicit plan.

## Guarded execution for supported actions

```sh
WORK="$WORK_DIR"
cd "$WORK"
OPS="$WORK/scripts/openstack_ops.py"
python3 "$OPS" inspect --context "$WORK/context.json" --domain "$DOMAIN" --evidence "$WORK/storage-before.json"
python3 "$OPS" prepare --context "$WORK/context.json" --request "$WORK/request.json" --plan "$WORK/storage-plan.json"
python3 "$OPS" execute --plan "$WORK/storage-plan.json" --approve "$APPROVAL_SHA256" --evidence "$WORK/storage-after.json"
```

Set `DOMAIN`, request keys, and action names from `references/operations-api.md`.
Review target UUIDs, scope, ownership proof, capacity, downtime, and data-loss risks.
Use the exact approved plan SHA256; altered state/targets require fresh preparation.
If the helper does not support a requested snapshot/backup/guest operation, record
that boundary and hand off to its authorized owner; do not invent executable fields.

## Snapshots and backups: name the guarantee accurately

An online snapshot without coordinated quiescing is generally crash-consistent,
not proof of database/application consistency. A force option does not quiesce I/O.
For a quiesced workflow, the application/guest owner flushes or freezes according
to its supported method, confirms the barrier, and coordinates capture completion.
Unfreeze/resume must have a bounded recovery path even if capture fails or times out.
A quiesced snapshot is still a snapshot; do not label it a verified backup.
Cinder backups require the backup service, permitted actions, suitable destination,
retention, and restore verification. A snapshot may share its source failure domain.
Backup completion status alone is not proof that a workload can be restored.
An approved restore test uses a separate target, verifies guest/application data,
and cleans up only owned test resources. Never overwrite production to “test” recovery.

## After and failure checks

- Record final volume UUID, size, status, attachments, and the exact checks performed.
  Keep tenant identifiers private and correlate all evidence through the case ID.
- Report API capacity separately from guest filesystem and application capacity.
- For a timeout, reconcile by UUID before retrying create/attach/extend/snapshot;
  the service may have accepted the operation even if the client got no response.
- For stuck attaching/extending/error states, collect tenant-visible status and
  sanitized request IDs; escalate unavailable details, not broad admin credentials.
- Do not force-delete, reset state, or detach an active disk as a generic fix.
- If guest access is unavailable, assign guest verification to its owner and leave
  completion conditional; do not claim storage usability from `in-use` alone.

## Official documentation

- OpenStackClient Volume v3 Commands: https://docs.openstack.org/python-openstackclient/latest/cli/command-objects/volume/v3/index.html
- Cinder Volume Backups: https://docs.openstack.org/cinder/latest/admin/volume-backups.html
- Block Storage API v3: https://docs.openstack.org/api-ref/block-storage/v3/
