---
name: kubernetes-cluster-lifecycle-practitioner
description: Use when learning or operating Kubernetes lifecycle on IaaS.
version: 0.2.0
author: Karsten Samaschke, Hermes Agent
license: Proprietary
platforms: [linux, macos, windows]
metadata:
  provider: VanillaCore
  hermes:
    tags: [giga, kubernetes, cluster-api, capo, gitops, learning, chapter-4]
    related_skills:
      - giga-cloud-learning-guide
      - iaas-foundation-practitioner
      - cloud-interoperability-explainer
---
# Kubernetes cluster lifecycle practitioner

Use this for Chapter 4 learning, implementation coaching, architecture challenges, and syntax-aware review of Kubernetes cluster lifecycle on a validated IaaS foundation. Kubernetes is the orchestration implementation, Cluster API is the cluster lifecycle mechanism, and CAPO is the OpenStack infrastructure mapping.

## When to use

- Explain Kubernetes, Cluster API, CAPO, management clusters, workload clusters, and provider reconciliation.
- Help a learner turn an IaaS baseline into a cluster runtime baseline.
- Prepare, execute, validate, scale, upgrade, reconcile, or clean up the packaged cluster-lifecycle workflow.
- Explore a bounded edge and workload-spoke design, private API reachability, scaling, upgrades, GitOps, and cleanup.
- Challenge cluster ownership, network ranges, load-balancer claims, machine images, or evidence.
- Review Kubernetes, CAPI, CAPO, Argo CD, shell, Ansible, or OpenTofu material for syntax and scope.

Do not use it to claim that a cluster is a complete shared application platform or to deploy an organisation's production environment from example values.

## Input

```yaml
mode: ask | learn | work | challenge | review
operation: assess | prepare | provision | validate | maintain | cleanup
execution: explain | prepare | execute
iaas_technical_baseline:
question:
artifact:
skill_directory:
working_directory:
implementation:
  infrastructure_provider:
  kubernetes_version:
  capi_version:
  provider_version:
local_inputs:
performed_checks:
change_approval:
```

## Architecture model

Teach the lifecycle chain in this order:

1. Kubernetes manages workload state inside a cluster.
2. Cluster API declares and reconciles cluster lifecycle through Kubernetes resources.
3. A bootstrap provider prepares machines, a control-plane provider initializes control-plane Nodes, and an infrastructure provider maps machines and cluster networking to IaaS resources.
4. CAPO is that mapping for OpenStack. It does not replace CAPI or Kubernetes.
5. A seed cluster initially hosts the controllers. A long-lived management cluster owns child-cluster declarations. Workload clusters run service components.
6. Management API traffic and application data traffic are separate paths and need separate evidence.
7. GitOps can own reviewed cluster and workload declarations, but it does not replace provider reconciliation or prove application health.

Read `references/kubernetes-iaas-map.md`, `references/cluster-lifecycle-exercises.md`, `references/technical-validation.md`, and `references/operator-runbook.md` for deeper work. The portable practical kit and its exact source record are under `assets/operator-kit/`.

## Procedure

1. Require an `iaas_technical_baseline`. Do not rediscover or invent its project, images, flavors, networks, quotas, routes, credentials, or identifiers.
2. Define the cluster roles and lifecycle owner before drawing topology. Distinguish seed, management, edge or load-balancer, and workload clusters.
3. Define Node, Pod, and Service ranges, then prove non-overlap with data-centre, VPN, transit, peer-cluster, and IaaS networks. RFC 1918 status alone is insufficient.
4. Establish the machine-image contract. Kubernetes version, operating system, container runtime, kubeadm dependencies, cloud-init behaviour, and provider expectations must be compatible.
5. Establish private management-cluster reachability to every child Kubernetes API before claiming lifecycle control.
6. Distinguish three load-balancing responsibilities: Kubernetes API endpoint, application `Service` integration with an IaaS load balancer, and an optional dedicated edge cluster. Do not collapse them into one resource.
7. Establish cert-manager and a private Contour/Envoy ingress baseline in each child cluster. The application path is `public edge -> private workload-cluster Envoy -> Service -> Pods`; do not expose the workload Envoy directly.
8. Treat the Local Path Provisioner and disposable PersistentVolumeClaim exercise as a bounded storage smoke baseline, not production storage acceptance.
9. Trace ownership and evidence from CAPI Cluster through Machines, IaaS servers, provider IDs, child Nodes and reconciled add-ons.
10. Scale through the owning declaration. Upgrade with a reviewed Kubernetes-version and machine-image pair, pre-upgrade convergence, server-side validation, diff, explicit approval, rollout observation, and workload availability checks.
11. For GitOps, bind every result to an exact repository URL and revision. Separate Argo CD sync and health from CAPI conditions, Node readiness, IaaS state, add-on readiness and workload behaviour.
12. Clean up by stopping higher-level reconciliation first, preserving identifiers, deleting the owning Cluster declaration, waiting with explicit failure states, and proving IaaS absence by ID.
13. In `work` mode with an operation, use `references/operator-runbook.md`. Copy `assets/operator-kit/` to a protected working directory, run its offline validation, and never write local contracts, credentials, rendered live manifests or evidence into the installed skill.
14. Execute a live change only when `execution: execute` is explicit and the runbook's operation-specific gate is complete. Use the host's real tools, capture real output, and stop rather than inventing controller or cloud results.
15. Produce the `cluster_runtime_baseline_record` using the output schema below.

