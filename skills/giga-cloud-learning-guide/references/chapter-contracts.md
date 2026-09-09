# Portable Chapter 1 to 4 contracts

This reference travels with `giga-cloud-learning-guide` during direct installation. It keeps the cross-chapter case and source boundary available without relying on repository-relative files outside the skill folder.

## Route and handoff

| Chapter | Learner question | Required input | Output |
|---|---|---|---|
| 1 | Which operating arrangement is defensible for one public-service workload? | Supplied service and workload facts | `service_arrangement_decision_record` |
| 2 | What must the foundation and platform provide for the service to remain dependable? | Chapter 1 decision record | `foundation_readiness_architecture_brief` |
| 3 | How does IaaS create and prove controlled compute, network, and storage resources? | Chapter 2 architecture brief | `iaas_technical_baseline` |
| 4 | How are Kubernetes clusters created and changed declaratively on that IaaS foundation? | Chapter 3 technical baseline | `cluster_runtime_baseline_record` |

A later chapter may preserve earlier gaps, but it must not silently decide them. Every handoff preserves the same `case_id`, stable fact and finding identifiers, unresolved gaps, and its explicit schema version.

## Minimum handoff fields

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
  decision_rows: []
  accepted_assumptions: []
  evidence_gaps: []
  bounded_outcome: retain_and_improve | investigate | reversible_pilot | redesign | procure_with_conditions | pause
  bounded_next_step:
  evidence_owners: []
  review_trigger:
```

```yaml
foundation_readiness_architecture_brief:
  schema: foundation-readiness-architecture-brief/v1
  case_id:
  inherited_service_decision:
  complete_service_journey: []
  dependency_and_ownership_map: []
  physical_and_connectivity_conditions: []
  iaas_capabilities_and_boundaries: []
  shared_and_isolated_capabilities: []
  platform_responsibility_boundary: []
  continuity_and_recovery_chain: []
  evidence_and_validation_methods: []
  unresolved_assumptions: []
  chapter_3_inputs: []
```

```yaml
iaas_technical_baseline:
  schema: iaas-technical-baseline/v1
  case_id:
  requirement_source:
  platform_and_interface:
  identity_and_administrative_boundary:
  region_and_service_catalogue:
  approved_image_and_compute_inputs:
  compute_and_storage_placement_inputs:
  network_subnet_router_and_exposure_policy:
  quota_and_current_use:
  persistent_data_decision:
  stable_resource_identifiers: []
  cross_service_validation: []
  cleanup_or_retention_decision:
  static_validation: []
  live_validation: []
  assumptions_and_deviations: []
  chapter_4_inputs: []
```

```yaml
cluster_runtime_baseline_record:
  schema: cluster-runtime-baseline-record/v1
  case_id:
  iaas_baseline_reference:
  management_cluster_context:
  provider_and_kubernetes_versions:
  machine_image_contract:
  cluster_roles: []
  node_pod_and_service_ranges:
  api_reachability:
  cluster_api_conditions:
  machine_server_node_identifier_chain: []
  cni_and_node_readiness:
  edge_to_spoke_path_test:
  gitops_scope_and_revision:
  lifecycle_change_evidence: []
  cleanup_or_retention_decision:
  static_validation: []
  live_validation: []
  assumptions_and_deviations: []
```

## Review envelope

```yaml
review:
  architecture:
    verdict: pass | needs-work | unverified
    findings: []
  content:
    verdict: pass | needs-work | unverified
    findings: []
  syntax:
    verdict: pass | needs-work | unverified
    checks_run: []
    findings: []
  evidence:
    verdict: pass | needs-work | unverified
    claims_proved: []
    claims_not_proved: []
  repair_order: []
```

## Reviewed public sources

- [Chapter 1 at reviewed revision](https://git.vanillacore.net/giga/content/src/commit/1ad5168a92e0b5187b99ef740e4a9c5f0c251c5b/chapter-1/chapter-1.md)
- [Chapter 2 at reviewed revision](https://git.vanillacore.net/giga/content/src/commit/1ad5168a92e0b5187b99ef740e4a9c5f0c251c5b/chapter-2/chapter-2.md)
- [Chapter 3 at reviewed revision](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/chapter-3.md)
- [Chapter 3 lab](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/lab/README.md)
- [Chapter 4 at reviewed revision](https://git.vanillacore.net/giga/content/src/commit/6d8d1c004988f3e0fcf72e25f5f2428286a7d883/chapter-4/chapter-4.md)
- [Chapter 4 lab](https://git.vanillacore.net/giga/content/src/commit/6d8d1c004988f3e0fcf72e25f5f2428286a7d883/chapter-4/lab/README.md)

## Source-note rule

The reviewed Chapter 4 scope record assigns broader GitOps integration to Chapter 5, while the reviewed Chapter 4 manuscript and lab already contain a bounded Argo CD exercise for cluster declarations and one demonstration workload. Treat Chapter 4 as the bounded learning exercise and keep broader production platform integration conditional until the source boundary is aligned.

When current sources contradict these reviewed revisions, name both revisions, state which one controls the answer, and keep the affected claim conditional. Never resolve a contradiction silently.
