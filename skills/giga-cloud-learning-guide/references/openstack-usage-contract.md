# OpenStack operational handoff

This contract is local to the installed coordinator. It does not depend on repository-level documentation or automatically authorize a change.

A routing request preserves `case_id`, `question`, optional `mode`, `execution`, explicit `domain`, `ownership`, `context` and `prior_handoff`. Context contains the supplied cloud-profile name, project ID and region. A cloud profile is never a credential body. Keep secrets out of both this request and the returned record.

`openstack-routing-record/v1` returns one `primary_skill`, optional `pending_skill`, an ordered `continuation_skills` list, the prior handoff, missing inputs, execution intent and next action. `mutation_authorized` is always false. The helper recognizes ordinary English and German task expressions; an ambiguous or unrecognized request must be clarified rather than forced into a cloud action. The host still activates the installed skill; routing tests do not prove host activation.

Execution intents are `explain`, `inspect`, `prepare`, `execute-requested` and `owner-continuation`. These are routing labels, not CLI subcommands. The CLI accepts `inspect`, `prepare` and `execute`. A valid digest in a routing request does not prove that the focused runtime's saved plan was approved or remains fresh.

The focused result is `openstack-operation-record/v1`, produced by the packaged OpenStack helper. Preserve the result verbatim as structured evidence and present a concise human summary. It identifies the case, domain/action, target project/region, execution level, checks, stable resource IDs, findings, status and next action. Consult the installed focused skill's local operations API for the exact field types. Never use a prose alias for a resource ID or turn missing evidence into a fabricated record.

The existing `iaas-technical-baseline/v1` contract remains unchanged. Evidence from a practical task may populate it when relevant, but a bounded inspection of existing resources does not need every chapter field. Chapter 4 still requires a coherent IaaS baseline before creating clusters.

For a cross-domain scenario, retain one case and a stable resource ledger. Each returned resource becomes a supplied dependency for the next action. An action may partially fail after cloud state changed; continue with its actual IDs and error status, never automatically replay creation or delete unrelated resources. A prior execution result is not approval for a retry.

Ownership is resolved per target. An OpenStack project may contain both direct tenant objects and controller-owned resources. Route CAPI ownership to the cluster lifecycle practitioner; OpenTofu/GitOps ownership requires the relevant declaration and reviewed plan/diff. Read-only diagnosis can retain IaaS evidence without obtaining write permission.

In challenge mode, ask for the learner's attempt and hold the correction. No challenge or demonstration authorizes a real cloud mutation.
