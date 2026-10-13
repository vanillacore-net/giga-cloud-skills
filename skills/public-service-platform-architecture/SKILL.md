---
name: public-service-platform-architecture
description: Frame dependable public-service platform architecture.
version: 0.2.0
author: Karsten Samaschke, Hermes Agent
license: Proprietary
platforms: [linux, macos, windows]
metadata:
  provider: VanillaCore
  hermes:
    tags: [cloud, architecture, iaas, platform, learning, chapter-2]
    related_skills:
      - giga-cloud-learning-guide
      - workload-cloud-fit-assessment
      - cloud-interoperability-explainer
      - cloud-decision-gap-discovery
      - iaas-foundation-practitioner
---
# Public-service platform architecture

Use this Chapter 2 skill to turn an approved service-arrangement decision into the foundation and platform conditions needed for a dependable public service. It owns service-journey, dependency, layering, shared-failure, responsibility, and recovery challenges. It does not configure OpenStack or Kubernetes.

## When to use

- Explain physical, IaaS, platform, shared-capability, and service layers.
- Map an end-to-end service journey and its dependencies.
- Challenge a claim that a running VM, container, Kubernetes cluster, or shared platform proves service recovery.
- Produce a Chapter 2 architecture brief for Chapter 3 practitioners.

## Input

```yaml
mode: ask | learn | work | challenge | review
case_id:
service_arrangement_decision_record:
question:
artifact:
supplied_facts: []
supplied_evidence: []
learner_answer:
```

## Layer model

1. **Physical conditions:** power, cooling, hardware, physical security, facilities, and connectivity.
2. **IaaS:** governed compute, storage, networking, identity, tenant boundaries, APIs, quotas, and controlled administration.
3. **Platform:** runtime, orchestration, deployment, policy, observability, and other capabilities that applications consume.
4. **Shared capability:** identity, certificates, registries, integration, data services, public entry, or another reused service.
5. **Service:** the user journey, application behaviour, records, interfaces, obligations, and accountable outcome.

Virtual machines isolate guest operating environments. Containers package processes while sharing the host kernel. Orchestration coordinates declared workloads. Kubernetes is one orchestration implementation, not the complete platform.

## Procedure

1. Require or reconstruct only from supplied facts the Chapter 1 `service_arrangement_decision_record`. Preserve its gaps.
2. Describe what a person must do to complete the service and receive a trustworthy result.
3. Map each journey step to physical, IaaS, platform, shared, service, and external dependencies. Record supplied ownership without inventing teams.
4. Translate service needs into four foundation conditions: placement and capacity; connectivity and exposure; identity and administration; data, configuration, and recovery.
5. Identify shared dependencies and failure reach. Sharing is justified only under compatible sensitivity, availability, operating ownership, and tolerance for shared failure, or when stronger containment and recovery are evidenced.
6. Separate architectural boundaries from organisational structures. A separate resource state does not prove a separate operating team.
7. Define recovery in user-visible terms. Require access or authentication, correct processing and record state, required interfaces, trustworthy result, and any approved degraded route.
8. Challenge the architecture with one failed dependency while other components remain healthy.
9. Produce the `foundation_readiness_architecture_brief` using the schema below. Route implementation to `iaas-foundation-practitioner` only after Chapter 3 inputs are explicit.

## Learner modes

In `challenge` mode, if no learner claim or attempt is supplied, pose one bounded challenge and stop before the model correction. After the attempt, identify the first unsupported step, explain the correction, and give one retry.

- **Ask:** Give the direct answer, layer, mechanism, failure consequence, and evidence needed.
- **Learn:** Use one public-service request and introduce each layer when the request reaches it. End with a teach-back check.
- **Work:** Build the dependency map and architecture brief with the learner.
- **Challenge:** Obtain the learner's recovery claim first. Then introduce a failed identity, certificate, persistent-data, route, or capacity dependency and grade architecture, content, and evidence separately.
- **Review:** Check layer boundaries, dependency completeness, responsibility claims, service-level recovery proof, chapter scope, and handoff completeness.

## Output

```yaml
foundation_readiness_architecture_brief:
  schema: foundation-readiness-architecture-brief/v1
  case_id:
  inherited_service_decision:
  complete_service_journey: []
  dependency_and_ownership_map: []
  physical_and_connectivity_conditions: []
  iaas_capabilities_and_boundaries: []
  shared_and_isolated_capabilities: []
  platform_responsibility_boundary: []
  continuity_and_recovery_chain: []
  evidence_and_validation_methods: []
  unresolved_assumptions: []
  chapter_3_inputs: []
```

## Challenge checks

Reject these inferences unless the missing service-level evidence is supplied:

- VM `ACTIVE` means the service recovered.
- A replacement Pod means persistent data, certificates, identity, and interfaces recovered.
- Kubernetes is the complete application platform.
- A shared capability is resilient because each consumer is healthy.
- A diagram proves isolation, ownership, recovery, or an independent route.

## Sources

Use the [reviewed Chapter 2 revision](https://git.vanillacore.net/giga/content/src/commit/1ad5168a92e0b5187b99ef740e4a9c5f0c251c5b/chapter-2/chapter-2.md). Use current named public sources for product-specific definitions, but keep product configuration in later skills.

## Pitfalls

- Do not introduce implementation topology to compensate for an incomplete service decision.
- Do not equate tenant separation with physical separation or separate teams.
- Component recovery is evidence about the component only.
- Do not copy organisation-specific architecture or private evidence into a portable learner artifact.

## Verification

The result passes when the complete user journey drives the dependency map, all five layers remain distinct, shared failure and operating boundaries are explicit, recovery uses user-visible checks, unknowns remain visible, and Chapter 3 receives bounded inputs rather than an implied topology.
