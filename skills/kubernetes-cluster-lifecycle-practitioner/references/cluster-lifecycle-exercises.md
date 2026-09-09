# Chapter 4 learner exercises

Use one bounded exercise at a time. Ask for the learner's answer before revealing a model correction in challenge mode.

## 1. Kubernetes and Cluster API teach-back

**Task:** Explain the progression from VM to container to Pod to Kubernetes cluster to Cluster API-managed cluster. For each step, name the added responsibility and one responsibility that remains below it.

**Pass conditions:** Containers do not receive a separate guest kernel. Kubernetes owns Pod scheduling and workload reconciliation. CAPI plus its providers owns cluster and machine lifecycle. IaaS still supplies compute, networks, images, storage, and related capabilities.

## 2. Reconciler card sort

Sort these events: schedule a Pod, replace a failed Pod, create an IaaS server for a Machine, bootstrap a control plane, join a worker, install the CNI, change worker replicas, select a machine image, and verify a Node provider ID.

**Pass conditions:** Kubernetes, CAPI, bootstrap provider, control-plane provider, infrastructure provider, and validation evidence remain distinct.

## 3. Role and path challenge

Given seed, management, edge, and two workload clusters, identify lifecycle authority, service-traffic role, workload spokes, private child API path, East-West path, and North-South path.

**Pass conditions:** The management cluster is not assumed to carry application traffic. Loss of management may leave existing workloads running but blocks the declared replacement, scaling, upgrade, and recovery path.

## 4. Three load balancers

For a private Kubernetes API endpoint, a `Service` of type `LoadBalancer`, and an edge cluster, name owner, traffic, integration, and proof.

**Pass conditions:** API health does not prove application load-balancer integration or edge-to-workload delivery. The answer does not invent DNS, certificates, ingress, or public routes.

## 5. Manifest clinic

Annotate a supplied ClusterClass, Cluster, AppProject, Application, or ApplicationSet by `apiVersion`, `kind`, namespace, references, topology, versions, replicas, variables, source revision, destination, and ownership.

**Pass conditions:** YAML parsing, versioned schema validation, server-side dry-run, live reconciliation, and workload evidence remain separate. Unknown provider or version syntax stays unverified.

## 6. Scale and upgrade tabletop

Order scale-out evidence, scale-in evidence, and a two-phase upgrade using one Kubernetes-version and machine-image pair.

**Pass conditions:** The owning declaration changes. Stable Machine, infrastructure, IaaS server, provider-ID, and Node relationships are checked. Preparation is non-mutating. Apply requires explicit approval and bounded rollout plus workload checks.

## 7. GitOps ownership challenge

Review an Argo CD project, lifecycle application, and workload ApplicationSet.

**Pass conditions:** Exact repository, revision, path, destination, selector, credential boundary, and live target are explicit. `Synced` does not prove the workload is available or reachable. One declaration has one active owner.

## 8. Cleanup ordering

Order Git intent removal, stopping Argo CD restoration, child registration removal, stable-ID capture, CAPI Cluster deletion, bounded absence checks, retained shared inputs, and any later foundation destroy review.

**Pass conditions:** Higher-level reconciliation stops first, registrations are removed while APIs respond, deletion goes through the owner, and absence uses captured IDs.

## Feedback format

```yaml
assessment:
  architecture: pass | needs_revision | not_assessed
  content: pass | needs_revision | not_assessed
  syntax: pass | needs_revision | unverified
  evidence: pass | needs_revision | unverified
  unsupported_claims: []
  broken_ownership_or_identity_links: []
  repair_order: []
  next_exercise:
```
