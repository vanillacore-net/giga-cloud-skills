---
name: cloud-delivery-model-advisor
description: Compare public-service hosting and cloud delivery options.
version: 0.2.0
metadata:
  hermes:
    tags: [cloud, hosting, delivery-model, public-sector, decision-support]
---
# Cloud delivery model advisor

Use when an agent needs to compare hosting and delivery options for a public service. The output is decision support, not a provider recommendation, local architecture approval, or cloud-first recommendation.

## Input

```yaml
service_or_workload:
  purpose:
  current_hosting:
  data_and_records:
  availability_and_recovery_need:
  demand_and_change_pattern:
  integration_dependencies:
  connectivity:
operating_context:
  accountability_and_ownership:
  skills_and_capacity:
  jurisdiction_and_regulatory_constraints:
  procurement_and_contract_constraints:
  lifecycle_cost_constraints:
  exit_requirements:
audience: decision-maker | practitioner | mixed
```

## Procedure

1. State known facts, assumptions and missing facts separately.
2. Consider the relevant option families without presuming cloud: retain and improve; owned or colocated infrastructure; managed hosting or dedicated infrastructure; rented virtual infrastructure or IaaS; managed platform or PaaS; SaaS; and applicable hybrid or multi-environment arrangements.
3. Compare only viable options against shared criteria: service fit, retained accountability, control and jurisdiction, operating capacity, connectivity and integration, lifecycle cost and contracts, resilience, dependency, portability and exit.
4. State conditions, mechanism, consequence and caveat for material claims. Do not describe cloud, SaaS, open source, standards or multi-cloud as automatic solutions.
5. Return conditional fit, trade-offs, unknowns, local questions, evidence owners and deeper routes. Stop short of recommendation when decision-blocking evidence is absent.

## Output

Return: decision frame, option families to examine, fit conditions, material trade-offs, known facts, unknowns, local questions, evidence owners, and deeper routes.

## Boundaries

Never expose internal research, private source names, document paths, or hidden evidence. Do not select a vendor or make a country-specific decision from generic information.