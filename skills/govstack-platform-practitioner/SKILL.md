---
name: govstack-platform-practitioner
description: Use when learning or operating the GovStack platform.
version: 0.1.0
author: Karsten Samaschke, Hermes Agent
license: Proprietary
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [giga, govstack, platform, openstack, gitops, learning, chapter-5]
    related_skills:
      - giga-cloud-learning-guide
      - kubernetes-cluster-lifecycle-practitioner
      - iaas-foundation-practitioner
---
# GovStack platform practitioner

A single domain practitioner for Chapter 5: understand, prepare, deploy, connect, use, adapt and operate a bounded GovStack platform through real host tools. It consumes the earlier IaaS and cluster-lifecycle decisions rather than replacing them. The existing `giga-cloud-learning-guide` orchestrates the chapter journey; this skill owns the platform operating task, not editorial control.

## When to use

- Explain how an existing OpenStack tenant becomes management/gateway, a dedicated LoadBalancer cluster and **two workload spokes**.
- Prepare or execute a bounded platform deployment, routing test, scaling, replacement, upgrade or retirement with supplied target values.
- Inspect a supplied platform-session, GitOps ownership or platform-runtime handoff; distinguish static checks from live behaviour.
- Continue the same service case into Chapter 6 without silently installing its business workloads.

Do not install the OpenStack control plane, assume a production mandate, collapse the two spokes into one demonstration cluster, or treat the Information Mediator application as installed because its cluster exists.

## Input

Conceptual input shape (empty fields are unknown, not operational defaults):

```yaml
mode: ask | learn | work | challenge | review
operation: assess | prepare | provision | validate | maintain | cleanup
execution: explain | prepare | execute
case_id:
question:
learner_attempt:
iaas_technical_baseline:
cluster_runtime_baseline_record:
platform_runtime_record:
session_file:
skill_directory:
working_directory:
change_approval:
local_inputs: {}
performed_checks: []
```

For practical work, read `references/operator-runbook.md`, `references/session-and-evidence.md`, `references/platform-model.md`, and `references/learner-exercises.md`. They are local to this skill. `scripts/validate_contract.py` validates the JSON handoff and the minimum session boundary without contacting a cloud. The final operator kit belongs at `assets/operator-kit/`; require its real `SOURCE.md`, `MANIFEST.sha256`, `THIRD_PARTY_NOTICES.md` and runnable lab before practical execution. An absent kit is a blocker, not permission to reconstruct scripts from prose.

## Platform model

Teach capabilities before products. An approved tenant supplies compute, image, network, storage and identity resources. The management cluster reconciles CAPI/CAPO child-cluster lifecycle and platform foundations. A gateway provides the reviewed access and forwarding boundary. Argo CD owns declared GitOps objects at exact repository revisions; team workload ownership is distinct from management-owned foundations.

The bounded topology is management/gateway -> LoadBalancer -> two workload spokes: `information-mediator` and `example-workloads`. The session uses role keys `loadbalancer`, `mediator`, `examples`; these are not invented cluster names or IDs. Each child has its own private ingress and per-cluster baseline. The application data path is **public edge -> private per-cluster Envoy -> Service -> Pods**. Private management access to child Kubernetes APIs is a different control path. Prove both paths independently. Do not expose a workload Envoy directly to make a failed edge test pass.

Chapter 5 establishes and operates this runtime and bounded disposable probes. Chapter 6 owns **actual Information Mediator and example workload installation**, configuration, secrets, persistence and business-use evidence. Keep the same case ID, cluster identifiers, domains, evidence gaps and ownership across that boundary. Cluster readiness or a probe response does not prove those applications are installed, usable or recovered.

## Procedure

