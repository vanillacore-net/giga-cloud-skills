# GIGA Cloud Learning Skills

This repository packages nine public-safe agent skills for Claude Code, Codex, and direct skill installation. Learners can ask questions, learn concepts, build bounded artifacts, challenge claims, and review architecture or syntax across GIGA Cloud Chapters 1 to 4.

## Skill system

`giga-cloud-learning-guide` is the cross-chapter learning coordinator. It keeps one case coherent, selects the earliest chapter that owns an unresolved question, enforces handoff contracts, reconciles conflicting findings, and reports architecture, content, syntax, and evidence separately. It is a skill of skills with its own task, not a directory of names.

| Scope | Skill | Learner result |
|---|---|---|
| Chapters 1 to 4 | `giga-cloud-learning-guide` | Route, mode, handoff continuity, challenge, and final quality envelope |
| Chapter 1 | `workload-cloud-fit-assessment` | A bounded service and workload profile |
| Chapter 1 | `cloud-delivery-model-advisor` | A three-axis operating-arrangement comparison |
| Chapters 1 to 4 | `cloud-interoperability-explainer` | Interoperability, portability, dependency, and exit findings |
| Chapters 1 to 4 | `cloud-decision-gap-discovery` | Prioritised evidence gaps and stop conditions |
| Chapter 1 | `cloud-decision-matrix-steward` | A reviewable service-arrangement decision record |
| Chapter 2 | `public-service-platform-architecture` | A foundation-readiness architecture brief |
| Chapter 3 | `iaas-foundation-practitioner` | An IaaS technical baseline with honest validation status |
| Chapter 4 | `kubernetes-cluster-lifecycle-practitioner` | A Kubernetes cluster-runtime baseline on IaaS |

The package intentionally uses nine coherent skills rather than separate skills for every OpenStack service, client interface, Kubernetes controller, or lifecycle operation.

## Learning contract

- `ask`: answer directly and separate transferable concepts, product mappings, assumptions, evidence status, and named sources.
- `learn`: teach one bounded concept through a concrete service case, then test understanding.
- `work`: use **Spec -> Run -> Validation. Repeat.** to produce a chapter handoff without inventing local facts.
- `challenge`: obtain the learner's claim or attempted answer, then test assumptions, failure paths, ownership, and evidence.
- `review`: return independent architecture, content, syntax, and evidence verdicts with repair actions.

The machine-readable route and coverage contract is `learning-contract.json`. Human-readable handoffs are in `docs/handoff-contracts.md`. Reviewed chapter revisions and known source tensions are in `docs/source-and-scope-map.md`.

## Platform integration

- **Claude Code:** `.claude-plugin/plugin.json` identifies this repository as a Claude plugin and discovers the folders under `skills/`.
- **Codex:** `.codex-plugin/plugin.json` packages the same `skills/` directory. Each skill also has `agents/openai.yaml` metadata.
- **Direct installation:** `docs/install-and-use.md` describes verified checkout installation and the conditions for public-URL installation.

## Data and authority boundary

The repository contains distilled, public-safe learning workflows, contracts, and exercises. It does not contain credentials, internal editorial controls, private evidence, organisation-specific topology, or a production approval. A skill may identify local evidence that is required, but it must not invent that evidence or disclose inaccessible provenance.

## Validation

```bash
python3 scripts/validate_skills.py
python3 scripts/test_learning_paths.py
```

The first command validates package syntax, manifests, frontmatter, references, relationships, and public-safety markers. The second runs deterministic routing and Chapter 1 to 4 coverage tests. These checks validate the package, not a live cloud or cluster.
