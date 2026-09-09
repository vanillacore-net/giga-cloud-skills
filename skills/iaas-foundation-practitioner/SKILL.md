---
name: iaas-foundation-practitioner
description: Use when teaching or reviewing an IaaS technical baseline.
version: 0.1.0
author: Karsten Samaschke, Hermes Agent
license: Proprietary
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [giga, iaas, openstack, opentofu, learning, chapter-3]
    related_skills:
      - giga-cloud-learning-guide
      - public-service-platform-architecture
      - cloud-decision-gap-discovery
---
# IaaS foundation practitioner

Use this for Chapter 3 learning, implementation coaching, architecture challenges, and syntax-aware review of an IaaS technical baseline. Explain the transferable IaaS mechanism first, then map it to OpenStack, Horizon, OpenStackClient, or OpenTofu as a reference implementation.

## When to use

- Explain how identity, images, compute, networking, storage, quota, and placement form one IaaS request.
- Help a learner prepare a bounded IaaS baseline from a Chapter 2 architecture brief.
- Compare a dashboard, CLI, and declarative path without mixing their session state.
- Challenge an OpenStack design or claimed validation result.
- Review OpenStack commands, YAML, shell, or OpenTofu for syntax and evidence limits.

Do not use it to design Kubernetes cluster lifecycle or a complete application platform.

## Input

```yaml
mode: ask | learn | work | challenge | review
architecture_brief:
platform: generic-iaas | openstack | other
interface: concept | horizon | openstackclient | opentofu
question:
artifact:
local_inputs:
performed_checks:
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

Read `references/openstack-iaas-map.md`, `references/iaas-exercises.md`, and `references/technical-validation.md` for deeper work.

## Procedure

1. Confirm the Chapter 2 input: administrative boundary, placement and capacity conditions, connectivity and exposure, identity, data, recovery, and evidence ownership.
2. Select one interface path. Treat Horizon, OpenStackClient, and OpenTofu as fresh alternatives unless the learner explicitly provides a handoff between them.
3. Discover environment-specific values before writing executable steps. Never invent a region, project, image, flavor, availability zone, network, subnet, external network, CIDR, key, credential profile, or UUID.
4. Keep compute and block-storage placement separate. Equal Nova and Cinder availability-zone labels do not prove one shared zone or attachment compatibility.
5. Build the resource chain with stable identifiers. Names help people navigate; IDs establish exact server-port-floating-IP-volume relationships.
6. Validate each layer with the service that owns it. A server status does not prove networking, attached storage, login, an HTTPS service, or public-service recovery.
7. Treat cleanup as an independently executable request. Capture identifiers before deletion, preserve retained data deliberately, stop on failed detach or timeout, and prove absence by ID.
8. Produce the `iaas_technical_baseline` using the output schema below.

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

Use the [reviewed Chapter 3 revision](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/chapter-3.md) and its linked lab. For version-sensitive syntax or API semantics, prefer current named upstream sources: OpenStack service and client documentation, the OpenTofu language documentation, and the OpenStack provider schema used by the artifact.

## Pitfalls

- Do not introduce OpenStack service names before explaining the capability they provide.
- Do not present example catalogue values as defaults.
- Do not mix dynamic outputs from one interface path into another without an explicit, executable handoff.
- Do not accept substring identifier checks or ambiguous name discovery.
- Do not claim that static validation proves live capacity, routing, attachment, recovery, or cleanup.

## Verification

The response or artifact passes only when the capability chain is coherent, every local value is supplied or marked unknown, executable syntax has a named validation status, stable identifiers connect the service records, evidence claims stay within their checks, and the Chapter 4 inputs are explicit.
