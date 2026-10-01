# Platform: capabilities, ownership and paths

## From tenant to runtime

The existing OpenStack tenant is an input, not an OpenStack installation project. Read its project/region, quotas, images, flavor/network/storage IDs and exposure policy from the supplied IaaS baseline. Read the compatible CAPI/CAPO versions, image contract and private ingress decisions from the cluster-lifecycle baseline. Neither artifact authorizes deployment.

1. Bootstrap the management/gateway foundation with the reviewed bootstrap automation and supplied environment, inventory, infrastructure outputs and image metadata. The gateway's public access/forwarding boundary is not a child Kubernetes API.
2. Deploy the dedicated LoadBalancer child cluster as the public application edge. Distinguish it from Kubernetes API endpoint load balancing and any IaaS-backed Service load balancer.
3. Deploy two workload spokes: `information-mediator` and `example-workloads`. Role keys in the session are `mediator` and `examples`; names, IDs, versions, ranges and machine counts come from target-specific configuration.
4. Establish management-owned foundations, private per-cluster Contour/Envoy ingress and the relevant certificate/storage baseline. Team workload Argo CD ownership does not transfer platform-foundation ownership.
5. Connect each selected public domain/TLS binding through the edge to its intended private Envoy, Service and Pods. Keep one chain and one evidence trail per spoke.

## Separate the questions

| Question | Owner/path | Evidence needed |
|---|---|---|
| Can management reconcile a child? | CAPI/CAPO and private child API control path | Exact management context, Cluster/Machine conditions, private API request, provider IDs, Nodes |
| Are declarations reconciled? | Reviewed GitOps owner and revision | Repository/revision, destination, sync/health, ownership UID/labels |
| Can a user reach the probe? | Public edge -> private per-cluster Envoy -> Service -> Pods | External request, edge backend, private ingress, Service selectors/endpoints and ready Pods for each spoke |
| Does the business service work? | Chapter 6 installation and service owner | Actual IM/examples deployment, configuration, data/credential policy and user journey; Chapter 5 cannot infer this |
| Is retirement complete? | Higher-level declarations then lifecycle owner | Reconciliation stopped, authenticated UID allowlists, stable IaaS IDs absent, identity/network/storage retention recorded |

Shared gateway, edge, management plane, DNS and certificate dependencies remain failure domains. Two workload clusters alone do not prove availability, tenancy isolation, recovery or sovereignty. Local storage smoke tests do not prove production data durability. A dashboard summary is not independent evidence of the full request path.

## Adapt and operate

Scale via the reviewed owning declaration, not by editing a provider-created VM. Replace a machine through the approved lifecycle mechanism; keep provider/Machine/Node IDs before and after. Upgrade with a reviewed Kubernetes-version/image pair, pre-change convergence, a diff, bounded rollout and route/use checks. Reject a change when the owner is ambiguous or Argo CD would overwrite it. Record recovery as a reviewed action, not an assumed instant rollback.

Chapter 5 uses only bounded disposable probes to demonstrate paths. Actual Information Mediator and example workload installation belongs to Chapter 6, carrying the same case ID and retained runtime IDs.
