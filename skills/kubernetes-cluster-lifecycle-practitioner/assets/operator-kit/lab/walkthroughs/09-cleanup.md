# 9. Cleanup

Video companion: [C4-P9](https://git.vanillacore.net/giga/content/src/commit/b56cad92b74b4335de99879415d437b97ab677cd/chapter-4/VIDEO_SCOPES.md#c4-p9-cleanup-stop-reconciliation-and-delete-through-the-owner)

## Purpose

Cleanup must stop Argo CD from restoring desired CAPI declarations, remove child credentials while their APIs still respond, and then let CAPI delete the infrastructure it owns. The Management cluster and its OpenTofu state remain until every child has gone.

## 1. Confirm every target in a fresh shell

```bash
# We declare every cloud, repository and Kubernetes target before cleanup begins.
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

test -r "$OS_CLIENT_CONFIG_FILE"
test -d "$CONFIG_REPO/.git"
./scripts/require-context.sh "$KUBECONFIG" "$MANAGEMENT_CONTEXT"
./scripts/require-context.sh "$SERVICE_A_KUBECONFIG" "$SERVICE_A_CONTEXT"
./scripts/require-context.sh "$LOADBALANCER_KUBECONFIG" "$LOADBALANCER_CONTEXT"
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
kubernetes-admin@kubernetes
https://<management-api>:6443
context checks completed without error
```

## 2. Remove the desired declarations and stop Argo CD

We remove the two child declarations from the configuration repository through its normal review process. This is a Git change, not an imperative cluster deletion. Because the lifecycle Application uses `prune: false`, the live CAPI objects remain until we delete them explicitly.

```bash
# We prepare and inspect the Git removal without committing on the reader's behalf.
git -C "$CONFIG_REPO" rm --ignore-unmatch \
  clusters/service-a*.yaml clusters/loadbalancer*.yaml
git -C "$CONFIG_REPO" diff --check
git -C "$CONFIG_REPO" diff -- clusters
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
rm 'clusters/service-a.yaml'
rm 'clusters/loadbalancer.yaml'
diff --check: no whitespace errors
```

We stop here until that removal has passed the repository's approval process and the approved revision no longer contains either declaration. We then remove the workload and lifecycle reconciliation objects from the Management cluster. `--cascade=orphan` leaves the CAPI Cluster objects for the explicit owner-driven deletion below.

```bash
# We confirm the approved Git revision before stopping reconciliation.
APPROVED_REMOVAL_REVISION="REPLACE_WITH_APPROVED_COMMIT_OR_TAG"
git -C "$CONFIG_REPO" cat-file -e "$APPROVED_REMOVAL_REVISION^{commit}"
! git -C "$CONFIG_REPO" cat-file -e "$APPROVED_REMOVAL_REVISION:clusters/service-a.yaml"
! git -C "$CONFIG_REPO" cat-file -e "$APPROVED_REMOVAL_REVISION:clusters/loadbalancer.yaml"
! git -C "$CONFIG_REPO" ls-tree -r --name-only "$APPROVED_REMOVAL_REVISION" -- clusters | grep -E 'clusters/(service-a|loadbalancer).*[.]yaml$'

kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  -n argocd delete applicationset/registered-workload-clusters \
  --cascade=orphan --ignore-not-found
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  -n argocd delete application/service-a-workload-demo \
  --cascade=orphan --ignore-not-found
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  -n argocd delete application/child-cluster-lifecycle \
  --cascade=orphan --ignore-not-found

! kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  -n argocd get application/child-cluster-lifecycle
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
applicationset.argoproj.io "registered-workload-clusters" deleted
application.argoproj.io "service-a-workload-demo" deleted
application.argoproj.io "child-cluster-lifecycle" deleted
Error from server (NotFound): applications.argoproj.io "child-cluster-lifecycle" not found
```

## 3. Remove child registrations while the APIs respond

The unregister helper removes child RBAC and token material first. It then removes the Management-cluster registration Secret. Every deletion is idempotent, so a repaired run can safely continue after a partial failure.

```bash
# We remove both confirmed registrations before deleting either child API.
CONFIRM_ARGOCD_UNREGISTER=service-a ./scripts/unregister-argocd-cluster.sh \
  "$KUBECONFIG" "$MANAGEMENT_CONTEXT" \
  "$SERVICE_A_KUBECONFIG" "$SERVICE_A_CONTEXT" \
  service-a workload-demo

CONFIRM_ARGOCD_UNREGISTER=loadbalancer ./scripts/unregister-argocd-cluster.sh \
  "$KUBECONFIG" "$MANAGEMENT_CONTEXT" \
  "$LOADBALANCER_KUBECONFIG" "$LOADBALANCER_CONTEXT" \
  loadbalancer workload-demo
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
cluster service-a unregistered and child RBAC removed
cluster loadbalancer unregistered and child RBAC removed
```

## 4. Capture IDs and delete through CAPI

We capture stable compute, port, volume and API-load-balancer IDs before deletion. Each local evidence file is ignored by Git. An empty evidence set cannot pass the cleanup helper.

```bash
# We capture both ownership sets before any CAPI deletion begins.
mkdir -p evidence
CONFIRM_MANAGEMENT_CONTEXT="$MANAGEMENT_CONTEXT" python3 scripts/capture-openstack-ids.py \
  "$KUBECONFIG" "$MANAGEMENT_CONTEXT" \
  service-a service-a "$OS_CLOUD" \
  evidence/service-a-resource-ids.json
CONFIRM_MANAGEMENT_CONTEXT="$MANAGEMENT_CONTEXT" python3 scripts/capture-openstack-ids.py \
  "$KUBECONFIG" "$MANAGEMENT_CONTEXT" \
  loadbalancer loadbalancer "$OS_CLOUD" \
  evidence/loadbalancer-resource-ids.json

# We delete each owning Cluster, wait for NotFound and query every captured IaaS ID.
CONFIRM_MANAGEMENT_CONTEXT="$MANAGEMENT_CONTEXT" CONFIRM_DELETE_CLUSTER=service-a/service-a \
  ./scripts/cleanup.sh \
  "$KUBECONFIG" "$MANAGEMENT_CONTEXT" \
  service-a service-a \
  evidence/service-a-resource-ids.json "$OS_CLOUD"

CONFIRM_MANAGEMENT_CONTEXT="$MANAGEMENT_CONTEXT" CONFIRM_DELETE_CLUSTER=loadbalancer/loadbalancer \
  ./scripts/cleanup.sh \
  "$KUBECONFIG" "$MANAGEMENT_CONTEXT" \
  loadbalancer loadbalancer \
  evidence/loadbalancer-resource-ids.json "$OS_CLOUD"

# The ClusterResourceSet and payload ConfigMap live in the Management cluster;
# remove them only after their target child Cluster is absent.
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  delete -f rendered/addons/service-a-cert-manager.yaml --ignore-not-found
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  delete -f rendered/addons/service-a-contour.yaml --ignore-not-found
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  delete -f rendered/addons/service-a-storage.yaml --ignore-not-found
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  delete -f rendered/addons/loadbalancer-cert-manager.yaml --ignore-not-found
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  delete -f rendered/addons/loadbalancer-contour.yaml --ignore-not-found
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  delete -f rendered/addons/loadbalancer-storage.yaml --ignore-not-found
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
cluster service-a/service-a is absent from the management API
all captured OpenStack resource IDs are absent
clusterresourceset.cluster.x-k8s.io "service-a-cert-manager" deleted
```

Shared networks, security groups, key pairs and credential inputs remain because the child Cluster objects do not own them. We retain the Management cluster until both deletions and absence checks have succeeded. A later approved shutdown reviews a separate OpenTofu destruction plan for that seed foundation.

## Evidence gate

Both child registrations, all six child add-on resource sets and the three Argo CD reconciliation objects are absent. The `service-a` and `loadbalancer` Cluster objects are NotFound, every captured CAPI-owned OpenStack ID is absent, and shared inputs remain.
