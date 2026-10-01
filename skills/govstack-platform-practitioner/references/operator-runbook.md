# Protected platform operating runbook

## Installation and preparation

Install the entire skill directory from a trusted checkout or verified plugin. A bare `SKILL.md` URL does not establish that the operator-kit tree was installed. The kit must include `SOURCE.md`, `MANIFEST.sha256`, `THIRD_PARTY_NOTICES.md`, `lab/README.md` and `lab/scripts/platform.py`. If any is absent, report `blocked`; do not create replacement runnable files.

Before copying, inspect the kit inventory and run `sha256sum -c MANIFEST.sha256` inside `assets/operator-kit/`. Reject checksum drift and any symlink escaping the kit. Choose an empty owner-controlled working directory outside the installed skill and Git, use restrictive permissions (`umask 077`), and copy the full kit there. Keep original immutable files unchanged. Runtime contracts, credentials, Kubeconfigs, rendered manifests, plans, state, resource ledgers and evidence live only in this protected working copy. Record their paths, not their secrets, in learner-facing output.

Run the copied lab's documented offline suite and read `lab/README.md`. Query the actual interface before using flags:

```bash
python3 lab/scripts/platform.py --help
```

This is executable only after kit verification and copying. The chapter interface exposes `init`, `doctor`, `bootstrap`, `render`, `route`, `probe`, `status`, `scale`, `replace`, `upgrade`, `retire`, `handoff`. Read subcommand help and the lab's documented plan/execute switches; do not invent argument syntax, assume a render applies resources, or interpret a default as mutation approval.

## Intent and gate

- `explain`: teach and return `explained`, with live claims unverified.
- `prepare`: validate the kit, prepare supplied target values, render/review local plans and perform explicitly scoped read-only discovery. Report `prepared` or `offline-validated` only for checks actually run.
- `execute`: require all of approved target, protected credentials, supplied local values, offline validation, read-only discovery, reviewed plan or diff, explicit operation approval, bounded validation, recovery and owner-aware cleanup/retention. No live deployment is authorized by installation or by this document.

Require named OpenStack project/region and IDs, exact management context, role-specific contexts/configs, local pinned `bootstrap_repo`, environment config, inventory, infrastructure outputs, image metadata, domains/TLS ownership, non-overlapping CIDRs, quota/capacity evidence and connectivity. Read paths and source revisions from the session; never substitute local paths from the author's machine. Preserve only sanitized output and stable IDs. Credentials and sensitive command arguments must not appear in evidence.

## Operation map

| Phase | Actual lab interface | Gate and continuation evidence |
|---|---|---|
| Assess / prepare | `init`, `doctor` | Create the session from supplied values. Inspect source pin and clean reviewed checkout; verify target contract, tools and kit. Missing facts block execute. |
| Management/gateway | `bootstrap` | Review infrastructure/Ansible plan and scope, approve exact target; bounded management readiness and gateway/private API access. |
| Child declarations | `render` plus documented deployment path | Review LoadBalancer first, then `mediator` and `examples`; approve applications before any apply/sync; capture all three role identities, conditions, Nodes and ownership. Rendering alone proves none of them exist. |
| Connect | `route` | Review exact domains, DNS/TLS and edge/backend diff; approve route mutation. Keep workload Envoys private. Verify certificate identity and one edge/private chain per spoke. |
| Validate / use | `probe`, `status` | Readiness separately from real external requests, backend selection, Envoy, endpoints and Pods. A disposable probe is not a Chapter 6 business workload. |
| Maintain | `scale`, `replace`, `upgrade` | Review owner/diff and exact version/image for upgrade. Approve the named target; capture convergence, changed resource IDs and post-change route/use evidence. |
| Cleanup | `retire` | See source blocker below. Preserve IDs, stop higher-level reconciliation, require UID-bound ownership/allowlists, bounded deletion and OpenStack absence by ID. |
| Continue | `handoff` | Export the limited `chapter5-handoff/v1` CLI intermediate, then construct the canonical `platform_runtime_record/v1` as described below. Preserve stable case/IDs, evidence and explicit retention/cleanup. Chapter 6 gets runtime inputs, not an invented application deployment. |

When a command fails, capture the real exit and first relevant error, mark the phase failed/blocked, and stop dependent operations. Bounded waits must have deadlines and failure conditions from the lab. Do not blindly retry mutation, bypass validation, remove finalizers, or reset the whole tenant. Compare desired/observed state before a reviewed retry. If the host cannot run a required tool, report that blocker instead of simulated output.

## Handoff: intermediate to canonical runtime record

The CLI emits `chapter5-handoff/v1`, not `platform_runtime_record/v1`. Default handoff is `prepared-only` with no live checks. `handoff --live` is `partial-live-readback`: it requires a non-deleting GovStackSpoke UID, current generation/observedGeneration agreement, rendered-versus-live controlPlane/workers replicas and optional rolloutAfter agreement, and desired/ready counts matching the live spec, then checks two HTTPS edge response markers. Its scope is only GovStackSpoke readback plus those edge probes; it does not verify the full backend/Envoy/Service/Pod identity chain or establish runtime acceptance.

The agent must construct the canonical `platform_runtime_record/v1` according to `SKILL.md` and `references/session-and-evidence.md`, retaining case ID, available UID/generation/status snapshots, actual scoped evidence, unknown fields, evidence gaps, and retention responsibilities. Collect missing identity/context/provider and application-path evidence separately before claiming runtime acceptance. Never merely rename the CLI schema or promote partial evidence to full convergence. Validate the constructed JSON record from the installed skill directory:

```bash
python3 scripts/validate_contract.py record /absolute/protected/path/runtime-record.json
```

Structural validation is not runtime acceptance. Explain, adapt, deploy and operate against approved targets through reviewed procedures; a restriction or blocker in this pinned implementation is not a blanket restriction on platform practice.

## Known retirement source blocker

At bootstrap commit `1195f539afe5a1018be07d2e1865824c225ee407`, `scripts/delete-spoke-resources.sh` lists the existing foundation applications without `workload-argocd`, although foundation verification includes it. Its exact AppProject destination assertions stop at the original namespaces, while `templates/spoke-foundation-project.yaml.j2` includes `argocd` and configured tenant namespaces. Generated and accepted ownership contracts therefore disagree.

Report retirement `blocked` unless a **repaired reviewed source** is explicitly selected, pinned and tested for this topology. Never widen the allowlist automatically, relabel ownership, strip finalizers or report deletion success. A repaired source must be recorded as a deviation and validated against bootstrap/dashboard compatibility and teardown-positive/ownership-negative tests. Plan cleanup before provisioning; without a safe retirement or approved retention/recovery plan, stop provisioning too. Any partially attempted retirement needs real evidence, retained IDs and an explicit unresolved-resource list.

## Recovery and end state

Stop upstream reconciliation before owner-aware teardown. Retire spokes only through reviewed source, keep management/gateway available until child absence is proven, then retire the approved edge/foundation scope. Shared/external networks, credentials, data and DNS are deleted only when explicit ownership and approval permit it. Report each resource retained, absent, failed, blocked or unverified by stable ID; absence of a Kubernetes Cluster is not IaaS absence. Carry retained resources into the Chapter 6 handoff with responsibility and review trigger.
