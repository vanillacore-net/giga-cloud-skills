---
name: hosting-platform-planning
description: Plan one IaaS and Kubernetes platform for services.
version: 0.1.0
author: Karsten Samaschke, Hermes Agent
license: Proprietary
platforms: [linux, macos, windows]
metadata:
  provider: VanillaCore
  hermes:
    tags: [cloud, platform, iaas, kubernetes, architecture, results-app]
    related_skills:
      - hosting-needs-planning
      - public-service-platform-architecture
      - iaas-foundation-practitioner
      - kubernetes-cluster-lifecycle-practitioner
---
# Hosting platform planning

Use this skill to plan one platform on IaaS and Kubernetes that runs several services with different needs, and to draw it as an architecture diagram. It starts from a needs plan, ideally the `hosting_needs_plan` from `hosting-needs-planning`, and answers where each service runs, what it shares, where it is separated and what is still open. It plans; it does not provision anything.

## When to use

- A needs plan for two to four services exists and the next question is "how does one platform run all of them?".
- A team needs an architecture diagram that non-specialists can read on a screen.
- A proposed platform design needs to be challenged for shared failure, missing separation or components drawn on nothing.

Do not use it to install or configure OpenStack, Kubernetes or any other product, to size hardware from guesses, or to pick a provider. For real operations, use the IaaS and Kubernetes practitioner skills if they are installed.

## Input

```yaml
mode: ask | learn | work | challenge | review
case_id:
hosting_needs_plan:   # from hosting-needs-planning, or the same facts in prose
cases: []             # optional, the original case files
audience:             # optional
results_app:          # optional path of an app built by hosting-needs-planning
learner_answer:       # challenge and review modes
```

If no needs plan is supplied, build one first with `hosting-needs-planning`, or ask for the facts per service: data sensitivity, outage consequence, load pattern, dependencies, retention.

## Terms

Explain each term once, in a few words, when it first appears:

- **IaaS:** the layer that provides virtual machines, networks, storage and identity through an API.
- **Project:** a tenant boundary in the IaaS with its own resources, quotas and access.
- **Virtual machine:** a computer emulated on shared hardware with its own operating system.
- **Kubernetes cluster:** a group of machines that runs containers and keeps them in the declared state.
- **GPU:** a processor for parallel computation, needed for example by language models.

## Procedure

1. Restate per service the needs that shape the platform: sensitivity, availability window, load pattern, special hardware, retention, dependencies. Carry unknowns forward unchanged.
2. Decide the separation per service on the IaaS: own project or shared project, with the reason taken from the needs. Separate where sensitivity, availability or capacity reservation differ.
3. Decide the Kubernetes layout: one cluster per service or domain, or a shared cluster with namespaces. Prefer one cluster per service where failure reach, upgrade timing or data protection differ. Name the management function that creates and maintains the clusters.
4. Place the shared capabilities (public entry, sign-in, certificates, registry, observability, cluster management) and state which services depend on each. A shared capability is a shared failure point; say what happens to each service when it fails.
5. Give each service its own settings: reserved or elastic capacity, scaling range, GPU pool, storage class, backup and retention, network exposure.
6. Draw the architecture diagram following `references/page-rules.md`: every component sits on what it runs on, every relationship is an arrow from source to target.
7. Test the plan with one failed dependency while everything else is healthy, and state the user-visible effect per service.
8. Produce the `hosting_platform_plan` below. If a results app is in use, fill `platform.html` following `references/page-rules.md`.

## Learner modes

In `challenge` mode, if no learner claim or attempt is supplied, pose one bounded challenge and stop before the model answer. After the attempt, name the first unsupported step, correct it and offer one retry.

- **Ask:** Answer directly, name the layer (IaaS, cluster, shared capability, service) and what would prove the claim.
- **Learn:** Build the platform for one service first, then add the second and show what changes.
- **Work:** Produce the full plan and diagram with the user.
- **Challenge:** Obtain the learner's design first. Then fail one shared capability or one capacity pool and grade separation, shared failure and evidence separately.
- **Review:** Check an existing design for components drawn on nothing, missing separation, unjustified sharing, invented capacity figures and product recommendations.

## Output

```yaml
hosting_platform_plan:
  schema: hosting-platform-plan/v1
  case_id:
  inherited_needs_plan:
  iaas_projects: []          # per service or shared, with reason
  kubernetes_clusters: []    # per service or shared, with reason
  cluster_management:
  shared_capabilities: []    # with dependent services and failure effect
  per_service_settings: []   # capacity, scaling, GPU, storage, retention, exposure
  failure_test: []           # one failed dependency, effect per service
  diagram:                   # inline SVG or a description of nodes and arrows
  open_items: []
```

## Challenge checks

Reject these inferences unless the missing evidence is supplied:

- One shared cluster is always cheaper and therefore better.
- A running virtual machine or Pod means the service recovered.
- Kubernetes alone is the complete platform.
- A shared capability is resilient because each consumer is healthy.
- A diagram proves isolation, capacity or recovery.

## Pitfalls

- Do not invent node counts, GPU numbers or capacity figures. Ask, or mark them open.
- Do not draw a component floating without the layer it runs on.
- Keep product names out of the plan unless the user supplied them as fixed facts.
- Two concurrent agent sessions writing the same results app overwrite each other. Use one session per app.

## Verification

The result passes when every service has a stated IaaS project and cluster placement with a reason from its needs, every shared capability lists its dependents and failure effect, the failure test shows user-visible effects per service, unknowns stay open, no provider or product is recommended, and a filled `platform.html` keeps the app's header, footer and styles intact.
