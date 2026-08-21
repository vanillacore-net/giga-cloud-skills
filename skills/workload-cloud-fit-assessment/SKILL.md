---
name: workload-cloud-fit-assessment
description: Profile service facts that shape hosting and cloud choices.
version: 0.2.0
metadata:
  hermes:
    tags: [cloud, hosting, workload, assessment, decision-support]
---
# Workload cloud-fit assessment

Use when an agent has a public-service or workload description and needs a disciplined fact pattern before comparing hosting or cloud options. It profiles the initial signal. It does not select a delivery model.

## Procedure

1. Extract service purpose, users, current hosting condition, data and records, service criticality, availability and recovery need, latency, demand and change pattern, integration dependencies, connectivity, and lifecycle maturity.
2. Record constraints in accountability, jurisdiction, procurement, contracts, operating capability, budget and lifecycle cost, resilience, portability and exit planning.
3. Mark every unsupported assumption as unknown.
4. Explain how each characteristic changes the questions to test. Include retain and improve, non-cloud, managed hosting, infrastructure, platform and SaaS routes where relevant. Do not equate a workload class with a prescribed model.
5. Hand off institution-level questions that workload facts cannot answer, including legal position, operating ownership, supplier terms and exit feasibility.
6. Return the minimum additional evidence needed for a reversible next decision.

## Output

```yaml
service_profile:
  known_facts:
  unknowns:
  option_questions:
  institutional_handoff:
  risks_to_test:
  next_evidence_needed:
```

## Boundaries

This skill gives a structured profile, not a compliance score, procurement decision, provider selection, or country-specific recommendation. Do not reference unpublished chapter materials.