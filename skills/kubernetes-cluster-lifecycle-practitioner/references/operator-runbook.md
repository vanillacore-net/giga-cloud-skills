# Chapter 4 operator runbook

This runbook turns the Chapter 4 practitioner skill into an executable cluster-lifecycle workflow on an approved OpenStack project. It covers a seed, a management cluster, CAPI/CAPO-managed child clusters, bounded Argo CD integration, scaling, upgrades, path validation and owner-aware cleanup. It is a production-oriented learning slice, not a complete production platform.

## Operator-kit boundary

The checked-in kit is under `assets/operator-kit/`. Never place kubeconfigs, credentials, local contracts, rendered live manifests, repository credentials or evidence in the installed skill directory. Create a protected working copy. Practical execution requires Bash and POSIX filesystem semantics. On Windows, use WSL or an equivalent POSIX environment; otherwise use the skill for explanation and review only.

```bash
set -euo pipefail
SKILL_DIR=/absolute/path/to/installed/kubernetes-cluster-lifecycle-practitioner
WORK_ROOT=/absolute/path/to/protected/work
WORK_DIR="$WORK_ROOT/giga-chapter-4-operator"
test -f "$SKILL_DIR/SKILL.md"
test ! -e "$WORK_DIR"
umask 077
mkdir -p "$WORK_ROOT"
cp -R "$SKILL_DIR/assets/operator-kit" "$WORK_DIR"
export GIGA_OPERATOR_KIT="$WORK_DIR/lab"
cd "$GIGA_OPERATOR_KIT"
./scripts/offline-validate.sh
```

Resolve `SKILL_DIR` from the host. The operator supplies `WORK_ROOT`. Do not guess paths, kubeconfig contexts or cloud values.

## Operations

| Operation | Goal | Default mutation level |
|---|---|---|
| `assess` | Check source pin, toolchain, IaaS handoff, ranges and version contract | None |
| `prepare` | Create local contracts, render declarations and review plans or diffs | Local files and read-only APIs |
| `provision` | Build seed infrastructure, management capability and child clusters | Live OpenStack and Kubernetes changes |
| `validate` | Prove controller convergence, identity chains and named control/data paths | Read-only plus approved disposable probes |
| `maintain` | Scale, upgrade, reconcile GitOps declarations and diagnose ownership | Live change when explicitly approved |
| `cleanup` | Stop higher-level reconciliation, delete through CAPI and prove IaaS absence | Live OpenStack, Kubernetes and Git change |

## Assess

1. Require the `iaas_technical_baseline` and verify its project, network, image, flavor, quota, route and placement inputs.
2. Read `SOURCE.md`, `lab/README.md` and `lab/VERSIONS.yaml`.
3. Run `lab/scripts/offline-validate.sh`.
4. Check the exact required versions of `kubectl`, `clusterctl`, OpenTofu, Ansible and supporting tools before a live run.
5. Check Node, Pod, Service, data-centre, VPN, transit and peer-cluster ranges for overlap.
6. Verify the Kubernetes-version and machine-image contract.

Missing `clusterctl` or provider schemas blocks provider installation and live custom-resource validation. It does not invalidate offline structure checks.

## Prepare

Create the ignored local environment contract:

```bash
set -euo pipefail
cd "$GIGA_OPERATOR_KIT"
test ! -e environment-contract.yaml
cp environment-contract.example.yaml environment-contract.yaml
chmod 600 environment-contract.yaml
```

Replace all examples, set `example_only: false`, then run local and read-only checks:

```bash
python3 scripts/preflight.py environment-contract.yaml
./scripts/preflight-readonly.sh environment-contract.yaml
```

Render declarations into the protected work directory. Validate YAML, matching CRD schemas or server-side dry-run, then review the exact diff. Do not apply during preparation.

## Live-change gate

Before any `provision`, mutating `maintain` or `cleanup` action, require:

