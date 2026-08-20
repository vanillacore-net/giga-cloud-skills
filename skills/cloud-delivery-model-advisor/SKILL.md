---
name: cloud-delivery-model-advisor
description: Frame cloud delivery choices from workload and operating facts.
version: 0.1.0
metadata:
  hermes:
    tags: [cloud, delivery-model, public-sector, decision-support]
---
# Cloud delivery model advisor

Use when an agent needs to frame a cloud delivery-model choice for a described workload. The output is decision support, not a provider recommendation or local architecture approval.

## Input

```yaml
workload:
  purpose:
  data_sensitivity:
  availability_need:
  latency_need:
  integration_dependencies:
  demand_variability:
  locality_constraints:
operating_context:
  skills_and_ownership:
  procurement_constraints:
  regulatory_constraints:
  connectivity:
  exit_requirements:
audience: decision-maker | practitioner | mixed
```

## Procedure

1. State known facts and missing facts separately.
2. Identify viable delivery-model families from the supplied context, without declaring a universal default.
3. Compare fit conditions and material trade-offs: control, security and jurisdiction, operating capacity, integration, connectivity, cost and contracts, resilience, and exit.
4. State local questions that require evidence before a decision.
5. Refer the user to an approved deeper route when the decision needs specialised legal, procurement, security, or technical analysis.

## Output

Return: decision frame, options to examine, fit conditions, trade-offs, missing facts, local questions, and deeper routes.

## Boundaries

Never expose internal research, private source names, document paths, or hidden evidence. Do not select a vendor or make a country-specific decision from generic information.
