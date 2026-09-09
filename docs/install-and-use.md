# Install and use the GIGA Cloud Learning Skills

The package has nine user-facing skills. Install `giga-cloud-learning-guide` when a learner needs the Chapter 1 to 4 journey or is unsure where a question belongs. Install a focused skill when the question and handoff are already bounded.

## Direct skill installation

Hermes supports direct installation from a public HTTPS `SKILL.md` URL and fetches explicitly referenced support files. Its URL-safety guard rejects hosts that resolve to private or internal addresses. In an environment where this Forgejo host is internal, use a checked-out repository instead of claiming that the Raw URL is installable.

From the root of a trusted checkout, install the cross-chapter guide into an empty destination:

```bash
skill=giga-cloud-learning-guide
install_root="${HERMES_HOME:-$HOME/.hermes}/skills"
test ! -e "$install_root/$skill"
mkdir -p "$install_root"
cp -R "skills/$skill" "$install_root/$skill"
```

This copies `SKILL.md` and `references/chapter-contracts.md` together. For a URL hosted on a public endpoint accepted by Hermes, the equivalent command is:

```bash
hermes skills install https://PUBLIC-HOST/PATH/giga-cloud-learning-guide/SKILL.md
```

The URL form and support-file retrieval are documented in the current [Hermes CLI reference](https://hermes-agent.nousresearch.com/docs/reference/cli-commands). The guide refers to focused sibling skills, so install those separately when required, or install the complete repository as a Claude or Codex plugin.

Check discovery with `hermes skills list`. Start a new Hermes session after installation, then invoke the guide explicitly:

```text
/skill giga-cloud-learning-guide
```

## Choose a mode

```yaml
mode: ask | learn | work | challenge | review
chapter: auto | 1 | 2 | 3 | 4
case:
  service_outcome:
  supplied_facts: []
  supplied_evidence: []
question:
artifact:
constraints: []
```

Examples:

```text
Use giga-cloud-learning-guide in learn mode. Explain why placement,
managed service layer, and operating model are separate Chapter 1 choices.
End with one exercise and do not reveal the answer until I attempt it.
```

```text
Use giga-cloud-learning-guide in challenge mode for Chapter 2.
I claim that our service is recovered because its VM is ACTIVE.
Challenge the claim and identify the user-visible evidence still required.
```

```text
Use iaas-foundation-practitioner in review mode. Check this OpenStack
runbook for architecture, content, syntax, and evidence. Treat all local
values as unknown unless they appear in the supplied evidence.
```

```text
Use kubernetes-cluster-lifecycle-practitioner in work mode. Consume this
iaas_technical_baseline and help me produce a cluster_runtime_baseline_record.
Keep Cluster API, CAPO, and Argo CD ownership separate.
```

## Focused skills

| Need | Skill |
|---|---|
| Bound the service and workload | `workload-cloud-fit-assessment` |
| Compare operating arrangements | `cloud-delivery-model-advisor` |
| Test interoperability, portability, dependencies, or exit | `cloud-interoperability-explainer` |
| Turn unknowns into evidence work | `cloud-decision-gap-discovery` |
| Build the Chapter 1 decision record | `cloud-decision-matrix-steward` |
| Build or challenge the Chapter 2 architecture brief | `public-service-platform-architecture` |
| Explain or review the Chapter 3 IaaS baseline | `iaas-foundation-practitioner` |
| Explain or review the Chapter 4 cluster lifecycle | `kubernetes-cluster-lifecycle-practitioner` |

For a checked-out repository installation, repeat the copy command above with the focused skill name. A copied Chapter 3 or Chapter 4 skill keeps its local `references/` files. For a public URL installation, replace the final skill directory in the public endpoint URL.

## Claude Code and Codex

The repository ships `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`. Add the repository to the approved plugin source or marketplace. Install `vanillacore-cloud-skills` in Claude Code or `vanillacore-giga-cloud` in Codex, then begin a new session so the client discovers every folder under `skills/`.

## Evidence discipline

The skills can explain generic mechanisms and review supplied artifacts. They cannot infer project IDs, quotas, capacity, routes, credentials, provider versions, live reconciliation, recovery, or cleanup. Parser success and static validation remain distinct from live evidence. Source revisions and known contradictions are recorded in `source-and-scope-map.md`.
