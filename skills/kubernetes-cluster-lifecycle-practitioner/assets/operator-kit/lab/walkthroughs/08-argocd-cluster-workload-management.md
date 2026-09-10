# 8. GitOps with Argo CD

Video companion: [C4-P8](https://git.vanillacore.net/giga/content/src/commit/b56cad92b74b4335de99879415d437b97ab677cd/chapter-4/VIDEO_SCOPES.md#c4-p8-gitops-with-argo-cd)

## Purpose

CAPI reconciles the lifecycle of child clusters. Argo CD adds a separate reconciliation loop for declarations stored in Git. In this walkthrough, we install Argo CD on the Management cluster, place reviewed CAPI declarations in a dedicated configuration repository, register two child clusters and deploy one workload only to the child labelled for workloads.

The ownership boundary remains explicit:

| Owner | Declared objects |
|---|---|
| OpenTofu | Seed IaaS foundation |
| Ansible and kubeadm | Seed host state and first Kubernetes API |
| CAPI and CAPO | Child control-plane and worker infrastructure |
| Bootstrap add-on path | CNI required before Nodes become fully usable |
| Argo CD lifecycle Application | Reviewed CAPI declarations in the Management cluster |
| Argo CD workload ApplicationSet | Reviewed namespaced workloads in selected child clusters |

Argo CD does not receive OpenStack credentials through Git. The CAPI declarations refer to the Kubernetes Secret created in Walkthrough 4, while its credential data remains in the Management cluster.

## Starting state and inputs

We begin in the repository clone after Walkthrough 7. The Management, `service-a` and `loadbalancer` clusters are healthy, and their kubeconfig files have restrictive permissions. We also need a separate Git configuration repository that Argo CD can read. The repository can be private when its access credential is configured directly in Argo CD; repository-credential setup is deployment-specific and must not be committed to this lab.

```bash
: "${GIGA_OPERATOR_KIT:=$PWD}"
cd "$GIGA_OPERATOR_KIT"
set -euo pipefail
test -r lab-session.env
. ./lab-session.env
test -r "$KUBECONFIG"
kubectl --kubeconfig "$KUBECONFIG" config get-contexts
kubectl --kubeconfig "$KUBECONFIG" config view --minify \
  -o jsonpath='{.clusters[0].cluster.server}{"\n"}'
kubectl --kubeconfig "$KUBECONFIG" config current-context

./scripts/require-context.sh "$KUBECONFIG" "$MANAGEMENT_CONTEXT"
./scripts/require-context.sh "$SERVICE_A_KUBECONFIG" "$SERVICE_A_CONTEXT"
./scripts/require-context.sh "$LOADBALANCER_KUBECONFIG" "$LOADBALANCER_CONTEXT"

# These values identify the operator-controlled configuration repository.
test -d "$CONFIG_REPO/.git"
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
kubernetes-admin@kubernetes
https://<management-api>:6443
context checks completed without error
```

We replace the example URL with the clone's real remote URL before continuing. If the repository requires authentication, we configure that credential in Argo CD through the organisation's approved secret-management path. We do not put a username, password or token into the generated Application objects.

## 1. Install the pinned Argo CD release

The helper reads the version and SHA-256 checksums from `VERSIONS.yaml`. It downloads the exact installation manifest and Linux CLI, verifies both files, installs Argo CD in the `argocd` namespace and waits for its Deployments and application-controller StatefulSet.

```bash
# We install the checksum-verified controller set and inspect its live state.
./scripts/install-argocd.sh "$KUBECONFIG" "$MANAGEMENT_CONTEXT"

kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  -n argocd get deployments,statefulsets,pods
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
deployment.apps/argocd-applicationset-controller condition met
deployment.apps/argocd-repo-server condition met
deployment.apps/argocd-server condition met
statefulset rolling update complete: 1 pod at revision <revision>
```

We continue when every Argo CD Deployment is Available, the application-controller StatefulSet is Ready and no Pod is in a terminal failure state.

## 2. Prepare the reviewed configuration repository

We render the two CAPI requests from the protected environment contract. The preparation helper copies those manifests, the shared ClusterClass and a harmless demo workload into the configuration-repository clone. It rejects Kubernetes Secret objects and common credential markers.

```bash
python3 scripts/render-manifests.py \
  --contract environment-contract.yaml \
  --output rendered
./scripts/prepare-gitops-repository.sh "$CONFIG_REPO"

# We review the exact declaration change before it becomes controller input.
git -C "$CONFIG_REPO" diff --check
git -C "$CONFIG_REPO" diff -- clusters workloads
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
clusters/service-a.yaml
clusters/loadbalancer.yaml
workloads/demo/deployment.yaml
workloads/demo/service.yaml
```

We commit and push this reviewed change through the configuration repository's normal approval process. `CONFIG_REPO_REVISION` must identify the branch, tag or commit that contains it. The Chapter 4 repository does not guess that revision or publish credentials on the reader's behalf.

## 3. Render and apply the Argo CD declarations

The renderer creates three declarations from the repository URL and revision: a bounded `AppProject`, one Application for CAPI declarations, and one ApplicationSet for selected workload clusters.

```bash
rm -rf rendered/gitops
python3 scripts/render-gitops.py \
  --repo-url "$CONFIG_REPO_URL" \
  --revision "$CONFIG_REPO_REVISION" \
  --cluster-path clusters \
  --workload-path workloads/demo \
  --output rendered/gitops

# The project must exist before a cluster registration refers to it.
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  apply -f rendered/gitops/01-project.yaml
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
rendered/gitops/01-project.yaml
rendered/gitops/02-cluster-lifecycle.yaml
rendered/gitops/03-workloads-applicationset.yaml
appproject.argoproj.io/workload-fleet configured
```

The lifecycle Application uses automated self-healing but sets `prune: false`. A Git deletion therefore cannot silently delete a child cluster. Walkthrough 9 remains the explicit deletion path.

## 4. Register the child clusters with bounded access

The registration helper creates a service account and persistent token Secret in `kube-system`, then binds that identity to a Role in the `workload-demo` namespace of each child. It stores the resulting cluster credential as a protected Secret in the Management cluster. It never writes the token to the configuration repository or terminal output.

```bash
# We register the workload and edge roles separately so selection stays explicit.
./scripts/register-argocd-cluster.sh \
  "$KUBECONFIG" "$MANAGEMENT_CONTEXT" \
  "$SERVICE_A_KUBECONFIG" "$SERVICE_A_CONTEXT" \
  service-a workload workload-demo

./scripts/register-argocd-cluster.sh \
  "$KUBECONFIG" "$MANAGEMENT_CONTEXT" \
  "$LOADBALANCER_KUBECONFIG" "$LOADBALANCER_CONTEXT" \
  loadbalancer edge workload-demo
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
registered cluster service-a with role=workload and workloads-enabled=true
registered cluster loadbalancer with role=edge and workloads-enabled=false
```

The `workload` role adds `platform.vanillacore.net/workloads-enabled=true`. The `edge` role registers the LoadBalancer cluster for later edge configuration but does not select it for the demo workload.

The lab creates a persistent service-account token because the Argo CD controller needs a stable child-cluster credential. The token object remains in `kube-system`, but its RoleBinding grants access only in `workload-demo`. A production deployment must place token rotation or an approved external identity mechanism under the organisation's credential policy. The unregister helper removes the lab token, Role and RoleBinding when the registration is no longer needed.

## 5. Reconcile and verify

We now apply the lifecycle Application and workload ApplicationSet. Argo CD reads the reviewed revision, reconciles the existing CAPI objects in the Management cluster and creates one workload Application for `service-a`.

```bash
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  apply -f rendered/gitops/02-cluster-lifecycle.yaml \
  -f rendered/gitops/03-workloads-applicationset.yaml

kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  -n argocd wait application/child-cluster-lifecycle \
  --for=jsonpath='{.status.sync.status}'=Synced --timeout=10m
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  -n argocd wait application/service-a-workload-demo \
  --for=jsonpath='{.status.sync.status}'=Synced --timeout=10m

# The selector must create the workload Application for service-a, not the edge.
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  -n argocd get applications,applicationsets -o wide
! kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  -n argocd get application/loadbalancer-workload-demo

# We verify the result in the target cluster instead of trusting Sync alone.
kubectl --kubeconfig "$SERVICE_A_KUBECONFIG" --context "$SERVICE_A_CONTEXT" \
  -n workload-demo rollout status deployment/chapter-4-demo --timeout=5m
kubectl --kubeconfig "$SERVICE_A_KUBECONFIG" --context "$SERVICE_A_CONTEXT" \
  -n workload-demo get deployment,service,pods -o wide
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
appproject.argoproj.io/workload-fleet configured
application.argoproj.io/child-cluster-lifecycle configured
NAME                                  SYNC STATUS   HEALTH STATUS
application/child-cluster-lifecycle   Synced        Healthy
application/service-a-workload-demo   Synced        Healthy
deployment "chapter-4-demo" successfully rolled out
```

If the configuration repository is private, an authentication failure at this point means that the approved repository credential is missing or wrong. We repair that credential in Argo CD, not in Git.

## Evidence gate

We continue when all of the following are visible:

- the pinned Argo CD controllers are Ready in the Management cluster;
- the lifecycle Application reports the reviewed repository revision as `Synced`;
- the ApplicationSet selects `service-a` and excludes the LoadBalancer cluster from the demo workload;
- the `service-a-workload-demo` Application is `Synced`;
- the target Deployment is Available in `service-a`; and
- no kubeconfig, service-account token or OpenStack credential appears in Git.

A Synced Application proves declared-state convergence to one Git revision. It does not prove service reachability, backup completion or recovery.

## Handoff to cleanup

Walkthrough 9 removes both registrations while the child APIs still respond, stops the Argo CD reconciliation loops and only then deletes the owning CAPI Cluster objects. We do not delete a directly reconciled Cluster while its lifecycle Application can restore the declaration.
