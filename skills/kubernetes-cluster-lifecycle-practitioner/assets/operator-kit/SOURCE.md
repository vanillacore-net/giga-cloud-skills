# Operator-kit source

- Source repository: `https://git.vanillacore.net/giga/content`
- Source commit: `b56cad92b74b4335de99879415d437b97ab677cd`
- Source path: `chapter-4/lab`
- Imported for: GIGA Cloud Chapter 4 practical skill execution

The operator kit preserves the source lab's environment contracts, examples, operational tests, safety gates and evidence boundaries. Portable adaptations replace repository-root assumptions and chapter-relative editorial links. Six source-package assertions that require `chapter-4.md` or `VIDEO_SCOPES.md` outside the lab are excluded. Two mixed tests retain their operational assertions without the external prose assertions. The portable copy runs 29 operational lab tests plus one source-pin test. The adaptations do not change the infrastructure model or turn example values into defaults.

## Documented invocation portability patch

The portable operator runbook passes the explicitly selected `OS_CLOUD` as the required second argument to `preflight-readonly.sh`. Cleanup walkthrough 09 supplies `CONFIRM_MANAGEMENT_CONTEXT="$MANAGEMENT_CONTEXT"` inline on both pre-deletion `capture-openstack-ids.py` invocations. This preserves the helper's confirmation gate and lets the documented capture commands run after loading `lab-session.env` in a fresh shell without inherited confirmation state.

Repository-level regression tests in `tests/test_chapter4_documented_invocations.py` execute the extracted commands in isolated Bash sessions using synthetic cloud, kubeconfig and resource values only. These documentation adaptations do not change the immutable source commit above or the lab's infrastructure and safety contracts.
