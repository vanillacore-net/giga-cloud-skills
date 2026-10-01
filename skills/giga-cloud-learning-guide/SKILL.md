---
name: giga-cloud-learning-guide
description: Route GIGA Cloud Chapter 1-5 learning and operations.
version: 0.3.0
author: Karsten Samaschke, Hermes Agent
license: Proprietary
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [giga, cloud, learning, tutor, architecture, public-sector]
    related_skills:
      - workload-cloud-fit-assessment
      - cloud-delivery-model-advisor
      - cloud-interoperability-explainer
      - cloud-decision-gap-discovery
      - cloud-decision-matrix-steward
      - public-service-platform-architecture
      - iaas-foundation-practitioner
      - kubernetes-cluster-lifecycle-practitioner
      - govstack-platform-practitioner
---
# GIGA cloud learning guide

Use this as the package entry point for learning and applying GIGA Cloud Chapters 1 to 5. It owns the cross-chapter case, learning mode, scope boundaries, handoffs, and final quality statement. It is not a directory of sibling skills and does not approve a local architecture.

## When to use

Use it when a learner wants to:

- ask a question spanning more than one chapter;
- learn a concept through a public-service case;
- build the Chapter 1 to 5 artifacts in sequence;
- prepare or execute the packaged Chapter 3 to 5 operator workflows;
- challenge an architecture, assumption, or claimed benefit;
- review an artifact for architectural, content, syntax, and evidence quality.

Use a focused skill directly when the question clearly belongs to one chapter and no cross-chapter handoff is needed.

## Input

```yaml
mode: ask | learn | work | challenge | review
chapter: auto | 1 | 2 | 3 | 4 | 5
operation: assess | prepare | provision | validate | maintain | cleanup
execution: explain | prepare | execute
working_directory:
change_approval:
case:
  service_outcome:
  supplied_facts:
  supplied_evidence:
question:
artifact:
constraints:
```

Do not require fields that are irrelevant to the selected mode. Never turn a missing local fact into a plausible default.

## Chapter route

| Chapter | Decision or operating question | Primary output | Focused skill |
|---|---|---|---|
| 1 | Which operating arrangement is defensible for this service? | `service_arrangement_decision_record` | Five decision skills, coordinated by this guide |
| 2 | What must the foundation and platform provide? | `foundation_readiness_architecture_brief` | `public-service-platform-architecture` |
| 3 | How does IaaS create and prove controlled resources? | `iaas_technical_baseline` | `iaas-foundation-practitioner` |
| 4 | How are Kubernetes clusters managed on that IaaS foundation? | `cluster_runtime_baseline_record` | `kubernetes-cluster-lifecycle-practitioner` |
| 5 | How is the GovStack platform deployed, connected, adapted and operated? | `platform_runtime_record` | `govstack-platform-practitioner` |

Read `references/chapter-contracts.md` when the request crosses a chapter boundary. The repository also keeps machine-readable and reviewer-facing copies of these contracts, but this skill must remain usable when installed directly.

## Procedure

1. Select the mode from the user's verb. “Explain” and a direct question select `ask`; “teach” selects `learn`; “help me create” selects `work`; “challenge” or “red-team” selects `challenge`; “check” or “validate” selects `review`.
2. Select the earliest chapter that owns the unresolved decision. Do not solve a Chapter 1 operating-arrangement gap with a Chapter 4 topology.
3. State the current case boundary in one sentence: service or artifact, supplied facts, and the decision under examination. Create or preserve one `case_id`.
4. Select exactly one primary focused skill from the chapter route. Activate it through the host's skill mechanism when available and pass the same `case_id`, mode, supplied facts, evidence, and prior handoff. Add a supporting skill only for a named secondary question.
5. If the focused skill is unavailable, return `focused_skill_required` with its name and the complete handoff. Do not imitate an unavailable specialist with invented detail.
6. Validate each returned artifact against the chapter contract, `case_id`, required IDs, and allowed status values. Preserve unknowns and reject prose aliases that break the handoff.
7. Reconcile specialist findings. When two findings conflict, return a reconciliation finding or decision gap with both bases. Do not silently choose one.
8. For Chapter 3, 4 or 5 `work` requests, preserve `operation`, `execution`, `working_directory`, `change_approval`, and the prior handoff when activating the practitioner skill. Require its portable operator kit for practical execution.
9. For Chapter 5, preserve `platform-session/v1`, all three child roles (`loadbalancer`, `mediator`, `examples`), exact target values, source revisions, approval and execution intent. Validate `platform_runtime_record/v1` and its evidence ladder; offline checks cannot imply live results. Retirement remains blocked on the pinned source unless a repaired reviewed source is explicitly selected. Carry the same case and stable IDs into Chapter 6; actual IM/examples installation belongs there.
10. Apply the selected mode contract below. In challenge mode without a learner attempt, pose the challenge and stop before the model correction.
11. Run the four-axis quality gate, then produce the integrated `architecture_learning_record` below with one bounded next action.

