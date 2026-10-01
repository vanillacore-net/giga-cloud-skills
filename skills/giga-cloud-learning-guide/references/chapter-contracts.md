# Portable Chapter 1 to 5 contracts

This reference travels with `giga-cloud-learning-guide` during direct installation. It keeps the cross-chapter case and source boundary available without relying on repository-relative files outside the skill folder.

## Route and handoff

| Chapter | Learner question | Required input | Output |
|---|---|---|---|
| 1 | Which operating arrangement is defensible for one public-service workload? | Supplied service and workload facts | `service_arrangement_decision_record` |
| 2 | What must the foundation and platform provide for the service to remain dependable? | Chapter 1 decision record | `foundation_readiness_architecture_brief` |
| 3 | How does IaaS create and prove controlled compute, network, and storage resources? | Chapter 2 architecture brief | `iaas_technical_baseline` |
| 4 | How are Kubernetes clusters created and changed declaratively on that IaaS foundation? | Chapter 3 technical baseline | `cluster_runtime_baseline_record` |
| 5 | How is the bounded GovStack runtime deployed, connected, adapted and operated? | IaaS/cluster baselines and supplied target values | `platform_runtime_record` |

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
  reconciled_cluster_addons:
    cert_manager:
    private_contour_envoy_ingress:
    storage_smoke_baseline:
  edge_to_spoke_path_test:
  gitops_scope_and_revision:
  lifecycle_change_evidence: []
  cleanup_or_retention_decision:
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
```

## Chapter 5 output

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

Keep `case_id`, stable resource IDs, session reference, retained ownership and gaps into Chapter 6. Actual Information Mediator and example workload installation belongs to Chapter 6, not this platform-runtime record. No offline check proves live execution.

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
- [Chapter 4 at reviewed revision](https://git.vanillacore.net/giga/content/src/commit/b56cad92b74b4335de99879415d437b97ab677cd/chapter-4/chapter-4.md)
- [Chapter 4 lab](https://git.vanillacore.net/giga/content/src/commit/b56cad92b74b4335de99879415d437b97ab677cd/chapter-4/lab/README.md)

## Chapter 5 operational boundary

Use the independently installed `govstack-platform-practitioner` and its verified local kit. Management/gateway, LoadBalancer and two workload spokes are Chapter 5 runtime scope; actual IM/examples workload installation is Chapter 6. Preserve one case, all three child roles, stable IDs and unresolved gaps. The pinned bootstrap teardown allowlist lacks `workload-argocd` and exact destinations disagree with generated AppProjects: retirement is blocked unless a repaired reviewed source is explicitly selected. Do not imply live operation from offline checks.

## Source-note rule

The reviewed Chapter 4 scope record assigns broader GitOps integration to Chapter 5, while the reviewed Chapter 4 manuscript and lab already contain a bounded Argo CD exercise for cluster declarations and one demonstration workload. Treat Chapter 4 as the bounded learning exercise and keep broader production platform integration conditional until the source boundary is aligned.

When current sources contradict these reviewed revisions, name both revisions, state which one controls the answer, and keep the affected claim conditional. Never resolve a contradiction silently.
