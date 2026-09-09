# IaaS capability and OpenStack reference map

Use this reference after the learner can state the generic capability. Product names describe the reviewed OpenStack reference, not IaaS as a universal architecture.

## Request chain

| Generic capability | OpenStack reference | State or relationship to inspect | What it does not prove |
|---|---|---|---|
| Authentication and service discovery | Keystone token and service catalogue | Token project scope, user or application identity, roles, region, service endpoints | Permission for every operation, endpoint reachability, or service capacity |
| Administrative resource boundary | Keystone project | Project ID, role assignment, scoped token | Physical isolation or a dedicated operating team |
| Approved boot source | Glance image | Immutable image ID, status, visibility, provenance and approval | Guest readiness for the intended workload |
| Compute request and scheduling | Nova and Placement | Server ID, flavor inputs, compute availability-zone input, status | Network reachability, attached storage, application readiness, or recovery |
| Network policy and addressing | Neutron | Network, subnet, router, port, security-group and floating-IP IDs and relationships | DNS, TLS, application response, or public-service usability |
| Persistent block storage | Cinder | Volume ID, type, storage availability-zone input, attachment server ID, status | Filesystem, data integrity, backup, or restore success |
| Allocation limits | Nova, Neutron and Cinder quota and usage | Service-specific limits and current use | Physical capacity or successful scheduling |
| Human dashboard | Horizon | The action and resulting resource state through service APIs | A separate orchestration layer or broader validation than the shown action |
| Command interface | OpenStackClient | Versioned command, selected cloud profile, structured API result | Correct local values or authority to mutate |
| Declarative client | OpenTofu with OpenStack provider | Configuration, provider schema, plan, state and read-back | Live service acceptance from formatting or validation alone |

## Cross-service acceptance

For the bounded Chapter 3 request, stable identifiers must establish the relationships that the conclusion uses:

1. the server record identifies the expected project and boot source;
2. exactly one selected VM port belongs to the server when the exercise assumes one port;
3. the expected security-group ID is applied to that port;
4. the floating-IP record points to that port;
5. the volume attachment names the same server ID;
6. compute and block-storage placement inputs were discovered from their owning services;
7. all asynchronous resources reached an accepted state within a stated time bound.

A display name is navigation help, not identity evidence. A substring match is not an exact relationship check.

## Boundary to Chapter 4

The handoff may provide project scope, approved image and machine inputs, networks, exposure policy, quota evidence, separate placement inputs, stable IDs, and IaaS validation status. It does not prove kubeadm readiness, Kubernetes API reachability, CNI behaviour, cluster reconciliation, or workload health.

## Sources

The reviewed basis is [Chapter 3](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/chapter-3.md) and its [lab](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/lab/README.md). For live syntax, also consult the installed OpenStackClient help and the exact OpenTofu provider schema.
