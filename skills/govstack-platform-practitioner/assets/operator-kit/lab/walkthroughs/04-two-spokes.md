# 04: Deploy two workload Spokes

We create `information-mediator` and `example-workloads` as separate clusters. Chapter 6 will use them for the mediator and the applications that communicate through it. Here we install only the foundations and later small test services.

## Keep the identities separate

Review both cluster inputs together. Each needs its own scoped identity references, resource-ownership tag, API address, Pod/Service CIDRs and service-address pool. Both use the same Management plane. In this source profile they consume an existing private OpenStack network; separate cluster names do not imply automatically created private networks or complete tenant isolation.

The offline generator uses visibly synthetic IDs and one-control-plane/one-worker counts. Those are not a production recommendation. Live sizing follows the project quota, workload and availability requirements established in step 01.

## Prepare both declarations

```bash
"$PYTHON" "$LAB/scripts/platform.py" render --case "$CASE" --target mediator
"$PYTHON" "$LAB/scripts/platform.py" render --case "$CASE" --target examples
```

Inspect the generated three directories, including the already prepared LoadBalancer. Each `cluster.yaml` must contain its own named CAPI Cluster and GovStackSpoke. Each foundation Application must target the intended child, including that child's cert-manager and Contour/Envoy. Do not copy a completed first Spoke and leave its identity or destination in the second.

The credential-only blocker described in step 03 also applies to both workload children. We do not claim the rendered clusters are live. Following a repaired, reviewed deployment path, publish them through the deployment repository in the same sequence and observe their independent readiness.

## Prepare team delivery

Add a permitted team repository and destination to each Spoke input before foundation rendering. The actual source field is:

```yaml
cluster:
  workloads:
    tenants:
      - name: learning
        source_repos:
          - https://git.example.test/team/deploy.git
        namespaces:
          - chapter5-probe
```

Replace the reserved example URL with your approved repository before live use. The platform installs the Workload Argo CD instance, AppProject, namespace and namespace-scoped access. An empty tenant list installs an instance without usable team projects. Management remains the foundation owner; Workload Argo CD may deploy only the allowed team's namespaced resources.

## Continue

The local exercise now has three valid declaration directories. A later live exercise also needs current conditions, Cluster UIDs, real Nodes and private ingress endpoints for both workload Spokes. Do not deploy the actual Information Mediator yet. Step 05 connects the two test paths first.
