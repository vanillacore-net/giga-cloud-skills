# 4. Workload-cluster configuration

Video companion: [C4-P4](https://git.vanillacore.net/giga/content/src/commit/b56cad92b74b4335de99879415d437b97ab677cd/chapter-4/VIDEO_SCOPES.md#c4-p4-workload-cluster-configuration-image-clusterclass-and-variables)

## Purpose

This step prepares the versioned controllers, machine image and reusable topology that will own every later workload cluster. It connects the conceptual object relationships from the chapter to the exact discovery values.

We first inspect or build the Kubernetes-ready image described in [`../foundation/image-builder/README.md`](../foundation/image-builder/README.md). A generic cloud-init image is not sufficient merely because cloud-init runs. The image must provide the compatible container runtime, kubelet, kubeadm and host configuration expected by kubeadm bootstrap.

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

# Confirm the target before creating controllers or Secrets.
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" auth can-i create deployments --all-namespaces
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" auth can-i create secrets --namespace service-a

# Create the CAPO clouds.yaml Secret without displaying its data. Its name comes
# from the reviewed environment contract used by the rendered Cluster objects.
SECRET_NAME=$(python3 -c 'import sys,yaml; print(yaml.safe_load(open(sys.argv[1]))["openstack"]["credential_secret_name"])' environment-contract.yaml)
CONFIRM_MANAGEMENT_CONTEXT="$MANAGEMENT_CONTEXT" \
  ./scripts/create-cloud-secret.sh "$KUBECONFIG" "$MANAGEMENT_CONTEXT" service-a "$SECRET_NAME" "$OS_CLIENT_CONFIG_FILE"
CONFIRM_MANAGEMENT_CONTEXT="$MANAGEMENT_CONTEXT" \
  ./scripts/create-cloud-secret.sh "$KUBECONFIG" "$MANAGEMENT_CONTEXT" loadbalancer "$SECRET_NAME" "$OS_CLIENT_CONFIG_FILE"

# Install the pinned controller versions. The helper verifies downloaded hashes,
# enables Cluster topology, installs ORC and runs clusterctl with this explicit
# kubeconfig and context. Read the script before running it.
CONFIRM_MANAGEMENT_CONTEXT="$MANAGEMENT_CONTEXT" \
  ./scripts/install-providers.sh "$KUBECONFIG" "$MANAGEMENT_CONTEXT"
CONFIRM_MANAGEMENT_CONTEXT="$MANAGEMENT_CONTEXT" \
  ./scripts/install-management-ingress.sh "$KUBECONFIG" "$MANAGEMENT_CONTEXT"

# Prove the controllers, CRDs and API contracts exist before rendering a Cluster.
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" get deployments -A
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" get crds
clusterctl --kubeconfig "$KUBECONFIG" describe cluster --help >/dev/null
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
credential secret service-a/<secret-name> applied without printing its content
NAME                                  TYPE                    VERSION
provider/cluster-api                  CoreProvider            <pinned-version>
provider/infrastructure-openstack     InfrastructureProvider  <pinned-version>
deployment "contour" successfully rolled out
```

The two helpers use the same explicit Management target. `clusterctl` installs the pinned cert-manager manifest for CAPI webhooks. `install-management-ingress.sh` verifies that existing deployment, then installs the private Contour/Envoy baseline without installing a second cert-manager. The Management endpoint remains internal and outside application traffic.

`VERSIONS.yaml` pins CAPI, CAPO, ORC, Kubernetes, Calico, cert-manager, Contour, Local Path Provisioner and tool checksums. `manifests/base/clusterclass.yaml` contains the shared machinery, while `overlays/service-a.yaml` supplies only the values that differ for `service-a`.

Each child cluster receives three separately selected baselines. cert-manager provides the local certificate APIs, Contour and Envoy provide the private ingress endpoint, and Local Path Provisioner provides disposable storage. Each rendered add-on file contains one or more payload ConfigMaps plus a `ClusterResourceSet` in the child Cluster's Management namespace. CAPI applies the payload only to a Cluster with the matching label. The large cert-manager manifest is split into size-bounded ConfigMaps, but one resource set owns the complete payload.

```bash
# Render the role-specific Cluster requests from the reviewed contract.
python3 scripts/render-manifests.py --contract environment-contract.yaml --output rendered

# Ask the live API to validate types and admission rules without persisting them.
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  apply --server-side --dry-run=server -f manifests/base/clusterclass.yaml
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  apply --server-side --dry-run=server -f rendered/service-a.yaml
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  apply --server-side --dry-run=server -f rendered/addons/service-a-cert-manager.yaml
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  apply --server-side --dry-run=server -f rendered/addons/service-a-contour.yaml
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" \
  apply --server-side --dry-run=server -f rendered/addons/service-a-storage.yaml
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
rendered/service-a.yaml
rendered/addons/service-a-cert-manager.yaml
clusterclass.cluster.x-k8s.io/openstack-standard serverside-applied (server dry run)
cluster.cluster.x-k8s.io/service-a serverside-applied (server dry run)
```

Each `ClusterResourceSet` uses `strategy: Reconcile`, so an updated payload is applied again. Controller installation remains separate from configuration: Chapter 4 creates no certificate Issuer and no public Envoy Service.

## Evidence gate

We continue when provider, Management cert-manager and Management Contour/Envoy workloads are ready, the version matrix is recorded, the CAPI image UUID is proven, and the ClusterClass, Cluster and all three child add-on declarations pass server-side dry run.
