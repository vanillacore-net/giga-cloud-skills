---
name: kubernetes-cluster-lifecycle-practitioner
description: Use when teaching or reviewing Kubernetes lifecycle on IaaS.
version: 0.1.0
author: Karsten Samaschke, Hermes Agent
license: Proprietary
platforms: [linux, macos, windows]
metadata:
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
- Explore a bounded edge and workload-spoke design, private API reachability, scaling, upgrades, GitOps, and cleanup.
- Challenge cluster ownership, network ranges, load-balancer claims, machine images, or evidence.
- Review Kubernetes, CAPI, CAPO, Argo CD, shell, Ansible, or OpenTofu material for syntax and scope.

Do not use it to claim that a cluster is a complete shared application platform or to deploy an organisation's production environment from example values.

## Input

```yaml
mode: ask | learn | work | challenge | review
iaas_technical_baseline:
question:
artifact:
implementation:
  infrastructure_provider:
  kubernetes_version:
  capi_version:
  provider_version:
local_inputs:
performed_checks:
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

Read `references/kubernetes-iaas-map.md`, `references/cluster-lifecycle-exercises.md`, and `references/technical-validation.md` for deeper work.

## Procedure

1. Require an `iaas_technical_baseline`. Do not rediscover or invent its project, images, flavors, networks, quotas, routes, credentials, or identifiers.
2. Define the cluster roles and lifecycle owner before drawing topology. Distinguish seed, management, edge or load-balancer, and workload clusters.
3. Define Node, Pod, and Service ranges, then prove non-overlap with data-centre, VPN, transit, peer-cluster, and IaaS networks. RFC 1918 status alone is insufficient.
4. Establish the machine-image contract. Kubernetes version, operating system, container runtime, kubeadm dependencies, cloud-init behaviour, and provider expectations must be compatible.
5. Establish private management-cluster reachability to every child Kubernetes API before claiming lifecycle control.
6. Distinguish three load-balancing responsibilities: Kubernetes API endpoint, application `Service` integration with an IaaS load balancer, and an optional dedicated edge cluster. Do not collapse them into one resource.
7. Trace ownership and evidence from CAPI Cluster through Machines, IaaS servers, provider IDs, and child Nodes.
8. Scale through the owning declaration. Upgrade with a reviewed Kubernetes-version and machine-image pair, pre-upgrade convergence, server-side validation, diff, explicit approval, rollout observation, and workload availability checks.
9. For GitOps, bind every result to an exact repository URL and revision. Separate Argo CD sync and health from CAPI conditions, Node readiness, IaaS state, and workload behaviour.
10. Clean up by stopping higher-level reconciliation first, preserving identifiers, deleting the owning Cluster declaration, waiting with explicit failure states, and proving IaaS absence by ID.
11. Produce the `cluster_runtime_baseline_record` using the output schema below.

## Learning modes

In `challenge` mode, if no learner claim or attempt is supplied, pose one bounded challenge and stop before the model correction. After the attempt, identify the first unsupported step, explain the correction, and give one retry.

### Ask

Answer directly, then give the generic lifecycle concept, CAPI/CAPO mapping, one counter-case, validation boundary, and named sources.

### Learn

Use one management cluster and two child roles. Ask the learner to identify which API owns each desired state, which controller acts, and what evidence proves convergence.

### Work

Guide **Spec -> Run -> Validation. Repeat.** Keep every environment input explicit and place a continuation criterion after every state change.

### Challenge

Attack provider/version compatibility, image readiness, context selection, CIDR overlap, management API routing, load-balancer ambiguity, controller ownership, unsafe scaling or upgrades, Git revision drift, and cleanup order.

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
  edge_to_spoke_path_test:
  gitops_scope_and_revision:
  lifecycle_change_evidence: []
  cleanup_or_retention_decision:
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

Use the [reviewed Chapter 4 revision](https://git.vanillacore.net/giga/content/src/commit/6d8d1c004988f3e0fcf72e25f5f2428286a7d883/chapter-4/chapter-4.md) and its linked lab. For version-sensitive syntax and behaviour, prefer current named upstream sources: Kubernetes, Cluster API, CAPO, Argo CD, OpenTofu, Ansible, and the exact CRD or provider schemas used by the artifact.

## Pitfalls

- Do not describe Kubernetes as the complete platform.
- Do not treat a product label or controller status as proof of resilience, sovereignty, portability, or production readiness.
- Do not mutate IaaS resources directly when a higher-level declaration owns them.
- Do not reuse context, namespace, identifier, or kubeconfig values without an explicit executable handoff.
- Do not present compact example replicas, CIDRs, or machine sizes as production recommendations.

## Verification

The result passes only when the IaaS input is explicit, lifecycle ownership is coherent, ranges and routes are checked, versions and images form a reviewed contract, custom-resource syntax has an honest validation status, cross-layer identifiers support the evidence, and cleanup respects controller ownership.
