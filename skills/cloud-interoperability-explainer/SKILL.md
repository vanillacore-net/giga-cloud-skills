---
name: cloud-interoperability-explainer
description: Explain interoperability, portability, and dependencies.
version: 0.4.0
author: Karsten Samaschke, Hermes Agent
license: Proprietary
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [cloud, interoperability, portability, dependency, learning, chapter-1]
    related_skills:
      - giga-cloud-learning-guide
      - cloud-delivery-model-advisor
      - cloud-decision-gap-discovery
---
# Cloud interoperability explainer

Use this skill to explain and challenge exchange, portability, dependency, and exit claims in Chapters 1 to 4. It keeps open standards, open-source software, interoperable exchange, movable assets, and a viable operating exit separate.

## When to use

- A learner needs to distinguish interoperability, portability, and exit.
- An architecture depends on shared identity, APIs, data models, platforms, networks, observability, people, or contracts.
- A claim uses standards, open source, data residency, or multiple providers as automatic proof.

Do not use it to approve a supplier, certify compliance, or infer a viable target environment.

## Input

```yaml
mode: ask | learn | work | challenge | review
case_id:
exchange_or_exit_goal:
supplied_assets: []
supplied_dependencies: []
supplied_evidence: []
learner_answer:
```

## Concept model

- **Interoperability** is meaningful, governed exchange between systems.
- **Portability** is the ability to move named data, configuration, workloads, and operating procedures to a viable target.
- **Exit** is the exercised ability to leave an arrangement while preserving the required service, records, controls, knowledge, and contractual rights.
- **Open standards** specify shared interfaces or representations. **Open-source software** exposes software under a licence. Neither guarantees the other or guarantees an operational outcome.

## Procedure

1. State the exchange or exit purpose in the service context.
2. Identify the mechanism: data model, API, identity federation, runtime contract, repeatable deployment, export, operational process, or contractual right.
3. Record required governance, authority, semantic alignment, identity and security controls, operating ownership, testing, skills, contracts, and target capability.
4. Record each dependency with a stable ID, owner if supplied, supported service, replacement effort, failure reach, recovery route, and review trigger.
5. Mark assets as exchangeable, portable, non-portable, or unproved. Do not infer a complete exit from one export or API.
6. Challenge open-standard and open-source claims separately.
7. Return evidence gaps to `cloud-decision-gap-discovery`.

## Learner modes

In `challenge` mode, if no learner claim or attempt is supplied, pose one bounded challenge and stop before the model correction. After the attempt, identify the first unsupported step, explain the correction, and give one retry.

- **Ask:** Give the direct distinction and apply it to one supplied asset.
- **Learn:** Ask the learner to classify fixed cards such as API, data export, deployment declaration, identity mapping, runbook, contract, and recovery test.
- **Work:** Build the dependency and exit record without filling missing target evidence.
- **Challenge:** Obtain the claim first, then produce the smallest counter-case that breaks it.
- **Review:** Check terms, mechanisms, asset boundaries, owners, evidence, and unsupported causal claims.

## Output

```yaml
interoperability_dependency:
  schema: interoperability-dependency/v1
  case_id:
  exchange_purpose:
  interoperability_conditions: []
  dependencies: []
  portable_assets: []
  non_portable_or_unproved_assets: []
  exit_requirements: []
  open_standard_claims: []
  open_source_claims: []
  evidence_gaps: []
```

Each finding needs an ID, claim, basis, status (`supported`, `conditional`, or `unknown`), mechanism, consequence, and caveat.

## Challenge checks

A shared dependency becomes a common failure domain when no independent path or effective recovery arrangement contains its failure. Multiple providers do not remove a shared identity, network, software, operator, contract, or control-plane dependency.

## Sources

Use the reviewed [Chapter 1](https://git.vanillacore.net/giga/content/src/commit/1ad5168a92e0b5187b99ef740e4a9c5f0c251c5b/chapter-1/chapter-1.md) and [Chapter 2](https://git.vanillacore.net/giga/content/src/commit/1ad5168a92e0b5187b99ef740e4a9c5f0c251c5b/chapter-2/chapter-2.md) revisions. Use named public standards and upstream documentation for version-specific interface claims.

## Pitfalls

- Compatibility between formats does not prove semantic agreement or operating authority.
- Deployment repeatability does not prove data portability or service recovery.
- Data location is one condition, not complete practical control or sovereignty evidence.

## Verification

The result passes when the three terms are distinct, every claim names a mechanism and conditions, dependencies expose their failure reach, portable assets are explicit, and a complete exit is not inferred from a partial interface.
