---
name: iaas-foundation-practitioner
description: Use when learning or operating an IaaS technical baseline.
version: 0.3.0
author: Karsten Samaschke, Hermes Agent
license: Proprietary
platforms: [linux, macos, windows]
metadata:
  provider: VanillaCore
  hermes:
    tags: [giga, iaas, openstack, opentofu, learning, chapter-3]
    related_skills:
      - giga-cloud-learning-guide
      - public-service-platform-architecture
      - cloud-decision-gap-discovery
      - openstack-environment
      - openstack-compute
      - openstack-networking
      - openstack-storage
      - openstack-troubleshooting
---
# IaaS foundation practitioner

Use this for Chapter 3 learning, implementation coaching, architecture challenges, and syntax-aware review of an IaaS technical baseline. Explain the transferable IaaS mechanism first, then map it to OpenStack, Horizon, OpenStackClient, or OpenTofu as a reference implementation.

## When to use

- Explain how identity, images, compute, networking, storage, quota, and placement form one IaaS request.
- Help a learner prepare a bounded IaaS baseline from a Chapter 2 architecture brief.
- Prepare, execute, validate, maintain, or clean up the packaged OpenStack tenant-resource workflow.
- Compare a dashboard, CLI, and declarative path without mixing their session state.
- Challenge an OpenStack design or claimed validation result.
- Review OpenStack commands, YAML, shell, or OpenTofu for syntax and evidence limits.

Do not use it to design Kubernetes cluster lifecycle or a complete application platform.

## Input

```yaml
mode: ask | learn | work | challenge | review
operation: assess | prepare | provision | validate | maintain | cleanup
execution: explain | prepare | execute
architecture_brief:
platform: generic-iaas | openstack | other
interface: concept | horizon | openstackclient | opentofu
question:
artifact:
skill_directory:
working_directory:
local_inputs:
performed_checks:
change_approval:
```

## Capability model

Start from the request rather than a product inventory:

1. An identity and administrative boundary controls who may act.
2. Approved images and compute inputs define the requested machine.
3. Network, subnet, router, port, security policy, and external-address relationships define reachability.
4. Block storage has its own lifecycle and placement input.
5. Quota limits permitted allocation; it does not prove physical capacity.
6. Independent service records must agree before the result is accepted.

For OpenStack, map those capabilities to Keystone, Glance, Nova with Placement, Neutron, and Cinder. Horizon and OpenStackClient are alternative interfaces to the service APIs. OpenTofu declares intent through the OpenStack provider and keeps generated state outside Git.

Read `references/openstack-iaas-map.md`, `references/iaas-exercises.md`, `references/technical-validation.md`, and `references/operator-runbook.md` for deeper work. The portable practical kit and its exact source record are under `assets/operator-kit/`.

## Procedure

1. Confirm the Chapter 2 input: administrative boundary, placement and capacity conditions, connectivity and exposure, identity, data, recovery, and evidence ownership.
2. Select one interface path. Treat Horizon, OpenStackClient, and OpenTofu as fresh alternatives unless the learner explicitly provides a handoff between them.
3. Discover environment-specific values before writing executable steps. Never invent a region, project, image, flavor, availability zone, network, subnet, external network, CIDR, key, credential profile, or UUID.
4. Keep compute and block-storage placement separate. Equal Nova and Cinder availability-zone labels do not prove one shared zone or attachment compatibility.
5. Build the resource chain with stable identifiers. Names help people navigate; IDs establish exact server-port-floating-IP-volume relationships.
6. Validate each layer with the service that owns it. A server status does not prove networking, attached storage, login, an HTTPS service, or public-service recovery.
7. Treat cleanup as an independently executable request. Capture identifiers before deletion, preserve retained data deliberately, stop on failed detach or timeout, and prove absence by ID.
8. In `work` mode with an operation, use `references/operator-runbook.md`. Copy `assets/operator-kit/` to a protected working directory, run its offline validation, and never write local values or evidence into the installed skill.
9. Execute a live change only when `execution: execute` is explicit and the runbook's operation-specific gate is complete. Use the host's real tools, preserve real output, and stop rather than inventing a result.
10. Produce the `iaas_technical_baseline` using the output schema below.

## Reusable OpenStack usage

The bundled operator kit below remains the reviewed Chapter 3 learning path. For ordinary work in existing OpenStack projects, activate the installed usage skill that owns the task: `openstack-environment` for inventory and quota, `openstack-compute` for VMs, `openstack-networking` for networks/access, `openstack-storage` for volumes/snapshots, or `openstack-troubleshooting` for diagnosis. Preserve the case, target context, IDs and data decisions. These usage skills are independently usable and do not require a disposable lab project or completion of the chapter.

