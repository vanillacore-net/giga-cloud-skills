# 02: Build Management

The first infrastructure gives us a gateway and Management seed, not the workload Spokes. The gateway provides the private administration route. The seed hosts Kubernetes and then the controllers that create and maintain child clusters.

## Follow the installation order

Inspect the actual interface and generate the stage plan:

```bash
"$PYTHON" "$LAB/scripts/platform.py" bootstrap --help
"$PYTHON" "$LAB/scripts/platform.py" bootstrap --case "$CASE" --target management
```

This prints the upstream commands without running them. The stage names in help map to initial OpenTofu infrastructure, gateway configuration, Kubernetes seed, providers, Argo CD, the bridge, Dashboard and image build. The separate read-only preflight is documented in step 01, not a helper stage. Run one stage at a time so that an unsuccessful gateway configuration cannot be hidden by starting later controllers.

The worked path uses the Bootstrap repository's integration-test profile. The source does not offer an independently validated production installation through this helper. Size and harden another deployment through its approved operating process rather than treating the example's single seed as highly available Management.

For an authorized live environment, select the exact stage name from help and review its target, environment and inventory. Only then use the separate execution gate:

```bash
"$PYTHON" "$LAB/scripts/platform.py" bootstrap --case "$LIVE_CASE" \
  --target management --stage "$REVIEWED_STAGE" --execute --confirm bootstrap:management
```

For infrastructure, `--execute` alone runs the upstream plan procedure with `bootstrap_apply=false`, regardless of the environment file's value. Inspect the actual plan and its ownership/state first. Starting the source apply requires its separate approved invocation:

```bash
"$PYTHON" "$LAB/scripts/platform.py" bootstrap --case "$LIVE_CASE" \
  --target management --stage infrastructure --execute --apply \
  --confirm bootstrap:management:apply
```

This explicitly passes `bootstrap_apply=true`; it can create cloud resources. The source regenerates and validates its plan during the apply invocation, so this is not a saved-plan-hash approval mechanism. Keep the target and inputs unchanged and inspect the source's safety assertions. The helper rejects `--apply` without execution, on another stage or with the ordinary confirmation.

The literal confirmation is not approval obtained from a file or earlier installation. It follows a human's approval of that operation. Example mode refuses execution. Non-zero exit stops the sequence; inspect the failing stage and retain its state instead of running the whole installation again.

## Read the resulting state

Privately inspect the OpenTofu plan before its apply stage and retain the protected state and outputs. Review gateway private routing and the source's generated inventories before proceeding. After the seed is configured, confirm the management API's identity and Node readiness, the installed CAPI/CAPO controllers, Argo CD and the Spoke-management components:

```bash
kubectl --context "$MANAGEMENT_CONTEXT" get nodes -o wide
kubectl --context "$MANAGEMENT_CONTEXT" get deployments -A
kubectl --context "$MANAGEMENT_CONTEXT" -n argocd get applications
```

Match the context's server to the approved endpoint. A successful command on an unrelated context is not a result for this installation. Use bounded source checks; do not substitute an arbitrary delay for readiness.

## Continue

Record the generated infrastructure/image paths in the session only after those artifacts exist and their IDs/version match the actual environment. Keep Management and its private route available. They are required before the LoadBalancer and workload Spokes can be delivered and observed.
