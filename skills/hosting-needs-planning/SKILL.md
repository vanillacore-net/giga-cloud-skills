---
name: hosting-needs-planning
description: Plan hosting needs for several services at once.
version: 0.1.0
author: Karsten Samaschke, Hermes Agent
license: Proprietary
platforms: [linux, macos, windows]
metadata:
  provider: VanillaCore
  hermes:
    tags: [cloud, hosting, workload, planning, platform, results-app]
    related_skills:
      - hosting-platform-planning
      - workload-cloud-fit-assessment
      - public-service-platform-architecture
---
# Hosting needs planning

Use this skill when two to four services carry the same label, for example "citizen services in the cloud" or "health data in the cloud", and someone has to decide what each one really needs from its hosting and whether one platform can run all of them. It turns short case files into a planning result: one needs profile per service, the shared and separate platform capabilities, and the questions that still block a decision. The result can be shown in a small results app that ships with the skill.

The skill is the first of two steps. `hosting-platform-planning` takes its result and plans the platform on IaaS and Kubernetes. Each skill works on its own.

## When to use

- A team, workshop or talk needs to show that a shared label hides different workload needs.
- Several services should share one platform and the boundaries between them are unclear.
- A planning result has to be presented to people who are not cloud specialists, on a screen or a projector.
- An existing planning answer needs to be challenged for missing users, failure consequences, dependencies or invented facts.

Do not use it to select a provider or a product, to approve a hosting decision, or to fill in legal, contractual, security or budget facts that were not supplied.

## Input

```yaml
mode: ask | learn | work | challenge | review
case_id:
cases: []            # case files, see "Case files"; 2 to 4 services
audience:            # optional, e.g. "ministry decision makers", "platform team"
results_app:         # optional path of a built app; omit for a chat-only answer
learner_answer:      # challenge and review modes
```

## Case files

One Markdown file per service, named `case-*.md`, in one directory:

```markdown
# Case A: Business permit applications

Label: "citizen services in the cloud"

- One supplied fact per bullet: users, data, volumes, peaks, deadlines,
  interfaces, what happens when the service is down.

Not supplied: what is still unknown, e.g. applicable law, recovery targets, budget.
```

Every bullet is a supplied fact. The `Not supplied` line lists unknowns the planning must keep visible. Two worked cases are in `assets/examples/cases/`. They are fictional and contain no real organisation's data.

## Procedure

1. Read every case. Restate only supplied facts. Mark anything else as an assumption or an unknown, never as a fact.
2. Profile each service on the same axes:
   - **Whose data:** which people or organisations, how sensitive, who may see it.
   - **What breaks for whom:** the user-visible consequence of an outage and how long it is tolerable.
   - **How it computes:** steady or peaky load, latency limits, special hardware such as GPUs.
   - **What it depends on:** external registers, payment, identity, operator feeds and other interfaces.
   - **Retention and evidence:** how long records must stay retrievable or verifiable.
   - **Blocking question:** the one unknown that stops a hosting decision for this service.
3. Compare the profiles. Show where the shared label hides different needs: sensitivity, availability window, load pattern, retention, dependencies.
4. Derive the platform capabilities that can be shared (for example public entry, sign-in, certificates, observability, cluster management) and the settings or boundaries each service needs on its own (data protection, capacity reservation, scaling range, retention, recovery). Sharing is justified only where sensitivity, availability, ownership and tolerance for shared failure are compatible.
5. List the open items once each, per service, without filling them in.
6. Produce the `hosting_needs_plan` below. If a results app is in use, fill `planning.html` following `references/page-rules.md`.
7. Hand off to `hosting-platform-planning` when the user wants the platform on IaaS and Kubernetes.

If the Chapter 1 and 2 learning skills of this package are installed, `workload-cloud-fit-assessment` can profile a single service in more depth and `public-service-platform-architecture` can map one service journey layer by layer. This skill does not depend on them.

## Results app

`assets/results-app/build_app.py` builds a small static web app from the case files: a start page, a case page and two empty result pages, `planning.html` and `platform.html`. It needs only Python 3.

```bash
# copy the app tooling next to your cases, outside the installed skill
python3 <skill>/assets/results-app/build_app.py --cases ./cases --out ./out
python3 <skill>/assets/results-app/build_app.py --cases ./cases --out ./out --config app.json
python3 -m http.server 8765 --directory ./out
```

`app.json` sets the title, the question, an optional logo, an accent colour, a context label (for example an event or team name) and links. Every key is optional; `assets/examples/app.json` shows all of them. Building again resets both result pages to empty. `--static` builds a start state without auto-reload, for publishing.

Write the app into a working directory of the user, never into the installed skill directory.

## Learner modes

In `challenge` mode, if no learner claim or attempt is supplied, pose one bounded challenge and stop before the model answer. After the attempt, name the first unsupported step, correct it and offer one retry.

- **Ask:** Answer the question directly from the supplied facts, name the axis it belongs to and the evidence still missing.
- **Learn:** Take one case, walk through the six axes and end with a short teach-back question.
- **Work:** Build the full plan with the user and fill the results app if one is in use.
- **Challenge:** Obtain the learner's claim first, for example "the data is public, so any cloud will do". Then test it against the cases: retained personal data, outage consequences, peak load, dependencies.
- **Review:** Check an existing plan for invented facts, missing axes, hidden unknowns, unjustified sharing and product recommendations.

## Output

```yaml
hosting_needs_plan:
  schema: hosting-needs-plan/v1
  case_id:
  services:
    - case:
      whose_data:
      what_breaks_for_whom:
      how_it_computes:
      depends_on: []
      retention_and_evidence:
      blocking_question:
      unknowns: []
  label_versus_needs: []
  shared_capabilities: []
  separate_per_service: []
  open_items: []
  handoff_to_platform_planning: []
```

## Challenge checks

Reject these inferences unless the missing evidence is supplied:

- Public source data means the service holds no personal data.
- The same label means the same hosting needs.
- A shared platform means shared failure is acceptable.
- A peak-free average load is enough to size capacity.
- An unknown such as recovery target or applicable law can be assumed.

## Pitfalls

- Do not fill an unknown with a plausible value. Keep it in the open-item colour.
- Do not name a provider or product. The plan describes needs and capabilities.
- Do not copy real case data from one organisation into another's example.
- Two concurrent agent sessions writing the same results app overwrite each other. Use one session per app.

## Verification

The result passes when every service is profiled on all six axes from supplied facts only, each unknown appears exactly once and stays unknown, shared and separate capabilities are justified by the profiles, no provider or product is recommended, and a filled `planning.html` keeps the app's header, footer and styles intact.
