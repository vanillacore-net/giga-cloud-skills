# OpenStack environment: establish a usable tenant context

Use this reference to connect an existing tenant, select the right identities,
and establish what can actually be operated. It does not install a control plane.
Linux and macOS use the local CLI; Windows uses the same workflow inside WSL.
The toolkit's CLI syntax baseline is python-openstackclient 8.2.0, not a promise
that every cloud has the same services, extensions, policies, or API microversions.

## Start from the requested outcome

For “connect me to the project,” establish a working tenant read and scoped evidence.
For “can I run a private VM?”, inspect compute and the selected network; do not
require public addressing or block storage when neither is needed.
Ask only for missing decisions: local cloud profile, project UUID, region,
intended task, timeout, and resource owner. The caller selects identities.
If learning is requested, explain profile versus project scope while performing
these checks. In work mode, produce the context and capability report first.
In challenge/review mode, test the claimed scope and permission assumptions.

## Before: local setup and identity

1. Read the local `references/operations-api.md` for this skill's exact contract.
   Copy the packaged helper into a protected operator work directory as directed
   by the skill. Keep context, plan, request, and evidence files private.
2. Verify the local client with `openstack --version` and command-specific help.
   If absent, install python-openstackclient in a virtual environment under the
   caller's package policy; do not silently upgrade an existing operator environment.
3. Use the caller-selected local `clouds.yaml` profile. Obtain credentials through
   its approved secret source, never chat, a committed file, or a command argument.
   Do not print token issuance, configuration dumps, auth values, or debug traces.
4. Check for conflicting `OS_*` environment overrides without printing their values.
   Resolve conflicts before assuming `--os-cloud` has selected the intended identity.
5. Confirm profile project and region against the context. A successful command
   alone does not establish that it used the requested project.
6. Obtain evidence of scope from a permitted identity read or trusted local auth
   metadata. If token scope cannot be corroborated, stop before a mutation.
   Do not require `project list`, `endpoint list`, or role-assignment listing.

The context uses schema `openstack-context/v1` and contains `case_id`, `cloud`,
`project_id` (UUID), `region`, `ownership`, and `timeout_seconds`.
Ownership is `direct`, `opentofu`, `capi`, `gitops`, or `unknown`; the supplied
value is a claim to corroborate, not permission to change any resource in scope.
Use controller records, configuration/state references, and resource metadata
when available. A name or the absence of a tag is not ownership proof.
Unknown ownership blocks mutations; managed resources go through the owning tool.

## Inspect: capability by action, not one global verdict

Use a permitted tenant read related to the intended task, for example:

```sh
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" server list -f json
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" network show "$NETWORK_ID" -f json
```

Variables here represent caller-selected, corroborated scope and resource UUIDs.
A denied list operation may coexist with an allowed show on a supplied UUID.
A 403 is an action-specific policy result, not proof that all reads or all writes
are forbidden. Record the denied action and try only a relevant permitted read.
Do not probe unrelated resources or switch to a broader identity automatically.
Service-catalog or endpoint-list permission is not a prerequisite for tenant work.
If endpoint discovery fails, request approved profile/service details from the
operator; do not guess URLs or ask for an administrator password.

Record separate outcomes for authentication, compute read, networking read,
block-storage read if needed, and availability of the intended mutation.
A successful list proves that read, not create, delete, attach, or resize permission.
When a service is absent, offer a task variant that does not depend on it; explain
what capability is lost instead of marking the entire environment unusable.

## Change: the common guarded interface

Set `WORK` to the protected work directory, and `DOMAIN` to the domain accepted
by this skill's `references/operations-api.md`. Do not infer action or request keys.
The helper path below is the copied helper, not a script executed in the package.

```sh
WORK="$WORK_DIR"
cd "$WORK"
OPS="$WORK/scripts/openstack_ops.py"
python3 "$OPS" inspect --context "$WORK/context.json" --domain "$DOMAIN" --evidence "$WORK/before.json"
python3 "$OPS" prepare --context "$WORK/context.json" --request "$WORK/request.json" --plan "$WORK/plan.json"
python3 "$OPS" execute --plan "$WORK/plan.json" --approve "$APPROVAL_SHA256" --evidence "$WORK/after.json"
```

Construct the request only from the local contract's supported actions and fields.
Review the generated plan's identities, UUIDs, impact, preconditions, timeout,
ownership proof, and verification steps. Obtain approval for its exact SHA256;
`APPROVAL_SHA256` is that approved digest, not an arbitrary consent string.
A changed context, target, request, or plan requires fresh preparation and approval.
Environment checks do not authorize an unrelated compute/network/storage change.

## After: useful handoff, not a credentials bundle

Produce a per-action capability table with evidence and remaining uncertainty.
State the project UUID, region, selected profile name, verified resource UUIDs,
ownership findings, and case ID in the protected coordinator state.
Do not transfer secret values between skills. A shared case ID and stable UUIDs
are enough to correlate compute, network, storage, and troubleshooting evidence.
Public reports replace tenant identifiers, private endpoints, names, and addresses
with neutral labels; retain detailed evidence only in approved private storage.
Label local syntax checks separately from API evidence and guest/application tests.

## Failure checks and adaptation

- Authentication failure: check local secret availability, scope, CA trust, and
  profile selection. Do not disable certificate validation to get a green check.
- Missing region endpoint: verify the caller's region and intended service before
  changing local configuration. An empty tenant list is not an absent service.
- 403: retain the denied operation and request ID; identify the narrow permission
  required for the chosen task. Continue unrelated permitted checks where useful.
- No quota visibility: use an operator-confirmed budget and report the uncertainty;
  do not assume unlimited capacity or create disposable resources merely to test it.
- Timeout or transport failure: reconcile by resource UUID before any retry.
  Never treat failure to receive a response as proof that a mutation did not occur.

Completion means a corroborated context and actionable capability evidence,
not all services healthy, all permissions granted, or a cloud readiness certificate.

## Official documentation

- OpenStackClient Configuration: https://docs.openstack.org/python-openstackclient/latest/configuration/index.html
- OpenStackClient Command List: https://docs.openstack.org/python-openstackclient/latest/cli/command-list.html
- Keystone Tokens and Scope: https://docs.openstack.org/keystone/latest/admin/tokens-overview.html
