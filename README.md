# GIGA Cloud Agent Plugin

A portable plugin package for Claude Code and Codex. It gives delivery, sales, research, and writing agents a public-safe way to reason about cloud delivery choices without receiving Chapter 1 drafts, internal source material, meeting notes, or vault access.

## Published agent skills

- `cloud-delivery-model-advisor`: frames a cloud delivery-model decision from a workload and operating context.
- `workload-cloud-fit-assessment`: identifies workload characteristics, decision constraints, and missing facts.
- `cloud-interoperability-explainer`: explains the conditions and mechanisms that can make cloud platforms support interoperability.
- `cloud-decision-gap-discovery`: turns vague cloud questions into a bounded set of local decisions, evidence needs, and deeper routes.

These are agent-consumable skills. They are not Hermes internal editorial or release-control skills.

## Platform integration

- **Claude Code:** `.claude-plugin/plugin.json` identifies this repository as a plugin and Claude discovers skill folders beneath `skills/`.
- **Codex:** each skill follows the open Agent Skills layout and includes `agents/openai.yaml` metadata. Install a skill directory, or distribute the repository as an Agent Skills plugin.

## Data boundary

The plugin contains public-safe workflows and structured outputs only. It does not contain Chapter 1 content or private evidence. An organisation may connect a restricted capability service later, but the plugin remains useful without it: it identifies what can be reasoned from supplied facts and what must be checked locally.

## Private Forgejo wiki and GitBook

A private Forgejo wiki makes sense as the editorial reading and review surface when its access list is controlled by VanillaCore. It gives reviewers a native, page-oriented view of draft length and flow. Do not treat it as a separate security control from the repository, because its history follows wiki permissions.

Use the wiki for controlled authoring and review, then export an approved snapshot as Markdown, DOCX, or PDF into the GitBook release repository. See `docs/forgejo-wiki-to-gitbook.md`.

## Validation

```bash
python3 scripts/validate_skills.py
```