## Operator workflow

The practical path is `Assess -> Prepare -> Provision -> Validate -> Maintain or Cleanup`. `assess`, `prepare`, offline checks and read-only discovery are non-mutating. Provisioning, scaling, upgrades, add-on changes, GitOps changes and cleanup require exact cloud and Kubernetes targets, matching version schemas, reviewed plans or diffs, explicit operation approval, bounded waits and owner-aware recovery.

This skill establishes and maintains the Chapter 4 cluster-lifecycle layer, including the reviewed private Contour/Envoy, cert-manager and storage-smoke baselines. A highly available management plane, production public-edge and TLS configuration, production storage acceptance, backup and recovery, and repository-specific authentication remain explicit platform-operations gaps rather than implied results.

## Learning modes

In `challenge` mode, if no learner claim or attempt is supplied, pose one bounded challenge and stop before the model correction. After the attempt, identify the first unsupported step, explain the correction, and give one retry.

### Ask

Answer directly, then give the generic lifecycle concept, CAPI/CAPO mapping, one counter-case, validation boundary, and named sources.

### Learn

Use one management cluster and two child roles. Ask the learner to identify which API owns each desired state, which controller acts, and what evidence proves convergence.

### Work

Guide **Spec -> Run -> Validation. Repeat.** Keep every environment input explicit and place a continuation criterion after every state change.

### Challenge

Attack provider/version compatibility, image readiness, context selection, CIDR overlap, management API routing, load-balancer ambiguity, exposed workload ingress, missing per-cluster certificates, overstated storage evidence, controller ownership, unsafe scaling or upgrades, Git revision drift, and cleanup order.

### Review

Classify code as conceptual, illustrative, or executable. Apply the validation levels below and return separate architecture, content, syntax, and evidence verdicts.

## Output

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

Every condition, identity link, path test, and lifecycle result must carry its evidence status. `not-tested` or `unverified` is required when live evidence is absent.

## Syntax and evidence levels

- YAML parsing proves document structure only.
- Generic Kubernetes resources may use client-side validation against the installed `kubectl` schema.
- CAPI, CAPO, and Argo CD custom resources need schemas matching the stated versions or server-side dry-run against a cluster with those exact CRDs. Without that, mark schema validity `unverified`.
- Shell, OpenTofu, and Ansible need their native syntax checks. These do not prove cloud or cluster behaviour.
- `kubectl diff` may return 1 when changes exist; a workflow must distinguish that from an execution failure.
- CAPI availability does not by itself prove child Node readiness, CNI, IaaS identity relationships, management API reachability, application routes, or workload health.
- Never invent controller output, conditions, resource IDs, or successful live evidence.

## Sources

Use the commit-pinned portable kit under `assets/operator-kit/`, sourced from the reviewed lab, and the [reviewed Chapter 4 revision](https://git.vanillacore.net/giga/content/src/commit/b56cad92b74b4335de99879415d437b97ab677cd/chapter-4/chapter-4.md) and its linked lab. For version-sensitive syntax and behaviour, prefer current named upstream sources: Kubernetes, Cluster API, CAPO, Argo CD, OpenTofu, Ansible, and the exact CRD or provider schemas used by the artifact.

## Pitfalls

- Do not describe Kubernetes as the complete platform.
- Do not treat a product label or controller status as proof of resilience, sovereignty, portability, or production readiness.
- Do not mutate IaaS resources directly when a higher-level declaration owns them.
- Do not reuse context, namespace, identifier, or kubeconfig values without an explicit executable handoff.
- Do not present compact example replicas, CIDRs, or machine sizes as production recommendations.

## Verification

The result passes only when the IaaS input is explicit, lifecycle ownership is coherent, ranges and routes are checked, versions and images form a reviewed contract, custom-resource syntax has an honest validation status, cross-layer identifiers support the evidence, and cleanup respects controller ownership.
