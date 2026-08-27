---
name: chapter-2-architecture-guide
description: Turn public-service needs into foundation and platform questions.
version: 0.1.0
metadata:
  hermes:
    tags: [cloud, architecture, iaas, platform, public-sector, chapter-2]
    related_skills:
      - workload-cloud-fit-assessment
      - cloud-delivery-model-advisor
      - cloud-interoperability-explainer
      - cloud-decision-gap-discovery
      - cloud-decision-matrix-steward
---
# Chapter 2 architecture guide

Use when a public-service, education-service or shared digital capability needs a coherent architecture discussion from service need through physical conditions, governed infrastructure, platform responsibility and service readiness. It is the chapter-level entry point for the cloud-skills package.

The skill is decision support. It does not select a provider, prescribe a national topology, configure Kubernetes, create a cluster design, or replace local legal, procurement or security review.

## Input

```yaml
service_context:
  purpose:
  users_and_routes:
  data_and_records:
  availability_and_recovery_need:
  interfaces_and_shared_dependencies:
  current_environment:
  operating_ownership:
  known_constraints:
question:
audience: decision-maker | practitioner | mixed
```

## Procedure

1. Start with the public-service outcome. Identify what users must be able to do, what failure or unauthorised change must be contained, and what proves recovery.
2. Apply `workload-cloud-fit-assessment` to separate known service facts, assumptions and missing evidence.
3. Translate service facts into four foundation questions:
   - placement and capacity;
   - connectivity and exposure;
   - identity and administration;
   - data, configuration and recovery.
4. Identify shared dependencies such as identity, certificates, storage, network routes, monitoring, public entry, provider support and administrative access. Apply `cloud-interoperability-explainer` when the relationship between interoperability, portability and dependencies needs explanation.
5. Use the following boundary rule: share an environment only when data sensitivity, availability need, operating ownership and tolerance for shared failure are comparable. Otherwise identify the local evidence needed for separate administrative, network, capacity or environment boundaries.
6. Explain the runtime transition when it is relevant. Containers package components but do not create a complete trust boundary or recover persistent data. Orchestration coordinates declared workloads but still depends on capacity, storage, identity, network integration and operating policy. Kubernetes is a reference model, not the entire platform.
7. Apply `cloud-delivery-model-advisor` to compare overlapping delivery models: managed container platform or CaaS, managed Kubernetes, self-operated Kubernetes and PaaS. Compare responsibility boundaries, retained competence, contract evidence, recovery and exit conditions. Do not treat the labels as mutually exclusive architecture layers.
8. Apply `cloud-decision-gap-discovery` when service facts, contracts or responsibility boundaries are insufficient for a reversible next decision.
9. Apply `cloud-decision-matrix-steward` when several contributors need one reviewable local record.

## Output

```yaml
chapter_2_architecture_frame:
  service_outcome:
  known_facts:
  foundation_conditions:
    placement_and_capacity:
    connectivity_and_exposure:
    identity_and_administration:
    data_configuration_and_recovery:
  boundaries_and_shared_dependencies:
  runtime_and_platform_implications:
  delivery_model_questions:
  evidence_gaps:
  foundation_readiness_record:
  deeper_routes:
```

## Foundation-readiness record

For each material condition, record:

- the condition and owner;
- the service or platform dependency affected;
- evidence or validation method;
- recovery or exit implication; and
- an unresolved risk or assumption.

The record should be sufficient to challenge the architecture before detailed platform rollout or workload implementation begins.

## Boundaries

Do not claim that cloud, containers, Kubernetes, standards, shared platforms or a managed service automatically provide resilience, isolation, portability, sovereignty or exit. Do not expose internal chapter sources, private evidence, credentials or organisation-specific architecture material.