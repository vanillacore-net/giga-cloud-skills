---
name: cloud-decision-gap-discovery
description: Find unanswered cloud decision questions and evidence needs.
version: 0.1.0
metadata:
  hermes:
    tags: [cloud, discovery, governance, decision-support]
---
# Cloud decision gap discovery

Use when a cloud question is broad, premature, or under-specified. It turns the question into bounded decisions and evidence requests rather than filling gaps with plausible assumptions.

## Procedure

1. Restate the decision the requester appears to be making.
2. Identify which of these are known: workload, data and jurisdiction, resilience, integration, operating ownership, skills, contracts, pricing, capacity, connectivity, procurement, and exit constraints.
3. Separate questions that can be answered generically from questions that require local evidence or specialist review.
4. Return the smallest useful decision matrix: question, why it changes the choice, evidence required, accountable local role, and deeper route.
5. If basic facts are missing, stop short of comparing options and explain why.

## Output

```yaml
decision_gaps:
  question:
  decision_impact:
  evidence_needed:
  accountable_role:
  deeper_route:
```

## Boundaries

This skill does not convert uncertainty into a recommendation. Do not disclose internal research or use inaccessible references as evidence.
