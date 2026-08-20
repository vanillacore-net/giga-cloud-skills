---
name: workload-cloud-fit-assessment
description: Assess workload facts that shape cloud delivery choices.
version: 0.1.0
metadata:
  hermes:
    tags: [cloud, workload, assessment, decision-support]
---
# Workload cloud-fit assessment

Use when an agent has a workload description but needs a disciplined fact pattern before discussing cloud delivery options.

## Procedure

1. Extract the workload purpose, users, data classes, service criticality, availability target, latency sensitivity, peak demand, integration dependencies, and lifecycle maturity.
2. Record constraints in governance, procurement, regulation, connectivity, operating capability, budget model, and exit planning.
3. Mark every unsupported assumption as unknown.
4. Explain how each characteristic changes the delivery decision. Do not equate a workload class with one prescribed cloud model.
5. Return the minimum additional evidence needed to make the next decision.

## Output

```yaml
workload_profile:
  known_facts:
  unknowns:
  decision_implications:
  risks_to_test:
  next_evidence_needed:
```

## Boundaries

This skill gives a structured assessment, not a compliance score, procurement decision, or provider selection. Do not reference unpublished chapter materials.
