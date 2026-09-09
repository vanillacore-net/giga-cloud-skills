---
name: cloud-delivery-model-advisor
description: Compare public-service hosting and cloud delivery options.
version: 0.4.0
author: Karsten Samaschke, Hermes Agent
license: Proprietary
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [cloud, hosting, delivery-model, learning, chapter-1]
    related_skills:
      - giga-cloud-learning-guide
      - workload-cloud-fit-assessment
      - cloud-interoperability-explainer
      - cloud-decision-gap-discovery
---
# Cloud delivery model advisor

Use this Chapter 1 skill to compare operating arrangements for one bounded public-service workload. It separates placement, managed service layer, and operating model so familiar labels do not hide responsibility or dependency choices.

## When to use

- Compare retain-and-improve, owned infrastructure, managed hosting, IaaS, managed containers, managed or self-operated Kubernetes, PaaS, SaaS, or a justified combination.
- Explain why private cloud, hybrid, multi-cloud, or SaaS is not a complete operating arrangement.
- Challenge a cloud-first or label-based recommendation.

Do not use it to select a supplier, approve an architecture, or make a country-specific policy decision.

## Input

```yaml
mode: ask | learn | work | challenge | review
case_id:
service_profile:
options_proposed: []
supplied_constraints: []
supplied_evidence: []
learner_answer:
```

## Decision model

Describe every option on three independent axes:

1. **Placement:** where the service resources run.
2. **Managed service layer:** which technical layer is supplied as a service.
3. **Operating model:** who performs each operating task and under what accountable control.

`hybrid` and `multi_cloud` are combination patterns. They require a stated purpose, named participating arrangements, cross-boundary dependencies, and evidence that the combination can be operated and recovered.

## Procedure

1. Require a `service-profile/v1` or build only the missing profile facts with `workload-cloud-fit-assessment`.
2. Separate supplied facts, assumptions, and gaps before comparing anything.
3. Include retain-and-improve and applicable non-cloud routes. Do not create a cloud-only choice set.
4. Describe each option on the three axes. Name a combination pattern separately.
5. Compare viable options against the same criteria: service fit, accountability and practical control, jurisdiction, operating capacity, connectivity and integration, lifecycle cost and contracts, resilience and recovery, dependencies, portability, and exit.
6. For each material claim, state condition, mechanism, consequence, caveat, and evidence gap. Do not use numeric scoring to create a winner.
7. Return a conditional decision state: `compare`, `investigate`, `reversible_pilot`, or `pause`.

## Learner modes

In `challenge` mode, if no learner claim or attempt is supplied, pose one bounded challenge and stop before the model correction. After the attempt, identify the first unsupported step, explain the correction, and give one retry.

- **Ask:** Answer directly with the three-axis model and one counter-case.
- **Learn:** Give two arrangements with one changed axis and ask the learner to identify the changed responsibilities.
- **Work:** Build the comparison row by row from supplied evidence.
- **Challenge:** Obtain the learner's recommendation first. Test slogans, hidden operating work, shared failure, recovery, cost, and exit.
- **Review:** Check that every option uses the same criteria and that no score or label substitutes for evidence.

## Output

```yaml
option_comparison:
  schema: option-comparison/v1
  case_id:
  options:
    - option_id:
      placement:
      managed_service_layer: retained | iaas | platform | saas | mixed
      operating_model: authority | managed_partner | outsourced | mixed | unknown
      combination_pattern: none | hybrid | multi_cloud
      fit_conditions: []
      trade_offs: []
      evidence_gap_ids: []
  comparison_criteria: []
  decision_state: compare | investigate | reversible_pilot | pause
  prohibited_outcome: numeric_winner_or_provider_recommendation
```

## Challenge checks

Reject automatic claims that private placement proves sovereignty, SaaS removes accountability, multi-cloud proves resilience, open source proves exit, standards prove portability, or outsourcing removes the need for retained competence.

## Sources

Use the [reviewed Chapter 1 revision](https://git.vanillacore.net/giga/content/src/commit/1ad5168a92e0b5187b99ef740e4a9c5f0c251c5b/chapter-1/chapter-1.md). Use current named public sources for delivery-model definitions when needed.

## Pitfalls

- Do not compare labels that describe different axes as if they were peers.
- Do not treat overlapping CaaS, managed Kubernetes, and PaaS contract models as fixed stack layers.
- Whole-life cost includes retained work, integration, controls, recovery, migration, and exit, but local figures require local evidence.

## Verification

The result passes when every option has all three axes, combination patterns have a stated purpose, criteria are applied consistently, assumptions and gaps remain visible, and the result is conditional rather than a provider choice.
