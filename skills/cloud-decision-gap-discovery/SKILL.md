---
name: cloud-decision-gap-discovery
description: Prioritize unanswered cloud evidence needs.
version: 0.4.0
author: Karsten Samaschke, Hermes Agent
license: Proprietary
platforms: [linux, macos, windows]
metadata:
  provider: VanillaCore
  hermes:
    tags: [cloud, discovery, governance, evidence, learning, chapter-1]
    related_skills:
      - giga-cloud-learning-guide
      - workload-cloud-fit-assessment
      - cloud-decision-matrix-steward
---
# Cloud decision gap discovery

Use this skill when a cloud or hosting question is premature, contradictory, or missing local evidence. It turns uncertainty into bounded evidence work rather than plausible assumptions.

## When to use

- Required service, architecture, contract, operating, recovery, or exit evidence is absent.
- Specialist outputs disagree.
- A learner needs to decide whether to continue, investigate, pilot, or pause.

Do not use it to turn uncertainty into a recommendation or to assign an owner that was not supplied.

## Input

```yaml
mode: ask | learn | work | challenge | review
case_id:
decision_under_review:
upstream_artifacts: []
supplied_evidence: []
learner_answer:
```

## Procedure

1. Restate the exact decision or continuation gate.
2. Collect referenced `fact_id`, `finding_id`, and `gap_id` values from upstream artifacts. Do not replace identifiers with loose prose.
3. Separate questions answerable from named public sources from questions requiring local legal, contractual, security, operating, capacity, routing, recovery, or exit evidence.
4. Classify each gap as `decision_blocking`, `before_commitment`, `reversible_pilot`, or `monitor`.
5. Record the affected decision, evidence needed, validation method, evidence owner or `local_owner_required`, consequence, and permitted next route.
6. If foundational service facts are absent, stop option comparison. If specialist findings conflict, create a reconciliation gap rather than choosing one silently.
7. Return `decision_gaps/v1` and one bounded action.

## Learner modes

In `challenge` mode, if no learner claim or attempt is supplied, pose one bounded challenge and stop before the model correction. After the attempt, identify the first unsupported step, explain the correction, and give one retry.

- **Ask:** Explain why the named gap blocks or qualifies the decision.
- **Learn:** Present facts and assumptions together and ask the learner to identify which require local evidence.
- **Work:** Produce the evidence register from the supplied artifacts.
- **Challenge:** Ask the learner which conclusion fails if the evidence is absent before revealing the classification.
- **Review:** Check traceability, priority, validation feasibility, ownership, and permitted next route.

## Output

```yaml
decision_gaps:
  schema: decision-gaps/v1
  case_id:
  gaps:
    - gap_id:
      blocked_finding_ids: []
      question:
      decision_impact:
      priority: decision_blocking | before_commitment | reversible_pilot | monitor
      evidence_needed:
      validation_method:
      evidence_owner: supplied_role | local_owner_required
      consequence_if_unresolved:
      next_route:
```

## Challenge checks

Reject a gap record that uses “confirm compliance,” “test resilience,” or similar language without naming the object, method, success condition, owner, and decision consequence. Reject dates, owners, environment values, or successful results that were not supplied.

## Sources

Use the applicable immutable chapter sources listed in the installed sibling skill or the repository source map. Local evidence remains a requested input, not a public citation. If no source map is available, ask for the controlling public revision rather than inventing one.

## Pitfalls

- A long question list is not prioritisation.
- `monitor` is not appropriate for evidence required before an irreversible commitment.
- A reversible pilot needs a bounded scope, success and stop conditions, cleanup, and an owner.

## Verification

The result passes when every gap is traceable, actionable, correctly prioritised, assigned only to a supplied or explicitly unresolved owner, and connected to a next route that does not outrun the evidence.