## Integrated output

```yaml
architecture_learning_record:
  schema: architecture-learning-record/v1
  case_id:
  mode: ask | learn | work | challenge | review
  chapter: 1 | 2 | 3 | 4 | 5
  primary_skill:
  supporting_skills: []
  learner_goal:
  execution_scope: guidance | offline-validation | live-change
  operator_execution:
  direct_answer_or_exercise:
  transferable_concepts: []
  reference_implementation_mapping: []
  supplied_facts: []
  assumptions_and_unknowns: []
  chapter_handoff:
  reconciliation_findings: []
  counter_case:
  sources: []
  review:
    architecture: pass | needs-work | unverified
    content: pass | needs-work | unverified
    syntax: pass | needs-work | unverified
    evidence: pass | needs-work | unverified
  bounded_next_action:
```

The record is a synthesis, not a copy of every specialist response. Keep exact IDs in the chapter handoff so a later fresh session can continue the case.

## Mode contracts

### Ask

Put the direct answer first. Then separate:

1. the transferable concept;
2. the reference-implementation mapping, if any;
3. conditions and counter-cases;
4. supplied facts versus assumptions;
5. what has and has not been validated; and
6. named public sources.

### Learn

Teach one concept because the learner needs it for the next decision. Use the current public-service case, contrast it with one counter-case, and end with one check question plus evaluation criteria. Give a worked answer only when requested.

### Work

Guide the learner through **Spec -> Run -> Validation. Repeat.** Produce or update the chapter handoff using supplied facts. Keep unknowns visible, assign evidence owners where known, and stop before a decision-blocking gap would require invention.

For Chapter 3 to 5 practical work, route `assess`, `prepare`, `provision`, `validate`, `maintain`, or `cleanup` to the matching practitioner. Practical execution uses a protected working copy of its `assets/operator-kit/`. Live changes require `execution: execute`, the focused skill's complete operation gate and explicit action approval. Return the real `operator_execution` record; never substitute plausible output when tools, credentials, targets or approval are absent.

### Challenge

Test the strongest claim in the artifact. Look for hidden dependencies, confused responsibility and accountability, shared failure domains, false portability or sovereignty claims, product names used as proof, absent recovery evidence, and claims that exceed the performed validation. Return the counter-case that would break the claim and the evidence needed to keep it.

### Review

Return the review envelope from `references/chapter-contracts.md`. A finding must quote or identify the exact artifact element, explain the failure consequence, and give a bounded repair. Keep parser, schema, environment, and live-behaviour verdicts separate.

## Four-axis quality gate

- **Architecture:** Layers, ownership, trust boundaries, dependencies, failure domains, lifecycle owners, and chapter scope are coherent.
- **Content:** Terms are defined before use, generic capability precedes product mapping, assumptions are labelled, and named public sources support material claims.
- **Syntax:** Every code block is classified as conceptual, illustrative, or executable. Executable material is checked with an appropriate parser or schema tool when available. Missing tooling yields `unverified`, never `valid`.
- **Evidence:** State exactly what each check proves. Static validation does not prove live capacity, routing, reconciliation, recovery, cleanup, or service usability.

## Pitfalls

- Do not turn this guide into a list of skill names. It must maintain the case, mode, handoffs, and final verdict.
- Do not answer a strategic question with implementation detail merely because concrete syntax is available.
- Do not hide contradictory chapter sources. Follow the source-note rule in `references/chapter-contracts.md`.
- Do not cite an internal note, inaccessible path, or anonymous authority.
- Do not claim a command, manifest, or architecture was validated unless the stated check actually ran.
- Do not run or modify the checked-in operator kit in place. Use a protected working copy and preserve its source record.
- Do not treat a request to establish the Chapter 4 cluster layer as proof that Chapter 5 platform operations are complete.

## Verification

A successful response identifies the mode and chapter, uses the correct handoff, answers or exercises the learner's actual question, includes a counter-case, separates generic concepts from product details, reports all four quality axes, and names the sources used.
