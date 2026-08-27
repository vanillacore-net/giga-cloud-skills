---
name: cloud-decision-gap-discovery
description: Prioritize unanswered hosting and cloud evidence needs.
version: 0.3.0
metadata:
  hermes:
    tags: [cloud, hosting, discovery, governance, decision-support]
---
# Cloud decision gap discovery

Use when a hosting or cloud question is broad, premature or under-specified. It turns uncertainty into bounded decisions and evidence requests rather than filling gaps with plausible assumptions.

## Procedure

1. Restate the operating or sourcing decision the requester appears to be making.
2. Identify what is known about service purpose, workload, current hosting, data and jurisdiction, resilience, integration, accountability, skills, connectivity, procurement, contracts, lifecycle cost, migration and exit. Include foundation conditions: placement and recovery capacity, public and administrative routes, shared identity or data dependencies, and the responsibility boundary for any platform provider or partner.
3. Separate questions that can be answered generically from questions requiring local evidence or specialist review.
4. Classify every gap as decision-blocking, required before procurement or commitment, suitable for a reversible pilot, or monitor during operation.
5. For each material gap, record the decision affected, evidence owner, validation method, consequence if unresolved and deeper route.
6. If basic facts are missing, stop short of comparing options and explain why.

## Output

```yaml
decision_gaps:
  question:
  decision_impact:
  priority:
  evidence_needed:
  validation_method:
  accountable_role:
  consequence_if_unresolved:
  deeper_route:
```

## Boundaries

This skill does not convert uncertainty into a recommendation. Do not disclose internal research or use inaccessible references as evidence. Do not make a country-specific decision from generic information.