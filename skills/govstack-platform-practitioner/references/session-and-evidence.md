# Session and evidence contracts

## platform-session/v1

The protected session is the executable continuation boundary. The lab reads JSON only (`json.loads`); save executable local cases as JSON, not YAML. The following YAML is a conceptual field inventory, not a runnable example, and contains no default values:

```yaml
schema: platform-session/v1
case_id:
bootstrap_repo:
environment_config:
inventory:
infrastructure_outputs:
image_metadata:
management_context:
clusters:
  loadbalancer:
  mediator:
  examples:
cluster_configs:
  loadbalancer:
  mediator:
  examples:
domains:
tls:
```

The lab owns exact field representations and command flags; read its session example/help. `bootstrap_repo` is a local pinned checkout of the reviewed bootstrap dependency, not a mutable branch URL. Environment/inventory/outputs/image metadata are explicitly supplied local artifacts. `clusters` and `cluster_configs` preserve all three role keys, independently configured; role labels are not authorization to invent target names. Domains and TLS require real selected routing/certificate values or explicit blocked status, not arbitrary examples. Before execute, reject every missing target field or incomplete role map. Earlier preparation may preserve unknowns, but must label them blocked for execution.

`case_id` is stable through Chapter 6. Record resource IDs/UIDs, exact source revisions, names and ownership separately; do not replace identifiers during a handoff. Keep session and local evidence outside the installed skill and Git. Public output references protected paths and sanitized findings only, never credentials, private keys, kubeconfig contents or provider state.

## Evidence ladder

`execution` describes requested intent (`explain`, `prepare`, `execute`); `operator_execution.execution_level` describes work actually performed:

| Level | What was actually done | What it cannot prove |
|---|---|---|
| `explained` | Concept and scoped steps | Package, environment or live result |
| `prepared` | Supplied values and local plan/artifacts prepared | Offline suite success or live result |
| `offline-validated` | Named parser/schema/unit/package checks completed | Live reconciliation, routes, capacity or cleanup |
| `live-executed` | Real scoped live tool calls with target and evidence | Success of an entire platform; retain failed/blocked status when applicable |

Each check/evidence item uses a stable identifier, scope (`offline` or `live`), actual command/check, result and sanitized evidence reference. Mutation evidence additionally records approval and changed resource IDs. Live execution requires nonempty live evidence; no other execution level may carry live validation or claim live success. A read-only live status check is not a deployment claim. An unsuccessful mutation can still be `live-executed`; distinguish status from level.

Capture independent control-path and application-path evidence for each spoke. Successful route/use claims require real external requests and the backend/Envoy/Service/Pod identity chain, not only Argo CD Healthy, CAPI Ready or Pod Running. The bounded path probe is not an installed Information Mediator or example application.

## Runtime output and Chapter 6 continuation

The primary schema is embedded in `SKILL.md`: `platform_runtime_record` with schema `platform_runtime_record/v1`. A handoff preserves every required field even when its value is unknown, with `evidence_gaps` and a bounded next action. `workload_installation_boundary` stays `chapter-6`; actual workload installation is not claimed by the Chapter 5 record.

For each `chapter_6_inputs` entry preserve case ID, protected session reference, cluster UID/provider IDs and exact context/config mapping, reviewed dependencies, domains/TLS ownership, ingress/backend configuration, GitOps destination/owner, per-cluster baseline, retained resource responsibility and evidence gaps. Chapter 6 must obtain installation approval, artifact revisions and secret/data policies before deploying its actual workloads.

The CLI `handoff` output is a separate, limited `chapter5-handoff/v1` intermediate. Default evidence is `prepared-only`; `--live` yields only `partial-live-readback` for current GovStackSpoke spec/generation/readiness readback plus two HTTPS edge marker probes. Available case ID and UID/generation/status snapshots are continuation evidence, not full backend/Envoy/Service/Pod identity verification or runtime acceptance. The agent must construct the canonical `platform_runtime_record/v1` using the required schema in `SKILL.md`, explicitly preserving evidence gaps; simply renaming the intermediate schema is invalid.

Run `python3 scripts/validate_contract.py record /absolute/protected/path/runtime-record.json` from this skill to validate the constructed canonical JSON record. The validator also supports the minimum JSON session boundary. This structural validator supplements, not replaces, the lab's exact schema, source checks and real live gates. YAML local cases cannot be passed to the lab; convert the supplied values to JSON first. Do not infer a successful deployment from either parser.
