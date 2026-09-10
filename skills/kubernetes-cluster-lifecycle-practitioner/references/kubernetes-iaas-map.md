# Kubernetes on IaaS architecture map

Use this reference after the learner understands the Chapter 3 IaaS baseline. Generic Kubernetes and Cluster API concepts come first. CAPO and OpenStack are the reviewed Chapter 4 reference mapping.

## Reconciliation layers

| Desired state | Primary mechanism | OpenStack reference involvement | Evidence needed |
|---|---|---|---|
| Pod placement and replacement | Kubernetes scheduler and workload controllers | None directly | Pod ownership, scheduling and readiness conditions |
| Node agent and container execution | kubelet, container runtime and CNI | Instance and network supplied below | Node identity, readiness, runtime and network evidence |
| Cluster and machine lifecycle | Cluster API Cluster, control-plane and Machine resources | Infrastructure provider translates requests | Conditions, owner references and stable provider IDs |
| OpenStack resources for clusters | Infrastructure provider contract | CAPO, Nova, Neutron, Glance, Cinder or Octavia as required | CAPO object to OpenStack resource relationship |
| Reviewed declarations | Git and optional GitOps controller | Argo CD can reconcile to management or child APIs | Exact repository, revision, path, destination, selector, sync and target state |

## Cluster roles

- **Seed cluster:** temporary bootstrap home for controllers until a durable management cluster exists.
- **Management cluster:** long-lived lifecycle authority for child-cluster declarations. It is a security and availability boundary.
- **Workload cluster:** runs service workloads.
- **Edge or load-balancer cluster:** an optional role in the reviewed reference for service traffic. It is not a universal requirement.

Do not route ordinary application traffic through the management cluster merely because it controls lifecycle.

## Paths to keep separate

1. **Lifecycle control path:** management controllers reach child Kubernetes APIs and the IaaS APIs needed for reconciliation.
2. **East-West service path:** workload clusters or services communicate across the private service network.
3. **North-South service path:** users or external systems reach the service through approved entry controls.

Each path requires its own routing, policy, identity, availability, and functional evidence.

## Three load-balancing meanings

- A highly available Kubernetes API endpoint for a child cluster.
- A Kubernetes `Service` of type `LoadBalancer` integrated with an IaaS load-balancing capability.
- A complete optional edge-cluster role through which service traffic is routed.

Evidence for one does not prove another.

## Ownership rule

Change an object through the declaration and controller that owns it. Scale or upgrade a CAPI-managed cluster through its Cluster topology or other owning declaration, not by resizing or deleting controller-owned IaaS servers directly. If Argo CD owns that declaration, use a reviewed Git change rather than a concurrent direct writer.

## Boundary

A ready cluster does not by itself prove a complete shared platform, service reachability, backup, recovery, observability, access policy, or production operation. The [reviewed Chapter 4 revision](https://git.vanillacore.net/giga/content/src/commit/b56cad92b74b4335de99879415d437b97ab677cd/chapter-4/chapter-4.md) demonstrates bounded cluster lifecycle and Argo CD reconciliation. Its broader Chapter 5 GitOps boundary remains qualified because the reviewed scope record and executable material differ.
