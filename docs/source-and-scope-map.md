# Chapter source and scope map

This package turns the public GIGA Chapter 1 to 4 material into reusable learning workflows. It does not copy internal notes or claim that a chapter replaces current upstream product documentation.

## Reviewed chapter revisions

| Chapter | Reviewed public source | Learning boundary |
|---|---|---|
| 1 | `giga/content` commit `1ad5168a92e0b5187b99ef740e4a9c5f0c251c5b`, `chapter-1/chapter-1.md` | Service and workload facts, operating arrangements, accountability, dependencies, continuity, cost, and exit. |
| 2 | `giga/content` commit `1ad5168a92e0b5187b99ef740e4a9c5f0c251c5b`, `chapter-2/chapter-2.md` | Service dependencies, physical conditions, governed IaaS, foundation/platform/service boundaries, containers, orchestration, and shared capabilities. |
| 3 | `giga/content` commit `65055f17aaf13cf1944e2f4c4e1180dd3b94478a`, `chapter-3/chapter-3.md` and `chapter-3/lab/` | IaaS resource model and validation, with OpenStack, Horizon, OpenStackClient, and OpenTofu as the worked reference. |
| 4 | `giga/content` commit `6d8d1c004988f3e0fcf72e25f5f2428286a7d883`, `chapter-4/chapter-4.md` and `chapter-4/lab/` | Kubernetes cluster lifecycle on IaaS, with Cluster API, CAPO, and a bounded Argo CD path as the worked reference. |

At package validation for version `0.3.0`, the remote heads were:

- `chapter/digital-sovereignty-1-2` at `1ad5168a92e0b5187b99ef740e4a9c5f0c251c5b`. Its Chapter 1 and Chapter 2 trees matched `main` at `aab5f88ad500883274d03923505f02535b034dab`.
- `chapter/3-lab-video-package` at `65055f17aaf13cf1944e2f4c4e1180dd3b94478a`. This newer learning-package branch had not been merged into `main`; `main` contained a different Chapter 3 tree.
- `chapter/4-capi-openstack` at `6d8d1c004988f3e0fcf72e25f5f2428286a7d883`. Chapter 4 was branch-only and absent from `main`.

This non-linear source state is intentional evidence context, not a claim that all chapter revisions are already published from `main`. Recheck branch heads before a later package release and record any material difference rather than silently moving a pin.

Immutable reading links:

- [Chapter 1](https://git.vanillacore.net/giga/content/src/commit/1ad5168a92e0b5187b99ef740e4a9c5f0c251c5b/chapter-1/chapter-1.md)
- [Chapter 2](https://git.vanillacore.net/giga/content/src/commit/1ad5168a92e0b5187b99ef740e4a9c5f0c251c5b/chapter-2/chapter-2.md)
- [Chapter 3](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/chapter-3.md)
- [Chapter 3 lab](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/lab/README.md)
- [Chapter 4](https://git.vanillacore.net/giga/content/src/commit/6d8d1c004988f3e0fcf72e25f5f2428286a7d883/chapter-4/chapter-4.md)
- [Chapter 4 lab](https://git.vanillacore.net/giga/content/src/commit/6d8d1c004988f3e0fcf72e25f5f2428286a7d883/chapter-4/lab/README.md)

## Scope rules

1. Chapter 1 chooses a bounded next step for one service or workload. It does not approve a provider or architecture.
2. Chapter 2 turns service needs into foundation and platform conditions. It does not configure OpenStack or Kubernetes.
3. Chapter 3 turns an approved IaaS requirement into a tested technical baseline. It explains a generic capability before mapping it to OpenStack.
4. Chapter 4 consumes that baseline and manages Kubernetes cluster lifecycle. It does not claim that a Kubernetes cluster is a complete multi-team platform.
5. A later chapter owns the complete shared-platform operating model and end-user workload lifecycle.

## Known source tensions

- Chapter 1 says that the plugin contains six skills. This package revision adds a cross-chapter guide and two practitioner skills, so that count is historical until the chapter text is updated.
- Chapter 4's scope record says Chapter 5 adds GitOps, while the current Chapter 4 manuscript and lab already include a bounded Argo CD exercise for cluster declarations and one demonstration workload. This package follows the executable Chapter 4 material for that bounded exercise. It reserves broader platform delivery, access, observability, recovery, and multi-team operation for Chapter 5.

Do not silently resolve future chapter contradictions. Name the conflicting files or revisions, state the interpretation used for the current answer, and keep the affected claim conditional until the source is aligned.
