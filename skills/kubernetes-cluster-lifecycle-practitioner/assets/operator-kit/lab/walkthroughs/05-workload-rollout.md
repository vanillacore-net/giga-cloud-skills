# 5. Workload-cluster rollout

Video companion: [C4-P5](https://git.vanillacore.net/giga/content/src/commit/b56cad92b74b4335de99879415d437b97ab677cd/chapter-4/VIDEO_SCOPES.md#c4-p5-workload-cluster-rollout-follow-reconciliation-to-ready-nodes)

## Purpose

One small `Cluster` request now activates the object relationships explained earlier. The management controllers create the OpenStack resources, kubeadm initializes and joins Nodes, the CNI completes the child network, and ClusterResourceSets add the certificate, private-ingress and disposable-storage baselines.

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
test -r "$OS_CLIENT_CONFIG_FILE"
./scripts/require-context.sh "$KUBECONFIG" "$MANAGEMENT_CONTEXT"

# Compare the requested object with the live management API before applying it.
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  diff -f manifests/base/clusterclass.yaml || test "$?" -eq 1
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  diff -f rendered/addons/service-a-cert-manager.yaml || test "$?" -eq 1
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  diff -f rendered/addons/service-a-contour.yaml || test "$?" -eq 1
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  diff -f rendered/addons/service-a-storage.yaml || test "$?" -eq 1
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  diff -f rendered/service-a.yaml || test "$?" -eq 1

# Apply the reusable class, the matching add-on declaration and the Cluster.
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  apply -f manifests/base/clusterclass.yaml
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  apply -f rendered/addons/service-a-cert-manager.yaml
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  apply -f rendered/addons/service-a-contour.yaml
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  apply -f rendered/addons/service-a-storage.yaml
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  apply -f rendered/service-a.yaml

# Read the ownership and condition tree while controllers reconcile the request.
clusterctl --kubeconfig "$KUBECONFIG" describe cluster service-a --namespace service-a --show-conditions all
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  get cluster,machine,machinedeployment,kubeadmcontrolplane -n service-a -o wide

# Wait for CAPI availability, then save diagnostics on any timeout.
./scripts/wait-for-cluster.sh   "$KUBECONFIG" "$MANAGEMENT_CONTEXT"   service-a service-a 30m
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
Cluster service-a/service-a reached Available; OpenStack state and child Node readiness were not checked.
```

We retrieve the generated child credential only after the control plane exists:

```bash
# Store the child kubeconfig with restrictive permissions and never print it.
umask 077
clusterctl --kubeconfig "$KUBECONFIG" get kubeconfig service-a --namespace service-a > service-a.kubeconfig

# Install the same pinned Calico implementation with service-a's own Pod CIDR.
# The helper verifies the operator checksum, waits for its CRD, applies the
# Installation resource and waits for Nodes. Its source is part of this lab.
./scripts/install-cni.sh   "$SERVICE_A_KUBECONFIG" 10.241.0.0/16

# A CAPI Available condition is necessary but not sufficient. Prove child API,
# Node and system-Pod health, then match CAPI Machine, Nova server and Node IDs.
./scripts/require-context.sh "$SERVICE_A_KUBECONFIG" "$SERVICE_A_CONTEXT"
kubectl --kubeconfig "$SERVICE_A_KUBECONFIG" --context "$SERVICE_A_CONTEXT" cluster-info
kubectl --kubeconfig "$SERVICE_A_KUBECONFIG" --context "$SERVICE_A_CONTEXT" get nodes -o wide
kubectl --kubeconfig "$SERVICE_A_KUBECONFIG" --context "$SERVICE_A_CONTEXT" -n kube-system get pods -o wide
./scripts/verify-resource-chain.sh   "$KUBECONFIG" "$MANAGEMENT_CONTEXT"   service-a service-a "$SERVICE_A_KUBECONFIG" "$OS_CLOUD"
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
NAME                         STATUS   ROLES           VERSION
service-a-control-plane-<id>   Ready    control-plane   <pinned-version>
service-a-md-0-<id>            Ready    <none>          <pinned-version>
verified Machine -> OpenStack server -> Ready Node: <openstack-server-uuid>
```

After the child API and CNI respond, CAPI can apply all matching resource sets. We inspect both sides, wait for cert-manager, Contour and Envoy, and then test the storage path:

```bash
# Confirm the management-side binding and the child-side provisioner.
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  -n service-a get clusterresourceset,clusterresourcesetbinding
kubectl --kubeconfig "$SERVICE_A_KUBECONFIG" --context "$SERVICE_A_CONTEXT" \
  -n cert-manager rollout status deployment/cert-manager --timeout=5m
kubectl --kubeconfig "$SERVICE_A_KUBECONFIG" --context "$SERVICE_A_CONTEXT" \
  -n cert-manager rollout status deployment/cert-manager-webhook --timeout=5m
kubectl --kubeconfig "$SERVICE_A_KUBECONFIG" --context "$SERVICE_A_CONTEXT" \
  -n projectcontour rollout status deployment/contour --timeout=5m
kubectl --kubeconfig "$SERVICE_A_KUBECONFIG" --context "$SERVICE_A_CONTEXT" \
  -n projectcontour rollout status daemonset/envoy --timeout=5m
kubectl --kubeconfig "$SERVICE_A_KUBECONFIG" --context "$SERVICE_A_CONTEXT" \
  -n local-path-storage rollout status deployment/local-path-provisioner --timeout=5m
kubectl --kubeconfig "$SERVICE_A_KUBECONFIG" --context "$SERVICE_A_CONTEXT" \
  get storageclass local-path

# The probe uses only declarative Kubernetes resources; no storage shell helper is needed.
kubectl --kubeconfig "$SERVICE_A_KUBECONFIG" --context "$SERVICE_A_CONTEXT" \
  apply -f manifests/probe/storage-smoke.yaml
kubectl --kubeconfig "$SERVICE_A_KUBECONFIG" --context "$SERVICE_A_CONTEXT" \
  -n storage-smoke wait --for=jsonpath='{.status.phase}'=Bound \
  pvc/local-path-smoke --timeout=3m
kubectl --kubeconfig "$SERVICE_A_KUBECONFIG" --context "$SERVICE_A_CONTEXT" \
  -n storage-smoke wait --for=jsonpath='{.status.phase}'=Succeeded \
  pod/local-path-smoke --timeout=3m
kubectl --kubeconfig "$SERVICE_A_KUBECONFIG" --context "$SERVICE_A_CONTEXT" \
  -n storage-smoke logs pod/local-path-smoke
```

The final line must be:



Representative success output (shortened; values in angle brackets are environment-specific):

```text
chapter-4-storage-ready
```

This proves dynamic local provisioning and one write/read cycle. Because the volume directory belongs to the selected Node, it does not prove replication, failover, backup or OpenStack block-volume integration.

## Evidence gate

We continue only when the child API responds, every expected Node is Ready, DNS and CNI are healthy, every Machine maps through an OpenStack server ID to a Node provider ID, cert-manager and Contour/Envoy are ready, and the storage probe completes with `chapter-4-storage-ready`.
