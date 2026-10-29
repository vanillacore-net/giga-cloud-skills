# Install and use the GIGA Cloud Learning Skills

The package has sixteen user-facing skills. Install `giga-cloud-learning-guide` when a learner needs the Chapter 1 to 4 journey or is unsure where a question belongs. Install a focused skill when the question and handoff are already bounded.

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

This copies `SKILL.md` and `references/chapter-contracts.md` together. For the Chapter 3 and Chapter 4 practitioner skills, the same checkout method also copies the practical `assets/operator-kit/` tree. For a URL hosted on a public endpoint accepted by Hermes, the equivalent command is:

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
operation: assess | prepare | provision | validate | maintain | cleanup
execution: explain | prepare | execute
working_directory:
change_approval:
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
Use kubernetes-cluster-lifecycle-practitioner in work mode with operation assess
and execution prepare. Consume this iaas_technical_baseline, copy the portable
operator kit to /protected/work/chapter-4, run its offline checks, and prepare a
cluster_runtime_baseline_record. Do not make a live change.
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
| Learn, operate or review the Chapter 3 IaaS baseline | `iaas-foundation-practitioner` |
| Learn, operate or review the Chapter 4 cluster lifecycle | `kubernetes-cluster-lifecycle-practitioner` |

For a checked-out repository installation, repeat the copy command above with the focused skill name. A copied Chapter 3 or Chapter 4 skill keeps its local `references/` and `assets/operator-kit/` files. Before practical use, copy `assets/operator-kit/` again to a protected work location and run `lab/scripts/offline-validate.sh`; never write live inputs into the installed skill. A direct `SKILL.md` URL is sufficient only when the installer and hosting endpoint also preserve the complete operator-kit tree. Otherwise use the verified checkout or plugin installation for practical operations.

## Independent OpenStack usage

For an existing OpenStack environment, install the focused usage skills you need and optionally the coordinator. Choose from `openstack-environment`, `openstack-compute`, `openstack-networking`, `openstack-storage` and `openstack-troubleshooting`. Copy the complete skill directory from the reviewed checkout, not just its SKILL.md. This includes local references, the standalone CLI, checksum manifest and source record.

Runtime tools are Python 3 and an OpenStackClient installation appropriate for the target APIs. This release checks syntax against OpenStackClient 8.2.0. It does not redistribute the client or provide credentials. Use a protected local cloud-profile configuration with permissions for the selected project and action.

A focused skill resolves its own installed path and copies its operator kit to an operator-supplied protected working directory. Inspect uses real read-only calls; prepare validates the target and creates a proposal without cloud changes; execute checks the exact approved proposal digest before mutation. The local `references/operations-api.md` is the executable contract and includes the supported action fields. Do not write live files into the installed skill.

Examples of useful requests:

```text
Use openstack-environment. Inspect my supplied project and region, list my VMs,
and report current quota and which checks were denied. Do not change anything.
```

```text
Use openstack-networking. Prepare a private network and subnet in my existing
project. Use my supplied CIDR and external network. Review each proposed
operation before execution, and preserve created IDs for the VM step.
```

```text
Use openstack-storage. Prepare an extension of this identified data volume.
Explain the subsequent guest filesystem work separately. Do not apply yet.
```

```text
Use giga-cloud-learning-guide. Diagnose why this private VM is unreachable.
Reuse my case context and stable IDs. A missing floating IP is expected.
Keep the investigation read-only and hand off any repair as a separate proposal.
```

These are not automatic approvals. For a mutating request, the agent must show the actual prepared proposal and receive its action-specific approval. A proposal hash computed by the agent is not evidence that a person approved it. Existing OpenTofu, CAPI and GitOps owners remain authoritative.

Package, behavioral fixture and independent-copy tests are automated. Host skill activation and live tenant behavior are separate verification levels; neither is inferred from CLI help or a checksum check.

## Hosting planning and the results app

Install `hosting-needs-planning` and `hosting-platform-planning` together when two to four services should be planned side by side and shown on a screen. Each also works alone.

1. Write one `case-*.md` per service, following `skills/hosting-needs-planning/assets/examples/cases/`.
2. Build the app in your own working directory, never inside the installed skill:

   ```bash
   python3 <skill>/assets/results-app/build_app.py --cases ./cases --out ./out --config app.json
   python3 -m http.server 8765 --directory ./out
   ```

3. In an agent session in the same working directory, ask for the planning step, then the platform step:

   ```text
   Look at the cases in cases/. What does each one need from its hosting, and how can one platform run all of them? Use hosting-needs-planning and fill out/planning.html.
   ```

   ```text
   Plan that platform with IaaS and Kubernetes and fill out/platform.html, with an architecture diagram. Use hosting-platform-planning.
   ```

Rebuild the app to reset both result pages. Run one agent session per app; two sessions overwrite each other's pages.

## Claude Code and Codex

The repository ships `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`. Add the repository to the approved plugin source or marketplace. Install `giga-cloud-skills` in Claude Code or Codex, then begin a new session so the client discovers every folder under `skills/`.

## Evidence discipline

The skills can explain generic mechanisms, review supplied artifacts, and execute the packaged Chapter 3 and 4 workflows when the host has the required tools and the operation gate is complete. They cannot infer project IDs, quotas, capacity, routes, credentials, provider versions, live reconciliation, recovery, or cleanup. Parser success and static validation remain distinct from live evidence. Source revisions and known contradictions are recorded in `source-and-scope-map.md`.
