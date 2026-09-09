---
name: cloud-decision-matrix-steward
description: Maintain an evidence-based public-service hosting matrix.
version: 0.3.0
author: Karsten Samaschke, Hermes Agent
license: Proprietary
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [cloud, hosting, decision-record, evidence, learning, chapter-1]
    related_skills:
      - giga-cloud-learning-guide
      - cloud-delivery-model-advisor
      - cloud-decision-gap-discovery
---
# Cloud decision matrix steward

Use this Chapter 1 skill to reconcile service facts, option comparisons, dependency findings, and evidence gaps into one reviewable decision record for one workload. It supports accountable judgment. It does not select a provider or create a numeric winner.

## When to use

- Several contributors or skills need one shared record.
- A learner needs to turn analysis into a bounded, reviewable next step.
- A matrix needs to be challenged for inconsistent criteria, unsupported scoring, stale evidence, or lost uncertainty.

## Input

```yaml
mode: ask | learn | work | challenge | review
case_id:
workload_id:
arrangement_ids: []
service_profile:
option_comparison:
interoperability_dependency:
decision_gaps:
supplied_evidence: []
learner_answer:
```

## Procedure

1. Require one case, one workload, and named arrangements. Reject generic cloud approval.
2. Use one shared criterion set: service outcome and continuity; data and records; demand and connectivity; integration; accountability and control; jurisdiction; operating capacity; lifecycle cost and contracts; foundation conditions; shared dependencies; interoperability; portability; recovery; and exit.
3. For each criterion, preserve stable fact, finding, and gap IDs. Record requirement, option implications, trade-off, evidence owner, status, next step, and review trigger.
4. Detect contradictions, duplicated criteria, unsupported scores, different criteria applied to different options, and automatic-outcome claims.
5. Use only `sufficient`, `needs_validation`, `decision_blocking`, `reversible_pilot`, or `monitor` as row statuses.
6. Return one bounded outcome: `retain_and_improve`, `investigate`, `reversible_pilot`, `redesign`, `procure_with_conditions`, or `pause`.
7. Produce the Chapter 1 `service_arrangement_decision_record` using the schema below.

## Learner modes

In `challenge` mode, if no learner claim or attempt is supplied, pose one bounded challenge and stop before the model correction. After the attempt, identify the first unsupported step, explain the correction, and give one retry.

- **Ask:** Explain one row and the evidence needed to change its status.
- **Learn:** Ask the learner to repair a row whose score hides contradictory evidence.
- **Work:** Build rows from supplied artifacts without dropping unknowns.
- **Challenge:** Obtain the learner's outcome first, then test whether each decisive row supports it.
- **Review:** Return separate architecture, content, syntax, and evidence findings plus a repair order.

## Output

```yaml
service_arrangement_decision_record:
  schema: service-arrangement-decision-record/v1
  case_id:
  workload_id:
  arrangement_ids: []
  service_outcome:
  users_and_failure_consequences:
  workload_and_data_facts:
  placement_choice:
  managed_service_layer_choice:
  operating_model_choice:
  accountability_and_practical_control:
  dependencies_and_interoperability:
  continuity_and_recovery:
  lifecycle_cost_and_contracts:
  portability_and_exit:
  decision_rows:
    - criterion_id:
      requirement:
      finding_ids: []
      assumption_or_gap_ids: []
      option_implications: {}
      trade_off:
      evidence_owner:
      status: sufficient | needs_validation | decision_blocking | reversible_pilot | monitor
      next_step:
      review_trigger:
  accepted_assumptions: []
  evidence_gaps: []
  bounded_outcome: retain_and_improve | investigate | reversible_pilot | redesign | procure_with_conditions | pause
  bounded_next_step:
  evidence_owners: []
  review_trigger:
```

## Challenge checks

Reject numeric totals, unlabeled assumptions, rows without owners or review triggers, arrangement-specific criteria that prevent comparison, and outcomes that exceed the weakest decision-blocking row.

## Sources

Use the [reviewed Chapter 1 revision](https://git.vanillacore.net/giga/content/src/commit/1ad5168a92e0b5187b99ef740e4a9c5f0c251c5b/chapter-1/chapter-1.md). The final record must distinguish public-source claims, supplied local evidence, and unresolved local evidence.

## Pitfalls

- A matrix is not neutral if its criteria or weights preselect one model.
- `sufficient` applies to the named decision and evidence date, not forever.
- A procurement condition is not evidence that the condition has been met.

## Verification

The result passes when every material criterion is represented once, IDs remain traceable, all arrangements use the same decision frame, gaps and contradictions remain visible, and the bounded outcome follows from the recorded evidence without an invented score.
