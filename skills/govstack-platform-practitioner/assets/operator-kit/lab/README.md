# Chapter 5 lab: build and use the platform

This companion follows Management and its gateway, the LoadBalancer cluster, then `information-mediator` and `example-workloads`. Chapter 6 installs the actual Information Mediator and example applications. Here we use small response-marker workloads to learn the platform path.

**Current package status: review candidate.** Local preparation, the real upstream renderer/lifecycle interface and the local HTTPS probe are executable and tested. A complete live build and retirement are not validated. At the reviewed Bootstrap revision, child credential preparation is coupled to the transitional direct rollout, and the teardown contract does not cover the current foundation destinations. The helper refuses both operations before a process starts. Do not use the old rollout path or remove finalizers to get past those stops. A reviewed source/kit revision and new tests are required before those parts can be released.

## Start locally

Use an owner-controlled directory outside the repository and installed skill. The following creates only synthetic offline inputs and rendered files. `.test` domains, fixture IDs, flavors and image metadata are deliberately not cloud facts.

```bash
export LAB="$(pwd)/chapter-5/lab"  # when starting at the content repository root
export WORK="$HOME/.local/state/chapter5-practice"
export BOOTSTRAP_REPO="/absolute/path/to/reviewed/govstack-bootstrap"
umask 077
mkdir -p "$WORK"
python3 -m venv "$WORK/venv"
"$WORK/venv/bin/pip" install -r "$LAB/requirements.txt"
export PYTHON="$WORK/venv/bin/python"
export CASE="$WORK/case.json"
"$PYTHON" "$LAB/scripts/prepare_example.py" \
  --bootstrap-repo "$BOOTSTRAP_REPO" --work-dir "$WORK/inputs"
"$PYTHON" "$LAB/scripts/platform.py" init --inputs "$WORK/inputs/inputs.json" --case "$CASE"
"$PYTHON" "$LAB/scripts/platform.py" doctor --case "$CASE" --offline
"$PYTHON" "$LAB/scripts/platform.py" render --case "$CASE" --target all
"$PYTHON" "$LAB/scripts/platform.py" route --case "$CASE"
"$PYTHON" "$LAB/scripts/platform.py" handoff --case "$CASE"
```

Use a fresh empty inputs directory and new output directory for another render. The helper does not silently overwrite either existing lifecycle state or handoff evidence. `route` needs Helm, but does not apply anything. `handoff` without `--live` exports preparation evidence, not a running platform.

The supported host is a Linux or compatible POSIX operator environment with Python 3, Git, Helm and curl. The live Bootstrap path additionally needs Ansible, OpenTofu, the OpenStack client, kubectl and the pinned Bootstrap dependencies described in that repository. Inspect actual help before adding arguments:

```bash
"$PYTHON" "$LAB/scripts/platform.py" --help
CH5_BOOTSTRAP_REPO="$BOOTSTRAP_REPO" "$PYTHON" -m unittest discover -s "$LAB/tests" -v
```

The tests use synthetic inputs and real local programs. They do not establish cloud quota, networking, a deployed cluster or end-to-end readiness.

## Reviewed source

Bootstrap is pinned to `1195f539afe5a1018be07d2e1865824c225ee407`. Clone it using your authorized repository access, fetch that full commit, then detach at the pin. No token belongs in a command, repository URL or session file. The helper rejects another revision or tracked source modifications. Dashboard behavior was inspected at `f2e6ff3a0b752a0708983407e1176d72faeae702`.

`prepare_example.py` uses the upstream fixture's foundation settings, labels its generated cloud/image data synthetic, keeps `mode=example` and contacts no endpoint. Its one-node counts are test inputs, not production sizing. The optional real probe image is `docker.io/hashicorp/http-echo@sha256:fcb75f691c8b0414d670ae570240cbf95502cc18a9ba57e982ecac589760a186`; its HTTP-echo executable and flags were exercised locally on Linux/amd64. No Kubernetes deployment of that image is claimed.

## Walkthroughs

1. [Prepare](walkthroughs/01-preparation.md): discover cloud facts and create a protected JSON session.
2. [Management](walkthroughs/02-management.md): initial infrastructure, gateway, seed and controllers in dependency order.
3. [LoadBalancer](walkthroughs/03-loadbalancer.md): prepare its credentials and declaration before either workload Spoke.
4. [Two Spokes](walkthroughs/04-two-spokes.md): keep distinct identities, addresses and delivery destinations.
5. [Routing](walkthroughs/05-routing.md): local Envoys and TLS, then the shared edge route.
6. [Use](walkthroughs/06-use.md): team GitOps, response revision, PVC and private Dashboard views.
7. [Maintain](walkthroughs/07-maintenance.md): scale, replace and upgrade through the existing owner.
8. [Cleanup](walkthroughs/08-cleanup.md): data/retention decision and the blocked retirement boundary.

The manual and agent-assisted routes use this same kit. Copy it into a protected working directory before agent execution; installation alone does not authorize changes. The session is JSON (`platform-session/v1`); the CLI's limited handoff is an intermediate artifact, separate from the skill's validated `platform_runtime_record/v1`.
