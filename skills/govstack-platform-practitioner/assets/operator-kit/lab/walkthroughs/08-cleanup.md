# 08: Retire a Spoke

We normally keep both Spokes for Chapter 6. A retirement exercise needs a separate disposable repetition or a reviewed rebuild/retention plan. Removing one Spoke must not remove the LoadBalancer, Management or the other workload Spoke.

## Decide what happens to data

Stop new team delivery and decide which application data, claims, cloud volumes, object data, domains and certificates must be retained or removed. Record the owner and stable IDs privately. A successful write test does not make the data disposable, and replica counts do not establish recovery.

Withdraw the selected public route only after its traffic/retention decision. Keep private Management available for cleanup. Removing an ApplicationSet input directory deliberately does not prove that its infrastructure has been destroyed.

## Current stop

```bash
"$PYTHON" "$LAB/scripts/platform.py" retire --case "$CASE" --target examples
```

At this revision the result is `RETIRE_BLOCKED`, exit 2, before any delete starts. The rendered foundation applications/destinations and exact teardown ownership contract disagree. The source must be repaired and tested at a new reviewed kit revision before this procedure can be executed safely.

Keep the declarations, resource IDs and identities while the blocker remains. Do not widen the allowlist, remove finalizers, relabel ownership, run a whole-tenant reset or revoke credentials while deletion still needs them. The block is an implementation dependency, not a successful cleanup result.

## Required live end state after repair

A released cleanup procedure must stop the selected higher-level reconciliation, verify the exact Cluster UID and resource ownership, remove only the selected child's foundations and CAPI resources, wait with a deadline for their cloud resources to disappear by ID, then revoke that child's identities. Verify which volumes/data/DNS were retained by agreement. An absent Kubernetes Cluster is not evidence that every VM, port or volume is absent.

The LoadBalancer, Management and other Spoke remain. Report any unresolved resource as retained, blocked or failed, with a bounded next action; never report a partial cleanup as complete.

## Continue to Chapter 6

For local preparation, export the limited intermediate handoff:

```bash
"$PYTHON" "$LAB/scripts/platform.py" handoff --case "$CASE"
```

It labels preparation rather than a live platform. A live readback can be requested only for an approved real case, and still does not establish the entire backend identity chain. The practitioner skill builds its separate `platform_runtime_record/v1` from real evidence and validates that contract; renaming this intermediate JSON file is not conversion.

Chapter 6 needs the two distinct retained cluster/context identities, allowed application repositories/namespaces, domains and trust, workload/storage choices and any unresolved dependency. The Information Mediator and business example applications are not installed by this chapter.
