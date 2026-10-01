# OpenStack toolkit 0.5.0 validation

The package contains fourteen skills, including five independent OpenStack tenant-usage skills. Validation was performed on 1 October 2026. Every test below ran; none contacted an OpenStack or Kubernetes API. The installed OpenStackClient help checks used version 8.2.0.

## Results

| Check | Result | Evidence scope |
|---|---|---|
| Skill/package validation | 14 skills, 4 chapter contracts, 2 plugin manifests passed | Frontmatter, local references, relationships, schema names, public-safety markers and client identity/version consistency |
| Existing learning-path suite | 8 routes, 4 chapter contracts, 4 handoffs passed | Existing Chapter 1 to 4 contracts remain intact |
| Original operator-kit suite | 2 kits, 6 operations passed | Original kit checksums, syntax, portable paths and offline lab validation |
| Runtime behavioral fixtures | 29 tests passed | Real helper subprocesses against an explicit synthetic client, not live API responses |
| Operational regressions | 7 tests passed | Usable sanitized inventory, live ownership-marker conflicts, changed target state, malformed inputs, retained config-file locations and cloud-init path binding across caller directories |
| Network/storage positive fixtures | 3 tests passed | Private network creation, exact volume-capacity readback and rejection of transferred-plan replay |
| Operational routing | 26 tests passed | English/German tasks, explicit inspection/explanation, prior case/IDs, ownership continuation, missing inputs, multi-domain continuations and explicit-domain prerequisite ordering |
| Independent package checks | 6 tests passed | Exact standalone runtime bytes, isolated skill copy/help execution, local contracts and final-file manifests, documented work-copy paths |
| Chapter 4 invocation regressions | 2 tests passed | Extracted documented commands executed in isolated fresh Bash processes with explicitly synthetic targets and client executables |
| Complete unittest discovery | 73 tests passed | All six modules above |
| Real-client command syntax | 27 supported actions passed | Every emitted mutation command prefix and option checked against actual OpenStackClient 8.2.0 help; no API call |
| Static source/security checks | Passed | Python compilation, whitespace and scans for shell injection, eval/exec, unsafe pickle, private machine paths and secret literals |
| Shell-snippet syntax | 28 blocks passed | Bash parser only, no snippet execution |

The secret-literal scan finds only two explicit `TOP_SECRET` sentinels in negative tests. Those test strings exercise redaction and environment override removal; they are not authentication material.

## Reproduction

Use the complete reviewed checkout and an appropriate Python/OpenStackClient environment:

```bash
python3 scripts/validate_skills.py
python3 scripts/test_learning_paths.py
python3 scripts/test_operator_kits.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/check_openstack_client_syntax.py --client openstack
git diff --check
```

`package_openstack_usage.py` is a build tool, not a cloud operator. The release process copies the canonical runtime and local API contract into each independent skill, seals final kit files and pins SOURCE.md to the reviewed runtime/API source commit. Each installed skill's copied work directory can run `scripts/verify_kit.py` before adding local inputs.

## Acceptance boundary

Inspection and preparation are read-only cloud operations. Execution requires the exact approved saved-plan digest, matching identity/project/region and relevant target state, direct ownership attestation without conflicting visible controller markers, protected work-root binding and unexpired approval. Created IDs are checkpointed before postcondition waits. Partial failures do not trigger automatic retries or cleanup.

Independent reviews were split into coordinator, execution/security and packaging/documentation panels. Blocking findings received bounded repairs and targeted regression tests. A delayed coordinator report exposed a missed finding: an explicit domain could reorder multi-domain creation ahead of prerequisite networking. The original no-remaining-must-fixes verdict was withdrawn in the PR. The added RED-GREEN regression and bounded independent recheck passed, restoring coordinator acceptance for this finding. Non-blocking expansion suggestions do not change this release's action catalogue.

These results do not prove host skill activation, cloud-specific API/microversion support, actual tenant policy, live network traffic, guest filesystem changes, application health, online snapshot consistency or recovery. Unknown controller ownership remains an operator evidence gap, not something absence of a metadata tag can settle. Read the local [operations API](openstack-operations-api.md) for the supported actions and explicit handoff boundaries, including unattached-volume extension and snapshot restrictions.

No live resources were created, modified or deleted during validation.
