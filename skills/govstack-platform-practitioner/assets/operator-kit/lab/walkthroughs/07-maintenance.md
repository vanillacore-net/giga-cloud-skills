# 07: Scale, replace and upgrade

We change `example-workloads` while leaving `information-mediator` alone. The existing GovStackSpoke declaration owns supported lifecycle fields; its bridge and CAPI/CAPO carry out the machine changes.

## Scale one worker pool

Inspect the current declaration and generate a proposal:

```bash
"$PYTHON" "$LAB/scripts/platform.py" scale --case "$CASE" --target examples --workers 2
```

The offline example starts with one worker, so this proposal adds one. For a live target, derive the requested total from its actual workload/capacity and check quota/headroom. After approval, the named local write is separate:

```bash
"$PYTHON" "$LAB/scripts/platform.py" scale --case "$CASE" --target examples \
  --workers "$APPROVED_TOTAL" --write --confirm scale:example-workloads
```

This changes local candidate manifests, not the cloud and not Git remotely. Review both the GovStackSpoke and initial Cluster lifecycle values in `cluster.yaml`; the upstream tool preserves their consistency. Publish through the approved deployment repository workflow. Then observe current generation, conditions, Machines/Nodes and the still-working request path. Retain the unchanged mediator's identity as well.

Scale down by the same process, after checking eviction/disruption and storage-placement effects. Do not delete a random VM or Node as a substitute for changing the owner. Control-plane counts follow the helper's supported odd-quorum step rules rather than an arbitrary total.

## Replace machines

```bash
"$PYTHON" "$LAB/scripts/platform.py" replace --case "$CASE" --target examples --pool workers
```

The proposal changes the rollout trigger. It is not an in-place VM update. For a local approved candidate add `--write --confirm replace:example-workloads`; publish its diff and retain before/after machine IDs. Check Node readiness, workload continuity and storage placement through the bounded source procedures. A generated trigger or accepted commit is not replacement completion.

## Upgrade the Kubernetes version

Choose a supported target and its actually built matching image metadata. Review compatibility and rollback/retention before writing the new template revision:

```bash
"$PYTHON" "$LAB/scripts/platform.py" upgrade --case "$LIVE_CASE" --target examples \
  --kubernetes-version "$APPROVED_KUBERNETES_VERSION" --image "$NEXT_IMAGE_METADATA"
```

The helper rejects mismatched version/image metadata. Approval of the prepared diff is followed by the separate `--write --confirm upgrade:example-workloads` gate. Publish the reviewed templates/declaration, then check actual control-plane and worker versions, Nodes and the test route. Do not treat the offline synthetic image metadata as a usable upgrade image.

## Record the outcome

Retain the declaration revision, actual resource IDs and observed post-change state in the protected work directory. A timeout is a reason to inspect the named condition and current desired/observed values, not a reason to start the same mutation again. Source/credential deployment blockers remain explicit; this package currently exercises preparation and local tooling, not a proven live rollout.
