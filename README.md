# GIGA Cloud Learning Skills

This repository packages fifteen public-safe agent skills for Claude Code, Codex and independent checkout installation. The Chapter 1 to 5 learning system includes portable operator kits and is joined by five task-focused OpenStack usage skills for existing tenant environments.

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

The ten chapter and cross-cutting skills remain the learning system. Five task-focused OpenStack skills add practical tenant operations without turning every API command into a separate skill. Each usage skill can be installed alone with its complete local operator kit.

## OpenStack usage toolkit

| Need | Skill |
|---|---|
| Profile/project/region, catalogue, inventory and quota | `openstack-environment` |
| VM creation, lifecycle and resize | `openstack-compute` |
| Networks, subnets, routers, security rules and floating IPs | `openstack-networking` |
| Volumes, attachments, extension and snapshots | `openstack-storage` |
| Cross-service fault diagnosis and repair handoff | `openstack-troubleshooting` |

These are tools for existing tenant environments, not only disposable learning labs. A private VM does not require a floating IP or extra volume. Credentials stay in local OpenStack configuration; service availability and permissions are checked per task. Missing permission for one API is reported without inventing or discarding permitted results.

Each skill includes a standalone `assets/operator-kit/scripts/openstack_ops.py` and local operation contract. It uses OpenStackClient with explicit project and region, read-only inspection, a fixed action catalogue, saved proposals and digest-bound change approval. Inspect and prepare do not mutate cloud resources. Execution checkpoints IDs and reports partial failures rather than automatically replaying or cleaning up. Known controller ownership continues through its owner.

The skill of skills uses a portable operational router for English and German task requests, preserves the case and prior IDs, activates one focused skill and keeps a continuation queue for cross-domain tasks. A routing result is never approval to change state. The Chapter 3 learning baseline and Chapter 4 handoff remain intact.

See [usage and installation](docs/install-and-use.md) and [executable operation contract](docs/openstack-operations-api.md). This release checks OpenStackClient 8.2.0 syntax and offline behavior. It does not claim live acceptance on your cloud.

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
python3 scripts/test_platform_contracts.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

The first command validates package syntax, manifests, frontmatter, references, relationships, and public-safety markers. The second runs deterministic routing and Chapter 1 to 5 coverage tests. The third verifies checksums, portable paths, script and data syntax, and all three operator kits through their offline suites. The platform-contract command checks Chapter 5 schema and evidence boundaries; unittest discovery checks the OpenStack operational toolkit. These checks validate the package and its offline behaviour, not a live cloud or cluster.
