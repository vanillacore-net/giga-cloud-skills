# Chapter 4 syntax and evidence validation

Pin the artifact's version contract before making field-level claims. The reviewed Chapter 4 source used a specific Kubernetes, CAPI, CAPO, ORC, and Argo CD matrix. Treat it as historical reference syntax, then check the learner's stated versions against current upstream schemas.

## Validation ladder

1. YAML parses and contains the intended documents.
2. Local structural checks find required objects, references, ranges, placeholders, and example-only values.
3. Schemas for the stated Kubernetes and custom-resource versions accept the object, or the matching installed API accepts a server-side dry-run.
4. A diff shows the exact intended change.
5. An approved apply reaches controller convergence within bounded waits.
6. Cross-system identity links CAPI Machines, provider infrastructure objects, IaaS server IDs, provider IDs, and Kubernetes Nodes.
7. Workload and network-path checks prove the specific runtime claim.
8. Cleanup proves absence by captured stable identifiers while preserving shared inputs.

## Syntax checks

- Parse YAML with a real parser and enumerate every `apiVersion` and `kind`.
- Use the stated CRD schemas or `kubectl --context "$CONTEXT" apply --server-side --dry-run=server -f "$FILE"` against a cluster with matching APIs before claiming schema acceptance.
- Treat `kubectl diff` exit code `1` as a detected change, not automatically an execution error.
- Validate shell, Ansible, and OpenTofu artifacts with their native tools. Static checks do not prove live behaviour.
- Do not expose kubeconfig bodies, `clouds.yaml` credentials, application credentials, tokens, private keys, certificate material, OpenTofu state, or saved plans.

Confirm every command against the installed tool version before classifying it as executable.

## Identity chain

A strong cluster-machine result checks:

1. the CAPI Cluster and namespace;
2. Machine ownership and labels;
3. the referenced provider infrastructure object;
4. the provider object's stable instance ID;
5. the matching IaaS server ID;
6. the normalized Kubernetes Node provider ID;
7. the Node `Ready` condition; and
8. expected cardinality at every join.

Names alone are not sufficient identity evidence.

## Claim calibration

- Parse success proves syntax structure only.
- Server-side dry-run proves acceptance by the contacted API and admission chain at that time, not reconciliation.
- CAPI `Available` proves the reported CAPI condition, not child Node readiness or service paths.
- Ready Nodes do not prove workload rollout or application reachability.
- Argo CD `Synced` proves comparison with the selected source revision, not backup, recovery, or user-visible service health.
- A path check proves only the named control or data path.

## Mutating-action gate

Default to explanation and offline review. Before a state change, require an approved environment, protected credentials, exact kubeconfig and context, namespace and object identity, supplied local values, server-side dry-run, reviewed diff, action-specific confirmation, bounded waits, failure states, and cleanup ownership.

## Source tensions

Do not reintroduce a helper invocation that its implementation rejects. The earlier [`6d8d1c0…` Chapter 4 lab](https://git.vanillacore.net/giga/content/src/commit/6d8d1c004988f3e0fcf72e25f5f2428286a7d883/chapter-4/lab/README.md) contained that mismatch in the load-balancer cleanup route. The [current reviewed operator-kit source](https://git.vanillacore.net/giga/content/src/commit/b56cad92b74b4335de99879415d437b97ab677cd/chapter-4/lab/README.md) corrects the path and tests its ownership-aware cleanup. Also keep seed and child CNI version pins role-specific, and qualify the Chapter 4 versus Chapter 5 GitOps boundary.
