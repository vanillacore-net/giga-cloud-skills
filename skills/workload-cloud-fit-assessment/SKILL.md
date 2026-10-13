---
name: workload-cloud-fit-assessment
description: Profile service facts for hosting and cloud choices.
version: 0.4.0
author: Karsten Samaschke, Hermes Agent
license: Proprietary
platforms: [linux, macos, windows]
metadata:
  provider: VanillaCore
  hermes:
    tags: [cloud, hosting, workload, assessment, learning, chapter-1]
    related_skills:
      - giga-cloud-learning-guide
      - cloud-delivery-model-advisor
      - cloud-decision-gap-discovery
---
# Workload cloud-fit assessment

Use this Chapter 1 skill to establish the service and workload facts needed before hosting arrangements can be compared. It teaches the service boundary and preserves uncertainty. It does not select a delivery model.

## When to use

- A learner needs to explain why a workload includes service, data, people, interfaces, obligations, and operations rather than application code alone.
- A team needs a reviewable service profile before comparing arrangements.
- A proposed answer needs to be challenged for missing users, failure consequences, recovery needs, dependencies, or evidence.

Do not use it to choose a provider, approve a workload, or invent local legal, contractual, security, or operating facts.

## Input

```yaml
mode: ask | learn | work | challenge | review
case_id:
service_description:
supplied_facts: []
supplied_evidence: []
learner_answer:
```

## Procedure

1. State the public-service outcome, affected users, complete user route, and harm caused by failure or unauthorised change.
2. Bound one workload as service components, data and records, people and operating tasks, interfaces and dependencies, and obligations.
3. Record current arrangement, demand and change pattern, latency, connectivity, availability, degraded route, recovery-time and recovery-point needs, and lifecycle maturity.
4. Classify each statement as `supplied_fact`, `assumption`, or `unknown`. Assign stable `fact_id` or `gap_id` values. Do not infer missing evidence.
5. Explain how each fact or gap changes the questions that an operating-arrangement comparison must test.
6. Route institution-level gaps to `cloud-decision-gap-discovery`. These include local law, procurement, supplier terms, accountable ownership, operating capacity, recovery proof, and exit feasibility.
7. Return `service_profile` and one bounded next step. The profile must remain usable if the next skill runs in a fresh session.

## Learner modes

In `challenge` mode, if no learner claim or attempt is supplied, pose one bounded challenge and stop before the model correction. After the attempt, identify the first unsupported step, explain the correction, and give one retry.

- **Ask:** Answer directly, then distinguish facts, assumptions, unknowns, and the decision consequence.
- **Learn:** Ask the learner to draw the service boundary first. Then correct omissions and give one counter-case.
- **Work:** Build the profile with the learner from supplied facts. Stop when a decision-blocking fact is absent.
- **Challenge:** Obtain the learner's claim or attempted profile before showing the model correction. Test whether component health has been confused with service outcome.
- **Review:** Return architecture, content, syntax, and evidence verdicts. Schema shape is a syntax concern; truth and provenance are evidence concerns.

## Output

```yaml
service_profile:
  schema: service-profile/v1
  case_id:
  public_outcome:
  users_and_routes: []
  workload_boundary:
    service_components: []
    data_and_records: []
    people_and_operations: []
    interfaces_and_dependencies: []
    obligations: []
  known_facts: []
  assumptions: []
  unknowns: []
  continuity_and_recovery_need:
  option_questions: []
  institutional_handoffs: []
  risks_to_test: []
  next_evidence_needed: []
```

Every item in `known_facts`, `assumptions`, and `unknowns` needs a stable ID, a statement, and its basis or required evidence owner.

## Challenge checks

Reject or repair an answer when it:

- starts from a product or the word cloud rather than the service outcome;
- treats a workload as code alone;
- omits users, records, interfaces, operations, or obligations;
- treats an availability percentage as recovery proof;
- converts unknown local facts into defaults; or
- prescribes an arrangement from a workload label.

## Sources

Use the [reviewed Chapter 1 revision](https://git.vanillacore.net/giga/content/src/commit/1ad5168a92e0b5187b99ef740e4a9c5f0c251c5b/chapter-1/chapter-1.md). Use only supplied public facts and named public sources in learner-facing answers.

## Pitfalls

- A service classification does not select a hosting model.
- Retained accountability and performed operating work are different facts.
- A degraded route is useful only when its users, data, authority, and operating conditions are explicit.
- Do not copy private evidence or internal source paths into the profile.

## Verification

The result passes when one workload is bounded, every material statement is typed, the user-visible failure and recovery needs are explicit, unknown local evidence remains unknown, and the next comparison can consume the profile without reconstructing missing context.
