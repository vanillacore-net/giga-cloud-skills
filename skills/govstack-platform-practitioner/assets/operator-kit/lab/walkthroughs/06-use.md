# 06: Use the platform

We now work as an application team in one allowed namespace. Releasing a new application response does not require rebuilding its cluster or changing CAPI resources.

## Deliver a small revision

Use the team repository and AppProject prepared in step 04. Keep the two paths distinct in that repository, for example `information-mediator/probe/` and `example-workloads/probe/`. Each Application runs in its own Spoke's Workload Argo CD and points to that child's local destination. Review the complete Application fields and repository credentials through the approved tenant setup; do not reuse the Management Argo CD identity for a team release.

Start with the probe objects prepared in step 05, excluding their platform-owned Namespace. After the application is healthy, change the `-text=` argument in the example-workloads Deployment to a new, clearly named release marker, review the diff and publish it. Observe application sync, Deployment rollout and the actual HTTPS response. Then restore the original `example-workloads` marker, because the lab's fixed marker probe and later handoff expect it. The hostname and edge route need not change for this release.

## Request storage

Select a configured StorageClass after checking its provisioner and policy. This platform includes Cinder CSI and Longhorn; do not silently use a cluster's default class and call it the requested backend.

```bash
kubectl --context "$EXAMPLES_CONTEXT" get storageclasses
kubectl --context "$EXAMPLES_CONTEXT" -n chapter5-probe get pvc,pods
```

Add a small namespaced PVC and a disposable reader/writer Pod to the team repository. Give the PVC an explicit `storageClassName`, supported access mode and approved size. The Pod mounts the claim, writes a marker, exits successfully and a second Pod reads the same marker. Keep evidence of the actual PVC/PV identities and result. A Bound claim alone does not prove the intended application can write it.

The [storage-smoke preparation script](../scripts/render_storage_smoke.py) generates this pair from an explicit class, size and digest-pinned shell-compatible image:

```bash
"$PYTHON" "$LAB/scripts/render_storage_smoke.py" \
  --storage-class "$STORAGE_CLASS" --size "$PVC_SIZE" \
  --image "$SHELL_IMAGE" --output-dir "$WORK/storage"
```

Deliver `storage-writer.yaml` through the team repository and verify its actual `Succeeded` phase and logs. Remove the writer Pod through that same Git owner before delivering `storage-reader.yaml`, so a ReadWriteOnce claim is not concurrently attached on two nodes. Verify the reader's `Succeeded` phase and retain the PVC until its separate retention decision. The script prepares manifests only. Inspect the mounted path and expected marker before delivery. Removing the Pod should preserve the data; deleting the claim follows the selected reclaim policy. This is not a backup/restore test.

## Observe what changed

The private Dashboard's Spokes (GovStackSpoke) card shows declared/observed replica counts, phase and foundations. Read the named row for the intended child. When status has not caught up with its generation, the UI shows Pending. Inspect the named condition before retrying an operation. Mock catalogue entries or fixed quota displays are not evidence for this deployment.

The same lifecycle observation is available through the CLI:

```bash
"$PYTHON" "$LAB/scripts/platform.py" status --case "$LIVE_CASE" --target examples
```

Use local monitoring for the actual workload, and the Argo application/controller logs or Service endpoints relevant to the failure. A resource summary does not replace a successful test-service request. Keep the working probe, selected storage policy and separate cluster identities available for the maintenance step.
