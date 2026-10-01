---
name: openstack-troubleshooting
description: Use when diagnosing OpenStack VM, network or disk faults.
version: 0.1.0
author: Karsten Samaschke, Hermes Agent
license: Proprietary
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [giga, openstack, operations, troubleshooting, chapter-3]
    related_skills:
      - giga-cloud-learning-guide
      - iaas-foundation-practitioner
---
# OpenStack troubleshooting

Read tenant evidence across Nova, Neutron and Cinder, join stable resource IDs, identify observed failures and return a ranked next check or a bounded repair handoff.

This is an operational skill for existing OpenStack environments, independent of the Chapter 3 lab. Teach the mechanism when the user needs it, then use the same tools for actual work. Do not force an experienced user to complete a chapter or create a disposable project.

## When to use

Use for a bounded troubleshooting task in a supplied OpenStack project. Use the chapter practitioner for a full IaaS lesson or chapter handoff. Do not install or repair the OpenStack control plane. Route controller-owned resources to their active OpenTofu, CAPI or GitOps owner rather than changing them underneath that owner.

## Inputs

Collect the task, existing local cloud profile, exact project ID and region, target IDs, ownership evidence, intended resource values and data decisions. Read `references/usage.md` for the domain flow and `references/operations-api.md` for the exact context and action field names supported by the executable helper. Ask only for missing fields needed by this action; do not invent catalogue values or assume admin permissions.

Credentials remain in the operator's protected local configuration. Runtime inputs, plans and evidence belong in a protected working copy, not this installed skill. Bash/POSIX semantics are required for these examples; Windows execution uses WSL. Python 3.10+ and OpenStackClient are required. CLI syntax is checked against OpenStackClient 8.2.0; cloud API behavior and policy are discovered per target.

## Procedure

1. Explain the requested outcome and identify its administrative boundary. Reuse the existing case ID, profile, project, region and stable IDs. A profile is not a permission grant.
2. Resolve the installed skill path and operator-supplied work path. Copy `assets/operator-kit/` to a new protected working directory; verify its checksums before writing local inputs.
3. For inspection, run the read-only command below. Return real permitted results plus unavailable or denied checks. Do not request change approval for a read-only diagnosis.
4. For a change, confirm ownership and data handling, then prepare exactly one supported action. The helper builds a saved plan through a fixed action catalogue; it does not accept arbitrary shell commands. Preparation performs read-only API checks but no cloud mutation.
5. Show the exact target, intended change, dependencies, interruption/data impact, verification and failure continuation. Obtain explicit approval for that saved plan digest. A general request to help or approval of inspection is not mutation approval.
6. Execute only that approved plan. Recheck identity and target before changing state, keep waits bounded, and preserve IDs after creation even if later validation fails. Do not automatically retry a failed create or silently delete partial resources.
7. Read back the affected service state and relationships. Explain what succeeded, what remains, and whether another independently approved operation is needed. Pass the real operation record to the coordinator.

Diagnosis never mutates. A private VM may have no floating IP, and a VM may have no extra volume. Missing optional resources are not automatic faults. Keep API authorization failures distinct from absent resources; guest firewalls, application health and filesystem state remain untested unless separately measured.

## Working commands

Resolve `SKILL_DIR` and `WORK_DIR` from actual host/operator inputs. The paths below are placeholders, not environment defaults.

```bash
set -euo pipefail
SKILL_DIR=/absolute/path/to/installed/openstack-troubleshooting
WORK_DIR=/absolute/path/to/protected/new-operation
umask 077
test ! -e "$WORK_DIR"
mkdir -p "$(dirname "$WORK_DIR")"
cp -R "$SKILL_DIR/assets/operator-kit" "$WORK_DIR"
cd "$WORK_DIR"
python3 scripts/verify_kit.py
python3 scripts/openstack_ops.py --help
```

Create the local context according to `references/operations-api.md`, without credentials, then inspect:

```bash
python3 scripts/openstack_ops.py inspect \
  --context context.json --domain troubleshooting \
  --evidence inspection.json
```

Use a domain-appropriate `--resource-id` for a specific existing target when the API contract requires it. Refer to the bundled action catalogue for supported parameters and complete examples. Environment discovery and troubleshooting are read-only; their next change is routed to the corresponding compute, networking or storage skill.

For a mutating domain, preparation and execution are separate:

```bash
python3 scripts/openstack_ops.py prepare \
  --context context.json --request request.json --plan proposal.json
# Review proposal.json and obtain approval of its exact digest.
APPROVED_PLAN_SHA256=operator_supplied_approved_digest
python3 scripts/openstack_ops.py execute \
  --plan proposal.json --approve "$APPROVED_PLAN_SHA256" \
  --evidence execution.json
```

The shell placeholder is not approval evidence. Never substitute a newly computed digest for one the operator actually approved. Reuse a prior result as evidence, not as authorization to replay a change. There is no automatic rollback guarantee after an API mutation: preserve affected IDs and prepare an explicit recovery or cleanup action.

## Output

Return a concise answer plus the real helper result. The operational contract is `openstack-operation-record/v1`; its required fields and statuses are defined locally in `references/operations-api.md` and produced by the helper. Preserve case identity, domain/action, target project/region, execution level, checks, stable resource IDs, findings, status and bounded next action. Do not turn offline fixture output into cloud evidence.

```yaml
schema: openstack-operation-record/v1
case_id:
domain: troubleshooting
action:
project_id:
region:
execution_level:
checks: []
resource_ids: []
findings: []
status:
next_action:
```

Do not include token values, credentials, raw client stderr, cloud configuration, secret-bearing user data, private keys, state or plan bodies in chat. A local plan can be reviewed at its protected path without publishing its contents. Report a denied operation precisely; it does not establish that all project work is impossible.

## Learning and review

`ask` explains one task. `learn` teaches it through a real or explicitly synthetic case. `work` uses Spec -> Run -> Validation. Repeat. `review` separates syntax, authorization, resource state and service behavior. In `challenge` mode, obtain the learner attempt and stop before the correction when no attempt exists; never run a live mutation merely to demonstrate an answer.

## Verification

The case, project and region match the supplied target. Local values are discovered or explicitly supplied. Each claimed operation is supported by the helper's action catalogue. Preparation did not mutate. Execution required the actual approved plan digest and direct ownership. Evidence names the strongest supported result, records partial failures and keeps guest/application or recovery claims separate from IaaS observations. Verify standalone installation and offline fixtures; live acceptance requires an explicitly approved real target.
