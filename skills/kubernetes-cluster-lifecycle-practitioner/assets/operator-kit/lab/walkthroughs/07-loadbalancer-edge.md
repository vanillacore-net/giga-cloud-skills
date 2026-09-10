# 7. LoadBalancer and edge-cluster path

Video companion: [C4-P7](https://git.vanillacore.net/giga/content/src/commit/b56cad92b74b4335de99879415d437b97ab677cd/chapter-4/VIDEO_SCOPES.md#c4-p7-load-balancer-and-edge-cluster-prove-a-real-hub-and-spoke-path)

## Purpose

The LoadBalancer cluster is the service-traffic hub. The Management cluster remains outside that data path and controls lifecycle through private child APIs. We prove the protected management path and the edge-to-workload service path separately.

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

# We render and validate the edge-role request from the shared ClusterClass.
python3 scripts/render-manifests.py --contract environment-contract.yaml --output rendered
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  apply --server-side --dry-run=server -f rendered/loadbalancer.yaml
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  apply --server-side --dry-run=server -f rendered/addons/loadbalancer-cert-manager.yaml
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  apply --server-side --dry-run=server -f rendered/addons/loadbalancer-contour.yaml
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  apply --server-side --dry-run=server -f rendered/addons/loadbalancer-storage.yaml
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  diff -f rendered/loadbalancer.yaml || test "$?" -eq 1

# We apply and wait for the dedicated LoadBalancer cluster.
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  apply -f rendered/addons/loadbalancer-cert-manager.yaml
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  apply -f rendered/addons/loadbalancer-contour.yaml
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  apply -f rendered/addons/loadbalancer-storage.yaml
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  apply -f rendered/loadbalancer.yaml
./scripts/wait-for-cluster.sh \
  "$KUBECONFIG" "$MANAGEMENT_CONTEXT" \
  loadbalancer loadbalancer 30m

# We retrieve its protected kubeconfig and install its declared Pod network.
umask 077
clusterctl --kubeconfig "$KUBECONFIG" get kubeconfig loadbalancer --namespace loadbalancer > loadbalancer.kubeconfig
./scripts/install-cni.sh "$LOADBALANCER_KUBECONFIG" 10.240.0.0/16

# Inspect both child identities against the context names reviewed in lab-session.env.
kubectl --kubeconfig "$LOADBALANCER_KUBECONFIG" config get-contexts
kubectl --kubeconfig "$SERVICE_A_KUBECONFIG" config get-contexts
./scripts/require-context.sh "$LOADBALANCER_KUBECONFIG" "$LOADBALANCER_CONTEXT"
./scripts/require-context.sh "$SERVICE_A_KUBECONFIG" "$SERVICE_A_CONTEXT"

# Confirm that all three baselines reached this child.
kubectl --kubeconfig "$LOADBALANCER_KUBECONFIG" \
  -n cert-manager rollout status deployment/cert-manager --timeout=5m
kubectl --kubeconfig "$LOADBALANCER_KUBECONFIG" \
  -n projectcontour rollout status deployment/contour --timeout=5m
kubectl --kubeconfig "$LOADBALANCER_KUBECONFIG" \
  -n projectcontour rollout status daemonset/envoy --timeout=5m
kubectl --kubeconfig "$LOADBALANCER_KUBECONFIG" \
  -n local-path-storage rollout status deployment/local-path-provisioner --timeout=5m
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
Cluster loadbalancer/loadbalancer reached Available; OpenStack state and child Node readiness were not checked.
```

Four resources participate in load balancing and ingress:

1. CAPO can use an OpenStack load balancer for a private Kubernetes API endpoint.
2. An application can request a Kubernetes `Service` of type `LoadBalancer`.
3. The LoadBalancer cluster runs the shared edge Envoy instances.
4. Every workload cluster runs a private Contour/Envoy ingress that routes to its local Services.

This package uses CAPO's bootstrap-driven provider-ID path and does not install the OpenStack Cloud Controller Manager. It therefore keeps every Chapter 4 Envoy Service private. Chapter 5 exposes the shared edge through the reviewed OpenStack integration, but the private workload-cluster ingress remains a separate hop.

## Prove the protected management path

The next helper starts a disposable curl Pod inside the Management cluster and supplies a child client certificate through a temporary Secret. Each call authenticates to a private child `/readyz` endpoint from the actual management network, checks for `ok` and removes the probe namespace and credential.

```bash
# We run each authenticated probe from a disposable Management-cluster Pod.
CONFIRM_MANAGEMENT_PATH_TEST=yes ./scripts/verify-management-api-path.sh \
  "$KUBECONFIG" "$MANAGEMENT_CONTEXT" \
  "$SERVICE_A_KUBECONFIG" service-a
CONFIRM_MANAGEMENT_PATH_TEST=yes ./scripts/verify-management-api-path.sh \
  "$KUBECONFIG" "$MANAGEMENT_CONTEXT" \
  "$LOADBALANCER_KUBECONFIG" loadbalancer
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
ManagementPathReady: service-a /readyz returned ok from a Management-cluster Pod
ManagementPathReady: loadbalancer /readyz returned ok from a Management-cluster Pod
```

## Prove the edge-to-workload-ingress path

The renderer verifies both kubeconfig contexts and writes their actual API servers into an ignored path contract. We inspect those generated identities, add approved route, return-route, policy, DNS and MTU evidence, then set `example_only: false` and `execution_approved: true`. The verifier reads the Envoy address from the confirmed destination cluster; the contract cannot substitute an arbitrary URL.

```bash
python3 scripts/render-path-contract.py \
  --source-kubeconfig "$LOADBALANCER_KUBECONFIG" \
  --source-context "$LOADBALANCER_CONTEXT" \
  --destination-kubeconfig "$SERVICE_A_KUBECONFIG" \
  --destination-context "$SERVICE_A_CONTEXT" \
  --output hub-spoke-contract.yaml
# Review the generated identities, then add approved network evidence and approvals.

# The helper creates a destination, Service and Ingress in service-a. It first
# proves the confirmed local Envoy route and rejects external Envoy exposure.
CONFIRM_PATH_DESTINATION="service-a/${SERVICE_A_CONTEXT}" \
  ./scripts/prepare-path-probe.sh hub-spoke-contract.yaml

# The verifier checks both API identities, derives the private Envoy URL from
# service-a, checks the Ingress class, host and backend, then runs the edge client.
CONFIRM_PATH_TEST="loadbalancer/${LOADBALANCER_CONTEXT}->service-a/${SERVICE_A_CONTEXT}" \
  ./scripts/verify-hub-spoke.sh hub-spoke-contract.yaml

CONFIRM_PATH_TEST_CLEANUP="${LOADBALANCER_CONTEXT}->${SERVICE_A_CONTEXT}" \
  ./scripts/cleanup-path-probe.sh \
  "$LOADBALANCER_KUBECONFIG" "$LOADBALANCER_CONTEXT" \
  "$SERVICE_A_KUBECONFIG" "$SERVICE_A_CONTEXT"
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
Path contract written: hub-spoke-contract.yaml
source: loadbalancer | loadbalancer-admin@loadbalancer | https://<loadbalancer-api>:6443
destination: service-a | service-a-admin@service-a | https://<service-a-api>:6443
WorkloadIngressReady: service-a/service-a-admin@service-a via private Envoy <cluster-ip>, HTTP 200
PathReady: loadbalancer/loadbalancer-admin@loadbalancer -> service-a/service-a-admin@service-a via private Envoy <cluster-ip>, HTTP 200
namespace "chapter4-path-test" deleted
```

## Evidence gate

We record two `ManagementPathReady` results, `WorkloadIngressReady` for the local Envoy-to-Service route, and `PathReady` for the edge-to-workload-ingress route. When the data route is not approved or not tested, we leave its status as `not-tested`.