- an approved OpenStack project and valid Chapter 3 handoff;
- protected cloud credentials and exact kubeconfig/context identities;
- a local contract that passes preflight without example override;
- reviewed network ranges, routes, capacity and machine-image contract;
- pinned Kubernetes, CAPI, CAPO, ORC, CNI, cert-manager, Contour, Local Path Provisioner and Argo CD versions as applicable;
- offline validation plus schema validation or server-side dry-run for the exact installed APIs;
- a reviewed OpenTofu plan, `kubectl diff` or equivalent change representation;
- explicit approval for the named operation and targets;
- bounded waits, failure states and owner-aware cleanup.

If any condition is absent, stop at `prepared`, `blocked` or `unverified`.

## Provision

Follow the nine walkthroughs in order. The operational ownership sequence is:

1. OpenTofu creates seed IaaS resources.
2. Ansible and kubeadm establish the seed Kubernetes API.
3. The pinned provider matrix establishes CAPI and CAPO lifecycle control.
4. The management cluster owns child-cluster declarations.
5. CAPI and CAPO create child machines and OpenStack resources.
6. The pinned CNI establishes Pod networking.
7. Reconciled add-on declarations establish the bounded storage baseline, cert-manager and private Contour/Envoy ingress per child cluster.
8. The management path reuses the provider-installed cert-manager and adds its bounded Contour ingress path.
9. Argo CD may own reviewed cluster and workload declarations after its repository and destination boundaries are explicit.

After each state change, run the next-layer validation before continuing.

## Validate

Use the supplied scripts to verify:

- management-to-child Kubernetes API reachability;
- CAPI Cluster and Machine conditions;
- provider infrastructure objects and stable OpenStack server IDs;
- Node provider IDs and `Ready` conditions;
- CNI readiness;
- cert-manager and private Contour/Envoy readiness in each named cluster;
- a disposable PersistentVolumeClaim and read/write Pod for the bounded storage smoke test;
- the specifically approved public-edge to workload-Envoy to Service to Pods path;
- Argo CD source revision, sync and health separately from workload behaviour.

A CAPI `Available` condition, ready Node or Argo CD `Synced` status proves only its named layer.

## Maintain

For scaling, modify the owning declaration with `set-worker-replicas.sh`, review the rendered change, approve it, then use `scale-workers.sh` and verify both creation and deletion evidence.

For upgrades, bind one Kubernetes version to one compatible machine image, prepare with `set-cluster-upgrade.py`, validate and diff without apply, obtain approval, then run `upgrade-cluster.sh`. Observe CAPI rollout, Machines, OpenStack IDs, Nodes and the workload that must remain available.

For add-on maintenance, update one pinned component at a time, verify the upstream artifact checksum, render into the protected working copy, review the diff and prove rollout in each intended cluster. For GitOps, bind every result to the exact repository URL, revision, path and destination. Do not let a manual apply and Argo CD own the same declaration concurrently.

Diagnosis begins with ownership: desired declaration, responsible controller, provider object, IaaS resource and runtime object. Repair through the highest active owner rather than mutating lower layers directly.

## Cleanup

Follow walkthrough 09. Remove Git intent or stop Argo CD restoration first, unregister child targets while APIs still respond, capture stable OpenStack IDs, delete the owning CAPI Cluster, wait with explicit failure states, then prove IaaS absence by captured ID. Shared images, networks or retained resources need explicit ownership decisions.

## Excluded production concerns

The kit does not prove a highly available management cluster, production public-edge or TLS configuration, production storage acceptance, backup or recovery, or repository-specific authentication policy. Its private Contour/Envoy path and Local Path Provisioner smoke test prove only the named lab paths. Keep the remaining concerns as explicit Chapter 5 or environment-specific platform-operation gaps.

## Operator result

Return this record with the Chapter 4 handoff:

```yaml
operator_execution:
  kit_source:
  operation:
  working_directory:
  execution_level: explained | prepared | offline-validated | live-executed
  change_approval:
  checks: []
  changed_resource_ids: []
  evidence: []
  rollback_or_cleanup:
  status: passed | failed | blocked | unverified
```

Never include kubeconfig bodies, `clouds.yaml` contents, application credentials, tokens, private keys, certificates, OpenTofu state or saved plan bodies.
