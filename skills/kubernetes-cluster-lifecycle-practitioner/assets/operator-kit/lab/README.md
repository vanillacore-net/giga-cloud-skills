# Chapter 4 learning environment

Commit-scoped package evidence is recorded once in [`../validation-evidence.json`](https://git.vanillacore.net/giga/content/src/commit/b56cad92b74b4335de99879415d437b97ab677cd/chapter-4/validation-evidence.json). The lab does not keep a second copy that could drift from the release record.

This package supports the chapter’s complete practical path from an empty OpenStack project contract to Cluster API-managed Kubernetes clusters. It is a production-oriented learning slice, not a production deployment. The single-node seed, small replica counts and example CIDRs keep ownership and failure evidence visible.

## Ownership layers

| Layer | Owner in this package | Main files |
|---|---|---|
| Seed network, router, reference-lab jump host, ports and VM | OpenTofu | `foundation/opentofu/bootstrap/` |
| Seed guest state and first Kubernetes API | Ansible and kubeadm | `foundation/ansible/` |
| Kubernetes-ready CAPO machine image | Kubernetes SIGs Image Builder workflow | `foundation/image-builder/` |
| Child cluster machines and OpenStack resources | CAPI and CAPO | `manifests/`, `overlays/`, `scripts/` |
| First child-cluster Pod network | Pinned Calico operator and Installation resource | `scripts/install-cni.sh` |
| Per-cluster certificate controller baseline | `clusterctl` in Management; CAPI ClusterResourceSets in child clusters | `addons/cert-manager/`, rendered `addons/*-cert-manager.yaml` |
| Per-cluster private ingress baseline | Guarded direct install in Management; CAPI ClusterResourceSets in child clusters | `addons/contour/`, rendered `addons/*-contour.yaml` |
| Disposable child-cluster storage baseline | CAPI ClusterResourceSet and pinned Local Path Provisioner | `addons/`, rendered `addons/*-storage.yaml` |
| Cluster declarations and selected workloads | Argo CD on the Management cluster | `walkthroughs/08-argocd-cluster-workload-management.md`, `gitops/` |

A tool’s successful exit code proves only that tool’s immediate operation. Every walkthrough ends with evidence from the next layer: OpenTofu output is checked against Nova and Neutron, kubeadm is checked through the Kubernetes API, CAPI conditions are checked against child Nodes and OpenStack IDs, and deletion is checked against identifiers captured before removal.

## Execution environment

The reference package requires Bash on Linux `amd64`. On Windows, run the complete repository and toolchain inside WSL 2. Native PowerShell paths and Windows binaries are not a supported mix for these helpers. macOS has not been validated for this release because the pinned `clusterctl` lock covers Linux `amd64` only.

The reference lab requires a jump host because its operator starts outside the private management network. Environments with direct private access, an approved VPN or a different administration gateway can remove that component, but must adapt the OpenTofu module, Ansible inventory and kubeconfig-copy path together.

## Start here

1. Read `VERSIONS.yaml`. It pins Kubernetes, CAPI, CAPO, ORC, Calico, cert-manager, Contour, Argo CD and downloaded-tool checksums.
2. Copy `lab-session.env.example` to the ignored `lab-session.env`, review the non-secret paths and context names once, then source it from this directory.
3. Copy `environment-contract.example.yaml` to the ignored `environment-contract.yaml`.
4. Complete the [nine walkthroughs](walkthroughs/README.md) in order. Each step links to its matching pre-production scope in [`../VIDEO_SCOPES.md`](https://git.vanillacore.net/giga/content/src/commit/b56cad92b74b4335de99879415d437b97ab677cd/chapter-4/VIDEO_SCOPES.md); that target can be replaced by the published video URL after production.
5. Run the static checks before and after changing any declaration:

```bash
# Validate the public examples, CIDR relationships, manifests and scripts.
./scripts/offline-validate.sh

# Validate the new IaaS foundation without requiring live credentials.
tofu fmt -check -recursive foundation/opentofu
TOFU_DATA_DIR=/tmp/chapter4-tofu-data \
  tofu -chdir=foundation/opentofu/bootstrap init -backend=false
TOFU_DATA_DIR=/tmp/chapter4-tofu-data \
  tofu -chdir=foundation/opentofu/bootstrap validate

# Parse the Ansible playbook and its pinned module references.
ansible-playbook \
  -i foundation/ansible/inventory.example.yaml \
  foundation/ansible/seed.yaml --syntax-check
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
offline validation passed
```

Live use additionally requires an approved OpenStack project, a protected `clouds.yaml` profile, reviewed routes and capacity, an SSH key, a writable working directory for ignored inputs, and an operator authorised to create and delete the resources.

## Example network contract

The examples use separate non-overlapping ranges:

| Role | Node CIDR | Pod CIDR | Service CIDR |
|---|---|---|---|
| Management | `10.42.0.0/24` | `10.242.0.0/16` | `10.98.0.0/16` |
| LoadBalancer edge | `10.40.0.0/24` | `10.240.0.0/16` | `10.96.0.0/16` |
| `service-a` workload | `10.41.0.0/24` | `10.241.0.0/16` | `10.97.0.0/16` |

`172.0.0.0/16` is not a private RFC 1918 range. The chosen private examples still have to be checked against real data-centre, VPN, transit and peer-cluster routes.

## Script transparency

The chapter no longer uses one-line shell wrappers as unexplained installation steps. The declarative OpenTofu, Ansible, kubeadm, ClusterClass and Calico resources are visible in this repository. The remaining scripts perform narrow rendering, guarding, waiting, evidence and cleanup tasks:

| Script | Bounded job |
|---|---|
| `preflight.py` | Validates contract structure, ownership values and CIDR non-overlap locally |
| `preflight-readonly.sh` | Inspects the selected OpenStack project and reports facts without creating resources |
| `require-context.sh` | Rejects unreadable kubeconfigs and unintended current contexts before a helper changes a cluster |
| `render-manifests.py` | Combines the environment contract and role overlay into Cluster resources plus certificate, ingress and storage ClusterResourceSets |
| `install-providers.sh` | Guards kubeconfig/context, verifies downloads and installs the exact controller matrix from `VERSIONS.yaml` |
| `install-management-ingress.sh` | Reuses the `clusterctl` cert-manager installation and adds the private Contour/Envoy baseline to Management |
| `create-cloud-secret.sh` | Creates the scoped CAPO `clouds.yaml` Secret without printing it |
| `apply.sh` | Guards target context and applies already rendered resources |
| `wait-for-cluster.sh` | Waits for CAPI availability and prints diagnostics on timeout |
| `install-cni.sh` | Verifies the Calico operator download, declares the selected Pod CIDR and waits for Nodes |
| `verify-resource-chain.sh` | Matches CAPI Machines, OpenStack servers and Kubernetes Node provider IDs |
| `set-worker-replicas.sh` | Changes the desired worker count in the local contract |
| `scale-workers.sh` | Applies a reviewed replica change and verifies both creation and deletion evidence |
| `set-cluster-upgrade.py` | Writes a reviewed Kubernetes version and image pair into one Cluster entry |
| `upgrade-cluster.sh` | Validates, diffs, gates and observes a version and image rollout without claiming live evidence |
| `prepare-path-probe.sh` | Binds a confirmed workload context and API server, rejects external Envoy exposure, and verifies the local Ingress path |
| `render-path-contract.py` | Reads the two reviewed kubeconfig contexts and writes their actual API servers into the ignored path contract |
| `verify-hub-spoke.sh` | Confirms both cluster identities, derives the workload Envoy endpoint, validates its Ingress and calls it from the LoadBalancer cluster |
| `cleanup-path-probe.sh` | Removes diagnostic resources only through both explicitly confirmed contexts |
| `capture-openstack-ids.py` | Captures stable CAPI-owned OpenStack IDs before deletion |
| `cleanup.sh` | Deletes the confirmed CAPI Cluster and verifies the previously captured IDs are absent |
| `wait-for-cluster-absence.sh` | Waits for the owning Cluster object to disappear |
| `verify-openstack-absence.sh` | Queries every captured OpenStack ID after deletion |
| `verify-management-api-path.sh` | Probes a child `/readyz` endpoint from a disposable Pod in the Management cluster |
| `install-argocd.sh` | Verifies and installs the pinned Argo CD manifest and CLI on the Management cluster |
| `prepare-gitops-repository.sh` | Copies reviewed CAPI and workload declarations into a separate configuration repository and rejects credential material |
| `render-gitops.py` | Renders the bounded AppProject, lifecycle Application and workload ApplicationSet from an explicit repository URL and revision |
| `register-argocd-cluster.sh` | Registers a child cluster with namespaced permissions and protected in-cluster credentials |
| `unregister-argocd-cluster.sh` | Removes the Chapter 4 registration credential and its child-cluster RBAC after explicit confirmation |

Read a script before running it. A script can enforce local guardrails, but it cannot approve a cloud project, route, quota decision or destructive action on the operator’s behalf.

## Values that must remain local

The repository ignores:

- `clouds.yaml`, application-credential secrets and certificate material;
- `environment-contract.yaml` and `hub-spoke-contract.yaml`;
- generated kubeconfigs;
- OpenTofu variable files, plans, state and provider working data;
- Ansible live inventory and reviewed group variables;
- rendered resources, evidence and build artifacts.

Never replace an example placeholder with a live secret in a tracked file. Image, flavor, network, subnet, server, port and load-balancer UUIDs are not authentication secrets, but they are environment-specific and belong in the ignored contract and evidence files.

## Limits

The static tests do not create cloud resources and therefore cannot prove live quota, capacity, image bootability, routing, API reachability, cleanup or Argo CD reconciliation against an operator repository. Live execution is gated by explicit contracts and confirmation values. The package validates private cert-manager and Contour/Envoy controller baselines, one workload-local Ingress route and one disposable local-path PVC workflow. It does not configure production Issuers, public edge exposure, production routing policy, highly available storage, backup or a highly available management cluster. Those subjects continue in Chapter 5 or require an environment-specific design.