The usage result is `openstack-operation-record/v1`. Use its actual observations to update the chapter baseline when relevant, without claiming that a single operation meets every baseline requirement. If the usage skill is not installed, return its exact name and task context as a continuation, not invented commands or results. Controller-owned resources continue through their owner; the five skills do not install or operate the OpenStack control plane.

## Operator workflow

The practical path is `Assess -> Prepare -> Provision -> Validate -> Maintain or Cleanup`. `assess`, `prepare`, and static validation are non-mutating. `provision`, mutating maintenance, and `cleanup` require an approved project, protected credentials, supplied environment values, a reviewed request or plan, explicit operation approval, bounded waits, and a predeclared cleanup or retention decision.

Chapter 3 operates tenant resources in an existing OpenStack project. It does not install, upgrade, or repair the OpenStack control plane. If the request crosses that boundary, return it as an unsupported platform-operations requirement.

## Learning modes

In `challenge` mode, if no learner claim or attempt is supplied, pose one bounded challenge and stop before the model correction. After the attempt, identify the first unsupported step, explain the correction, and give one retry.

### Ask

Answer directly, then give the generic mechanism, OpenStack mapping, one failure counter-case, validation boundary, and named sources.

### Learn

Use one small request containing a project, VM, port, security group, persistent volume, and optional external address. Ask the learner to predict which service owns each state before showing the mapping.

### Work

Coach discovery, specification, creation, cross-service read-back, and cleanup. Require a checkable continuation criterion after every state change.

### Challenge

Test identity scope, quota versus capacity, network exposure, compute/storage placement, mutable-name lookup, persistent-data ownership, recovery claims, and whether the evidence connects the complete resource chain.

### Review

Classify every code block as conceptual, illustrative, or executable. Apply the validation levels below and return separate architecture, content, syntax, and evidence verdicts.

## Output

```yaml
iaas_technical_baseline:
  schema: iaas-technical-baseline/v1
  case_id:
  requirement_source:
  platform_and_interface:
  identity_and_administrative_boundary:
  region_and_service_catalogue:
  approved_image_and_compute_inputs:
  compute_and_storage_placement_inputs:
  network_subnet_router_and_exposure_policy:
  quota_and_current_use:
  persistent_data_decision:
  stable_resource_identifiers: []
  cross_service_validation: []
  cleanup_or_retention_decision:
  operator_execution:
    kit_source:
    operation:
    working_directory:
    execution_level: explained | prepared | offline-validated | live-executed
    change_approval:
    checks: []
    changed_resource_ids: []
    evidence: []
    rollback_or_cleanup:
    status: passed | failed | blocked | unverified
  static_validation: []
  live_validation: []
  assumptions_and_deviations: []
  chapter_4_inputs: []
```

`static_validation` and `live_validation` must name the check, result, evidence reference, and strongest supported claim. Empty or unavailable live evidence remains `unverified`.

## Syntax and evidence levels

- JSON or YAML parsing proves structure only.
- `sh -n` or `bash -n` proves shell parsing only.
- OpenTofu needs `fmt`, `init -backend=false`, and `validate` against the declared provider. A saved plan is required to review proposed live changes.
- OpenStackClient options must match the installed client or current official command documentation. `--help` does not prove permissions or environment values.
- Horizon instructions must name the verified navigation path, fields, values, confirmation, expected state, and read-back. A screenshot of an available item does not prove selection.
- Live acceptance requires API read-back with stable IDs. Never fabricate output.

If a required tool, schema, credential, or environment is absent, mark the corresponding result `unverified` and state the exact missing check.

## Sources

Use the commit-pinned portable kit under `assets/operator-kit/`, sourced from the reviewed lab, and the [reviewed Chapter 3 revision](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/chapter-3.md) and its linked lab. For version-sensitive syntax or API semantics, prefer current named upstream sources: OpenStack service and client documentation, the OpenTofu language documentation, and the OpenStack provider schema used by the artifact.

## Pitfalls

- Do not introduce OpenStack service names before explaining the capability they provide.
- Do not present example catalogue values as defaults.
- Do not mix dynamic outputs from one interface path into another without an explicit, executable handoff.
- Do not accept substring identifier checks or ambiguous name discovery.
- Do not claim that static validation proves live capacity, routing, attachment, recovery, or cleanup.

## Verification

The response or artifact passes only when the capability chain is coherent, every local value is supplied or marked unknown, executable syntax has a named validation status, stable identifiers connect the service records, evidence claims stay within their checks, and the Chapter 4 inputs are explicit.
