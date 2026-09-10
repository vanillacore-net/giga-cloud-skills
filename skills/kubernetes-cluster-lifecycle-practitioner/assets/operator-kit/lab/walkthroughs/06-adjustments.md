# 6. Adjustments: sizing, scaling and upgrades

Video companion: [C4-P6](https://git.vanillacore.net/giga/content/src/commit/b56cad92b74b4335de99879415d437b97ab677cd/chapter-4/VIDEO_SCOPES.md#c4-p6-adjustments-scale-workers-and-plan-upgrades)

## Purpose

The declaration must continue to own the cluster after creation. Scaling an individual IaaS instance would bypass that ownership. We change the worker count in the Cluster topology, prove the resulting identity chain and then scale back.

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

# The helper prepares a temporary contract change, renders it, performs
# server-side validation, shows kubectl diff and then requires CONFIRM_APPLY.
CONFIRM_MANAGEMENT_CONTEXT="$MANAGEMENT_CONTEXT" CONFIRM_APPLY="$MANAGEMENT_CONTEXT" \
  ./scripts/scale-workers.sh \
  environment-contract.yaml 2 \
  "$KUBECONFIG" "$MANAGEMENT_CONTEXT" \
  "$SERVICE_A_KUBECONFIG" "$OS_CLOUD"
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
scale-out server present: <openstack-server-uuid>
verified Machine -> OpenStack server -> Ready Node: <openstack-server-uuid>
```

The helper waits for the expected OpenStackMachine count and verifies every CAPI Machine to OpenStack instance to Kubernetes Node identity chain. It also proves that any added instance exists in the selected OpenStack project.

Control-plane and worker flavors stay separate because their bottlenecks differ. API server and etcd need predictable latency and availability. Workers follow application CPU, memory, accelerator and local-disk needs. The example sizes are learning inputs, not production recommendations.

We scale back through the same declaration and prove the intended deletion:

```bash
# The helper records the pre-change instance IDs. After scaling to one worker,
# it proves that the removed instance is absent and the retained chain is Ready.
CONFIRM_MANAGEMENT_CONTEXT="$MANAGEMENT_CONTEXT" CONFIRM_APPLY="$MANAGEMENT_CONTEXT" \
  ./scripts/scale-workers.sh \
  environment-contract.yaml 1 \
  "$KUBECONFIG" "$MANAGEMENT_CONTEXT" \
  "$SERVICE_A_KUBECONFIG" "$OS_CLOUD"
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
scale-in server absent: <removed-openstack-server-uuid>
verified Machine -> OpenStack server -> Ready Node: <retained-openstack-server-uuid>
```

A Kubernetes upgrade changes both the Kubernetes version and the machine image used for replacement machines. Before preparing the change, review the Kubernetes target, kubeadm API compatibility, CAPI and CAPO support matrix, CNI compatibility, machine-image provenance, rollout order, rollback assumptions and workload availability test together. The target image must already contain the selected Kubernetes packages and remain available in the approved Glance project.

The helper below creates a temporary copy of the environment contract and adds `kubernetes_version` and `image_id` only to `service-a`. This keeps the default version and image for other clusters unchanged. It rejects a namespace that differs from the selected contract entry, binds the child kubeconfig to the CAPI Cluster through the Machine, OpenStack server and Ready Node identity chain, and requires every current Machine and matching kubelet to have reached the current topology version. This prevents a second upgrade from starting while the first rollout is incomplete. Its first run then performs the OpenStack image read-back, renders both cluster declarations, asks the installed API to validate them and displays the actual `service-a` diff. `PREPARE_ONLY=yes` makes that review phase return without changing the contract or Cluster object.

```bash
# Start from a fresh shell and name an independently reviewed version, image
# and workload that must remain available throughout the replacement rollout.
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
TARGET_KUBERNETES_VERSION="REPLACE_WITH_REVIEWED_TARGET_VERSION"
TARGET_IMAGE_ID="REPLACE_WITH_PREPARED_GLANCE_IMAGE_UUID"
test -r "$OS_CLIENT_CONFIG_FILE"
./scripts/require-context.sh "$KUBECONFIG" "$MANAGEMENT_CONTEXT"

CONFIRM_MANAGEMENT_CONTEXT="$MANAGEMENT_CONTEXT" PREPARE_ONLY=yes \
  ./scripts/upgrade-cluster.sh \
  environment-contract.yaml service-a service-a \
  "$TARGET_KUBERNETES_VERSION" "$TARGET_IMAGE_ID" \
  "$KUBECONFIG" "$MANAGEMENT_CONTEXT" \
  "$SERVICE_A_KUBECONFIG" "$OS_CLOUD" \
  kube-system coredns

```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
deployment/coredns condition met
server-side manifest schema validation passed using a namespace-neutral temporary copy
prepare-only complete; no Cluster object or contract was changed
```

The rendered proposal is `evidence/upgrade/service-a.yaml`. Review its topology version and `imageID` together with the displayed diff. Applying requires a second run with a confirmation bound to the namespace, Cluster, version and image. At this pre-GitOps stage, CoreDNS is the availability gate because it already runs in every child cluster; a production change should also pass an application-level service check. The helper verifies the named Deployment, persists the two per-cluster values in `environment-contract.yaml`, and applies the rendered Cluster. It then waits for the control-plane and worker rollout conditions, verifies that every resulting Machine has the target version and every OpenStackMachine uses the target image, checks the Machine to server to Ready Node identity chain, and repeats the Deployment check.

```bash
# Bind approval to the exact change that was reviewed, then rerun the same
# validation and diff before the helper can apply it.
CONFIRM_MANAGEMENT_CONTEXT="$MANAGEMENT_CONTEXT" \
CONFIRM_UPGRADE="service-a/service-a:${TARGET_KUBERNETES_VERSION}:${TARGET_IMAGE_ID}" \
  ./scripts/upgrade-cluster.sh \
  environment-contract.yaml service-a service-a \
  "$TARGET_KUBERNETES_VERSION" "$TARGET_IMAGE_ID" \
  "$KUBECONFIG" "$MANAGEMENT_CONTEXT" \
  "$SERVICE_A_KUBECONFIG" "$OS_CLOUD" \
  kube-system coredns
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
upgrade verified: service-a/service-a version=<reviewed-version> image=<image-uuid> workload=kube-system/coredns
```

This walkthrough occurs before Argo CD is installed. Once the GitOps lifecycle Application owns Cluster declarations, submit the rendered change to its reviewed repository path and let Argo CD apply it instead of running a direct apply in parallel.

## Evidence gate

The requested and observed worker counts match, retained Nodes remain healthy, and the deleted Machine's OpenStack identifier is absent. A successful patch command alone is not scaling evidence. The upgrade path is now copyable and guarded, but its OpenStack rollout remains explicitly `not-tested` until an approved target version and image have passed the complete helper against the reference environment.
