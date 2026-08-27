# Install and use the GIGA Cloud Agent Plugin

The package has six user-facing skills. `chapter-2-architecture-guide` is the chapter-level entry point. It routes a service-architecture question through the five focused cloud skills when needed.

## Install in Hermes Agent

Install the direct raw `SKILL.md` URL for the chapter-level guide:

```bash
hermes skills install \
  https://git.vanillacore.net/giga/cloud-skills/raw/branch/main/skills/chapter-2-architecture-guide/SKILL.md
```

Start a new Hermes session after installation, then invoke it explicitly:

```text
/skill chapter-2-architecture-guide
```

Or preload it from the command line:

```bash
hermes --skills chapter-2-architecture-guide
```

Check installation with:

```bash
hermes skills list
```

## Use the chapter-level guide

Provide a service description and ask for the architecture decision frame. For example:

```text
Use chapter-2-architecture-guide for a university enrolment service.
It serves students and staff through a public portal, uses federated identity,
keeps enrolment records, exchanges data with a registry, and must recover before
term starts. We need to decide what should be shared, where stronger boundaries
are needed, and whether a managed platform is credible.
```

The skill returns:

- known facts and assumptions;
- foundation conditions for placement, routes, identity, data and recovery;
- shared dependencies and failure-domain questions;
- container and platform implications;
- delivery-model questions;
- evidence gaps; and
- a foundation-readiness record.

It does not select a provider or prescribe a topology.

## Use a focused skill directly

Use a focused skill when the question is narrower:

| Need | Skill |
|---|---|
| Establish service facts and unknowns | `workload-cloud-fit-assessment` |
| Compare hosting, IaaS, managed platform or SaaS routes | `cloud-delivery-model-advisor` |
| Explain interoperability, portability and dependency limits | `cloud-interoperability-explainer` |
| Identify missing evidence before a decision | `cloud-decision-gap-discovery` |
| Maintain one reviewable local decision frame | `cloud-decision-matrix-steward` |

Install an individual Hermes skill by replacing the final path in the direct URL above, for example:

```bash
hermes skills install \
  https://git.vanillacore.net/giga/cloud-skills/raw/branch/main/skills/cloud-delivery-model-advisor/SKILL.md
```

## Claude Code and Codex

The repository ships both plugin manifests:

- `.claude-plugin/plugin.json` for Claude Code;
- `.codex-plugin/plugin.json` for Codex.

After adding this repository to the relevant Claude Code plugin source or Codex marketplace, install the `vanillacore-cloud-skills` plugin, then begin a new session so the client discovers `skills/`.

The package contains public-safe decision support only. Supply the local service facts and evidence needed for a real assessment. Do not expect the skill to invent missing legal, contractual, operational or recovery evidence.
