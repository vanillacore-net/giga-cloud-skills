# GIGA Cloud Agent Plugin

A portable plugin package for Claude Code and Codex. It gives delivery, sales, research, and writing agents a public-safe way to reason about cloud delivery choices without receiving Chapter 1 drafts, internal source material, meeting notes, or vault access.

## Published agent skills

- `public-service-platform-architecture`: entry point for turning a service need into foundation, platform, responsibility and readiness questions. It routes to the focused skills below when needed.
- `cloud-delivery-model-advisor`: compares public-service hosting and cloud delivery options under supplied constraints.
- `workload-cloud-fit-assessment`: profiles service facts, uncertainty, and the institutional checks that must follow.
- `cloud-interoperability-explainer`: explains cloud, interoperability, portability, and dependency conditions without slogans.
- `cloud-decision-gap-discovery`: prioritizes unanswered hosting and cloud evidence needs.
- `cloud-decision-matrix-steward`: maintains one reviewable, evidence-based hosting decision matrix.

These are agent-consumable skills. They are not Hermes internal editorial or release-control skills.

## Platform integration

- **Claude Code:** `.claude-plugin/plugin.json` identifies this repository as a Claude plugin and Claude discovers skill folders beneath `skills/`.
- **Codex:** `.codex-plugin/plugin.json` packages the same `skills/` directory as a Codex plugin. In Codex CLI, use `/plugins` to install it from a configured marketplace, then begin a new session. Each skill also includes `agents/openai.yaml` metadata.

## Install and use

See [Install and use the GIGA Cloud Agent Plugin](docs/install-and-use.md) for Hermes direct installation, chapter-level invocation, focused-skill invocation, and Claude Code or Codex plugin use.

## Data boundary

The plugin contains public-safe workflows and structured outputs only. It does not contain Chapter 1 content or private evidence. An organisation may connect a restricted capability service later, but the plugin remains useful without it: it identifies what can be reasoned from supplied facts and what must be checked locally.

## Private Forgejo wiki and GitBook

A private Forgejo wiki makes sense as the editorial reading and review surface when its access list is controlled by VanillaCore. It gives reviewers a native, page-oriented view of draft length and flow. Do not treat it as a separate security control from the repository, because its history follows wiki permissions.

Use the wiki for controlled authoring and review, then export an approved snapshot as Markdown, DOCX, or PDF into the GitBook release repository. See `docs/forgejo-wiki-to-gitbook.md`.

## Validation

```bash
python3 scripts/validate_skills.py
```
