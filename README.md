# GIGA Cloud Learning Skills

This repository packages ten public-safe agent skills for Claude Code, Codex, and direct skill installation. Learners can ask questions, learn concepts, build bounded artifacts, challenge claims, review architecture or syntax, and operate the Chapter 3 to 5 practical paths from protected working copies.

## Skill system

`giga-cloud-learning-guide` is the cross-chapter learning coordinator. It keeps one case coherent, selects the earliest chapter that owns an unresolved question, enforces handoff contracts, reconciles conflicting findings, and reports architecture, content, syntax, and evidence separately. It is a skill of skills with its own task, not a directory of names.

| Scope | Skill | Learner result |
|---|---|---|
| Chapters 1 to 5 | `giga-cloud-learning-guide` | Route, mode, handoff continuity, challenge, and final quality envelope |
| Chapter 1 | `workload-cloud-fit-assessment` | A bounded service and workload profile |
| Chapter 1 | `cloud-delivery-model-advisor` | A three-axis operating-arrangement comparison |
| Chapters 1 to 5 | `cloud-interoperability-explainer` | Interoperability, portability, dependency, and exit findings |
| Chapters 1 to 5 | `cloud-decision-gap-discovery` | Prioritised evidence gaps and stop conditions |
| Chapter 1 | `cloud-decision-matrix-steward` | A reviewable service-arrangement decision record |
| Chapter 2 | `public-service-platform-architecture` | A foundation-readiness architecture brief |
| Chapter 3 | `iaas-foundation-practitioner` | An IaaS baseline plus a portable OpenStack tenant-resource operator kit |
| Chapter 4 | `kubernetes-cluster-lifecycle-practitioner` | A cluster-runtime baseline plus a portable CAPI/CAPO operator kit |
| Chapter 5 | `govstack-platform-practitioner` | A platform_runtime_record plus a protected runtime operator path for management/gateway, LoadBalancer and two workload spokes |

The package intentionally uses ten coherent skills rather than separate skills for every OpenStack service, client interface, Kubernetes controller, or lifecycle operation.

## Learning contract

- `ask`: answer directly and separate transferable concepts, product mappings, assumptions, evidence status, and named sources.
- `learn`: teach one bounded concept through a concrete service case, then test understanding.
- `work`: use **Spec -> Run -> Validation. Repeat.** to produce a chapter handoff without inventing local facts.
- `challenge`: obtain the learner's claim or attempted answer, then test assumptions, failure paths, ownership, and evidence.
- `review`: return independent architecture, content, syntax, and evidence verdicts with repair actions.

The machine-readable route and coverage contract is `learning-contract.json`. Human-readable handoffs are in `docs/handoff-contracts.md`. Reviewed chapter revisions and known source tensions are in `docs/source-and-scope-map.md`.

## Practical operator paths

The Chapter 3, Chapter 4 and Chapter 5 practitioner skills include commit-pinned operator kits under their local `assets/operator-kit/` directories. In `work` mode they support `assess`, `prepare`, `provision`, `validate`, `maintain`, and `cleanup` with `explain`, `prepare`, or `execute` intent.

A practical run always copies the kit to a protected working directory. Offline validation runs before environment values are accepted. Live changes require an approved target, protected credentials, supplied local inputs, a reviewed plan or diff, explicit action approval, bounded validation and owner-aware cleanup. The skill returns an `operator_execution` record with real checks and evidence status.

Chapter 3 operates resources inside an existing OpenStack project. Chapter 4 establishes and maintains the Kubernetes cluster-lifecycle layer on that IaaS foundation, including the reviewed per-cluster cert-manager and private Contour/Envoy ingress declarations, bounded storage smoke test, scaling, upgrades, Argo CD path and owner-aware cleanup. Neither skill silently expands into OpenStack control-plane installation or the complete Chapter 5 production platform.

Chapter 5 turns supplied tenant and lifecycle decisions into a bounded GovStack runtime: management/gateway -> LoadBalancer -> information-mediator and example-workloads. It connects public edge -> private per-cluster Envoy -> Service -> Pods, checks bounded use, and supports scaling, replacement, upgrades and explicit cleanup/retention. Actual IM/examples installation is Chapter 6 and preserves the same case and stable IDs. The pinned source has a teardown allowlist/destination mismatch; retirement must be reported blocked unless a repaired reviewed source is selected.

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
python3 scripts/test_operator_kits.py
python3 scripts/test_platform_practitioner.py
```

The first command validates package syntax, manifests, frontmatter, references, relationships, and public-safety markers. The second runs deterministic routing and Chapter 1 to 5 coverage tests. The third verifies checksums, portable paths, script and data syntax, and all three operator kits through their offline suites. The fourth runs positive and mutation tests for Chapter 5 routing, target values, two-spoke and evidence boundaries. These checks validate the package and its offline behaviour, not a live cloud or cluster.
