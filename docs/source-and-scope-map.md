# Chapter source and scope map

This package turns the public GIGA Chapter 1 to 5 material into reusable learning and operator workflows. It does not copy internal notes or claim that a chapter replaces current upstream product documentation.

## Reviewed chapter revisions

| Chapter | Reviewed public source | Learning and operator boundary |
|---|---|---|
| 1 | `giga/content` commit `1ad5168a92e0b5187b99ef740e4a9c5f0c251c5b`, `chapter-1/chapter-1.md` | Service and workload facts, operating arrangements, accountability, dependencies, continuity, cost, and exit. |
| 2 | `giga/content` commit `1ad5168a92e0b5187b99ef740e4a9c5f0c251c5b`, `chapter-2/chapter-2.md` | Service dependencies, physical conditions, governed IaaS, foundation/platform/service boundaries, containers, orchestration, and shared capabilities. |
| 3 | `giga/content` commit `65055f17aaf13cf1944e2f4c4e1180dd3b94478a`, `chapter-3/chapter-3.md` and `chapter-3/lab/` | IaaS resource model and tenant-resource operation, with OpenStack, Horizon, OpenStackClient, and OpenTofu as the worked reference. It does not install or operate an OpenStack control plane. |
| 4 | `giga/content` commit `b56cad92b74b4335de99879415d437b97ab677cd`, `chapter-4/chapter-4.md` and `chapter-4/lab/` | Kubernetes cluster lifecycle on IaaS, with Cluster API, CAPO, per-cluster cert-manager and Contour/Envoy ingress, a storage smoke baseline, and a bounded Argo CD path as the worked reference. It does not claim complete shared-platform operation. |

At package validation for version `0.4.0`, the remote heads were:

- `main` at `1dc2ae15376d88c980fcbf4b740b2f258c9f8a09`.
- `chapter/digital-sovereignty-1-2` at `1ad5168a92e0b5187b99ef740e4a9c5f0c251c5b`. Its Chapter 1 tree matched `main`. Its Chapter 2 tree differed from `main`; this package retains the previously reviewed `1ad5168…` Chapter 2 pin rather than moving it without a Chapter 2 review.
- `chapter/3-lab-video-package` at `65055f17aaf13cf1944e2f4c4e1180dd3b94478a`. This learning-package revision was not an ancestor of `main`, and its Chapter 3 tree differed materially from `main`. The package retains this reviewed revision because it contains the complete Chapter 3 lab used by the operator kit.
- `chapter/4-capi-openstack` at `b56cad92b74b4335de99879415d437b97ab677cd`. Its Chapter 4 tree matched `main`, and the commit was an ancestor of the current `main` head.

This non-linear source state is evidence context, not a claim that every reviewed revision is the current `main` version. Recheck branch heads before a later package release and record material differences rather than silently moving a pin.

The Chapter 3 and Chapter 4 practitioner skills carry portable operator kits imported from the lab paths at the exact revisions above. Their `SOURCE.md` and `MANIFEST.sha256` files record provenance, portability adaptations and final packaged checksums. Portable adaptations remove repository-root assumptions and replace chapter-relative editorial links. They do not change the infrastructure model, safety gates, example status or evidence boundary.

Immutable reading links:

- [Chapter 1](https://git.vanillacore.net/giga/content/src/commit/1ad5168a92e0b5187b99ef740e4a9c5f0c251c5b/chapter-1/chapter-1.md)
- [Chapter 2](https://git.vanillacore.net/giga/content/src/commit/1ad5168a92e0b5187b99ef740e4a9c5f0c251c5b/chapter-2/chapter-2.md)
- [Chapter 3](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/chapter-3.md)
- [Chapter 3 lab](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/lab/README.md)
- [Chapter 4](https://git.vanillacore.net/giga/content/src/commit/b56cad92b74b4335de99879415d437b97ab677cd/chapter-4/chapter-4.md)
- [Chapter 4 lab](https://git.vanillacore.net/giga/content/src/commit/b56cad92b74b4335de99879415d437b97ab677cd/chapter-4/lab/README.md)

## Version 0.5.0 operational extension

The immutable Chapter 3 source pin remains `65055f17aaf13cf1944e2f4c4e1180dd3b94478a`. That reviewed chapter package has since been merged into content main as `9b78032b56aa7070273d4b7e2794bbd82cd96a1d`; the historical pre-merge observations above describe version 0.4.0, not the current publication state.

Version 0.5.0 adds newly authored tenant-usage tools rather than relabeling the lab as a general operator. The five independently installed usage skills have a fixed action catalogue, local execution contracts and checksum-protected operator kits. Their source records identify the release runtime and its checked bytes. They use project/region-scoped OpenStackClient calls and do not install or repair the control plane.

The Chapter 4 kit retains its original source pin. Two portability-level documentation repairs supply the required cloud-profile argument for read-only preflight and explicit management-context confirmation before ID capture. Fresh-session regression tests cover those documented invocations. The final kit manifest is regenerated after the repairs.

No live cloud operation is implied by this source record. Version-specific client syntax, offline behavior, portable package checks and actual tenant acceptance are reported separately.

## Scope rules

1. Chapter 1 chooses a bounded next step for one service or workload. It does not approve a provider or architecture.
2. Chapter 2 turns service needs into foundation and platform conditions. It does not configure OpenStack or Kubernetes.
3. Chapter 3 turns an approved IaaS requirement into a tested tenant-resource baseline. It explains a generic capability before mapping it to OpenStack.
4. Chapter 4 consumes that baseline and manages Kubernetes cluster lifecycle, including the private workload ingress path and bounded storage and GitOps exercises in the reviewed lab. It does not claim that Kubernetes clusters form a complete multi-team platform.
5. Chapter 5 bootstraps and operates the bounded GovStack runtime in an existing tenant: management/gateway, LoadBalancer and two workload spokes. Actual IM/examples workload installation belongs to Chapter 6; production recovery and service acceptance remain evidence gates.

## Chapter 5 operational dependencies

The Chapter 5 practitioner uses the finalized local operator kit, not inaccessible chapter working sources. Bootstrap dependency: `https://git.vanillacore.net/govstack/govstack-bootstrap.git` at `1195f539afe5a1018be07d2e1865824c225ee407`. Dashboard dependency: `https://git.vanillacore.net/govstack-apps/govstack-dashboard.git` at `f2e6ff3a0b752a0708983407e1176d72faeae702`. These pins identify operational source, not proof of a live deployment or unrestricted access. No live deployment is authorized during package construction. Final kit SOURCE/notices/checksums and native tests are required before release.

At the bootstrap pin, teardown omits `workload-argocd` from its application allowlist and requires destinations that omit generated `argocd`/tenant entries. Retirement is blocked unless a repaired reviewed source is explicitly selected and tested; do not claim cleanup or weaken ownership checks.

## Known source tensions

- Chapter 1 says that the plugin contains six skills. This package revision adds a cross-chapter guide and two practitioner skills, so that count is historical until the chapter text is updated.
- Chapter 4's scope record says Chapter 5 adds GitOps, while the reviewed Chapter 4 manuscript and lab already include a bounded Argo CD exercise for cluster declarations and one demonstration workload. This package follows the executable Chapter 4 material for that bounded exercise. It reserves broader platform delivery, access, observability, recovery and multi-team operation for Chapter 5.

Do not silently resolve future chapter contradictions. Name the conflicting files or revisions, state the interpretation used for the current answer, and keep the affected claim conditional until the source is aligned.
