# Chapter handoff contracts

The handoffs keep a learner's case coherent across Chapters 1 to 4. Unknown local facts remain explicit. A handoff is a learning and review artifact, not production approval.

## Chapter 1 output

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

## Chapter 2 output

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

## Chapter 3 output

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

## Chapter 4 output

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

## Review envelope

Every review mode returns the same four axes:

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

A parser success is not evidence that an environment-specific value is valid. A successful API request is not evidence that a complete service or cross-layer resource chain works.

Every handoff preserves the same `case_id`. Fact, finding, gap, and resource identifiers remain stable across fresh sessions. A consumer rejects an absent required field, an incompatible schema version, an unknown status value, or a conflicting claim that has no reconciliation finding.
