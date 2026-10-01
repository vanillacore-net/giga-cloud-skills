# 03: Deploy the LoadBalancer cluster

Management can now create its first child. The LoadBalancer is a Kubernetes cluster with foundations and a separate Envoy routing service. It is not an existing endpoint that we assume someone supplied.

## Prepare its inputs

Read the LoadBalancer input produced by the offline example. For a live configuration, use the selected image/flavors, existing private network, reserved API/service addresses and the scoped CAPO identity references. The machine image must be built for the requested Kubernetes version; the upstream `70-build-capo-image.yml` is the separate image-build procedure, not a fabricated image ID in our session.

The initial gateway forwards incoming service traffic toward the LoadBalancer service address. The LoadBalancer selects a destination; it does not replace either workload Spoke's local ingress.

## Credential boundary at this revision

```bash
"$PYTHON" "$LAB/scripts/platform.py" bootstrap --case "$CASE" --target loadbalancer
```

At the pinned source, this returns `CREDENTIAL_BOOTSTRAP_BLOCKED` and exit 2 before starting a process. Scoped identity/Secret installation exists inside the direct 80/90 rollout, not as the credential-only primitive needed by this declaration-first path. Do not publish a new live child and then run that old rollout to make the Secret appear. A reviewed source and kit revision must provide the missing boundary before live creation can be demonstrated.

This stop does not prevent local configuration/render learning:

```bash
"$PYTHON" "$LAB/scripts/platform.py" render --case "$CASE" --target loadbalancer
```

We obtain `cluster.yaml`, `foundations.yaml` and `bridge-access.yaml` under the rendered LoadBalancer directory. Inspect the actual directory listing, since upstream file names are authoritative. The files describe CAPI infrastructure and topology, the GovStackSpoke lifecycle resource, foundation Applications and bridge access. Rendering does not create a VM or Kubernetes resource.

## Delivery after the implementation dependency is repaired

Use the reviewed deployment repository, not this learning repository. Copy only reviewed non-secret declarations to its `gitops/spokes/loadbalancer/` path, inspect the diff, obtain approval, then use that repository's branch/PR workflow. Management's ApplicationSet discovers the directory. Argo CD delivers the initial CAPI declarations; CAPI/CAPO creates machines. The bridge registers the child and Argo CD delivers its foundations.

Watch GovStackSpoke conditions, actual Machines and child Nodes rather than stopping at an accepted Git commit. Record the child Cluster UID and observed generation. Check private API access and the LoadBalancer routing service's actual address. At this point the workload routes are intentionally absent; the two Spokes are created next.