1. Preserve or establish `case_id`, prior handoffs, stable resource IDs, supplied facts and unresolved gaps. If the request exposes an earlier unresolved IaaS or lifecycle decision, route that gap back instead of hiding it behind a topology.
2. Select the learner mode and `execution` intent independently. Explanation does not authorize mutation. `prepare` permits protected local preparation and approved read-only discovery, not provisioning. Live changes require `execution: execute` and explicit operation approval for the named target and diff.
3. Trace the model above, name the reconciliation owner of each change and choose one bounded goal. Never invent local facts or reuse example CIDRs, DNS, project IDs, images, inventory hosts or Kubernetes contexts as target values.
4. Copy the complete verified kit to a protected working directory outside the installed skill and Git. Check its checksums, reviewed source revisions and offline tests. Stop when any dependency is missing or drifted. Do not write credentials, kubeconfigs, plans, state, rendered manifests or evidence into the installed skill.
5. Establish `platform-session/v1` using `lab/scripts/platform.py init` and supplied values. Before execute, reject missing target values: `bootstrap_repo`, `environment_config`, `inventory`, `infrastructure_outputs`, `image_metadata`, `management_context`, `clusters`, `cluster_configs`, `domains`, `tls`. Read the actual CLI help for flags. Validate the local pinned checkout and its clean reviewed tree, exact contexts, ownership, addresses, quotas, non-overlapping ranges and management reachability. Unknown does not become a default.
6. Follow **Spec -> Run -> Validation. Repeat.** through init/doctor -> bootstrap management/gateway -> render and deploy LoadBalancer -> render and deploy both workload spokes -> route -> probe/status -> bounded use -> scale/replace/upgrade -> explicit cleanup or retention -> handoff. Use `references/operator-runbook.md` for gates and evidence; never skip the second spoke.
7. Before each live operation, require read-only target discovery, offline validation, a reviewed plan or diff, named operation approval, bounded waits, recovery and cleanup ownership. Execute real tools and retain sanitized command/exit/output evidence. Distinguish failure, timeout, partial execution and skipped checks.
8. Treat retirement as **blocked** on the pinned bootstrap source: the current teardown allowlist lacks `workload-argocd` and exact AppProject destinations mismatch the generated destinations. Proceed only if a repaired reviewed source is explicitly selected and its compatibility tests pass. Never weaken the allowlist, strip finalizers or claim successful cleanup to evade this gate. If cleanup is blocked, assess whether provisioning must also stop until an approved recovery/retention plan exists.
9. Return the embedded output below. Set execution level only from checks actually performed: `explained`, `prepared`, `offline-validated`, or `live-executed`. A real attempted mutation may be `live-executed` with `failed` or `blocked`; it is not automatically success. Without live evidence, live validation stays empty and affected claims remain unverified.
10. For Chapter 6, emit the same case and stable identifiers with a bounded installation handoff, retention decision and outstanding gates. Do not create another case or replace resource IDs with names.

## Learning modes

- **ask:** answer first; separate generic concept, GovStack mapping, supplied facts, unknowns, one counter-case, performed checks and named public operational sources.
- **learn:** teach one link in the chain, show its owner and evidence, then ask one bounded check question. Use the current service case, not an invented environment.
- **work:** explain, prepare or execute one operation through real host tools and the runbook. Report unavailable tools, missing values, approvals and source blockers directly. No plausible fabricated command output.
- **challenge:** without a learner claim or attempt, pose one bounded challenge and **stop before the model correction**. After the attempt, identify the first unsupported step, explain the correction and invite one retry. Do not reveal the answer in the initial challenge.
- **review:** independently report architecture, content, syntax and evidence with exact repairs. Parser success is structure only; it cannot establish cloud capacity, routes, application use or cleanup.

## Output

This is a conceptual schema, not a completed run or a set of default target values. Populate claims only from supplied or actually observed evidence. Every evidence item identifies its scope, command/check, result and sanitized evidence reference.

```yaml
platform_runtime_record:
  schema: platform_runtime_record/v1
  case_id:
  prior_handoff_reference:
  session_reference:
  source_revisions: {}
  platform_boundary:
  management_and_gateway: {}
  clusters:
    loadbalancer: {}
    mediator: {}
    examples: {}
  control_path_evidence: []
  public_edge_to_private_envoy_service_pods: []
  domains_and_tls: {}
  gitops_ownership_and_revisions: []
  stable_resource_identifiers: []
  workload_installation_boundary: chapter-6
  use_evidence: []
  adaptation_evidence: []
  cleanup_or_retention_decision:
  cleanup_blockers: []
  operator_execution:
    kit_source:
    operation:
    working_directory:
    execution_level: explained | prepared | offline-validated | live-executed
    change_approval:
    checks: []
    changed_resource_ids: []
    evidence: []
    rollback_or_cleanup:
    status: passed | failed | blocked | unverified
  static_validation: []
  live_validation: []
  assumptions_and_deviations: []
  evidence_gaps: []
  chapter_6_inputs: []
  review:
    architecture: pass | needs-work | unverified
    content: pass | needs-work | unverified
    syntax: pass | needs-work | unverified
    evidence: pass | needs-work | unverified
  bounded_next_action:
```

## Verification

A defensible result preserves the case, all three child roles and two-spoke boundary, public/private ingress separation, explicit local inputs and lifecycle owners. It names the checks actually run and which claims remain unverified. Offline validation never becomes a live deployment or successful retirement claim. Successful live routing requires external request evidence plus the private Envoy -> Service -> Pods chain for **each** spoke; management control reachability is checked separately. Changes require convergence and post-change route/use checks, not only command exit 0. Cleanup requires absence by stable IDs or an explicit retained/blocked result. The Chapter 6 handoff never implies business workload installation from Chapter 5 infrastructure evidence.
