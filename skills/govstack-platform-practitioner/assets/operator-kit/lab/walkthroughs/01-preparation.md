# 01: Prepare the environment

We begin with an existing OpenStack project. We need facts about that project before choosing machine sizes or address ranges. An operator's cloud profile is not evidence that the project has enough quota, or that the controller uses the same identity.

## Discover the local boundary

Keep credentials in the approved local cloud configuration or credential store, never in `inputs.json`. Set the profile and region to values supplied by your administrator, then inspect them:

```bash
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" token issue -f json
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" quota show "$PROJECT_ID" -f json
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" flavor list -f json
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" image list --status active -f json
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" network list -f json
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" subnet list -f json
```

The token response is sensitive. Inspect it privately; do not save it with learning evidence or record it on screen. Record only the verified project/region and selected resource IDs. Check router/external-network connectivity, quota already consumed and capacity for replacement as well as initial machines. Do not add the quotas from different projects or regions.

Compare the new private network, gateway/VPN, each cluster's Pod and Service CIDRs, API VIPs and service-address pools. Addresses must belong to the selected network and must not collide with existing leases or API/node addresses. Different cluster names do not prevent an IP conflict.

## Create the session

Follow the [lab README](../README.md) to prepare an offline example. Read the resulting `inputs.json`, environment YAML and three cluster inputs before running `init`. `case.json` stores paths, role names, context/server identity and domains. It stores no credential values.

For a later authorized live run, create a separate reviewed JSON input, replacing every synthetic value with discovered facts. Use the actual environment config and inventory, infrastructure outputs and built-image metadata. Supply `management_server` and the exact management context, both domains, certificate trust, the private Envoy addresses and a compatible digest-pinned probe image. Do not turn the fixture live by changing only `mode`.

```bash
"$PYTHON" "$LAB/scripts/platform.py" init --inputs "$LIVE_INPUTS" --case "$LIVE_CASE"
"$PYTHON" "$LAB/scripts/platform.py" doctor --case "$LIVE_CASE" --offline
```

`doctor` checks local input/source contracts. Its `offline-only` result does not validate quota, credentials or connectivity. Missing infrastructure/image artifacts before bootstrap are expected to remain explicit; after bootstrap they must be replaced with real outputs before child rendering.

## Ready for the next step

We have a protected session, reviewed environment/inventory and a sizing/address decision supported by read-only discovery. We also have an approved retention/recovery plan. The current child-bootstrap and retirement blockers remain release dependencies, so this package's default exercise continues locally, without provisioning a cloud.

## Read-only upstream preflight

The helper's `doctor` is local only. The pinned repository also supplies `playbooks/01-preflight-readonly.yml`, which contacts the approved controller/cloud and checks authentication, services, flavors, images, networks and compute quota. It is not a `bootstrap --stage` choice. It does not check all volume/network/load-balancer quotas or establish actual spare compute capacity.

Prepare an isolated directory containing only the three selected cluster declarations:

```bash
"$PYTHON" "$LAB/scripts/prepare_preflight.py" --case "$LIVE_CASE" \
  --output-dir "$WORK/preflight-clusters"
```

This makes local copies and prints the actual Ansible argv with your session's inventory, environment and `preflight_clusters_dir`. Review that selection, the source pin, controller identity and read-only permission before running the displayed upstream command. The source verifies its expected integration-test host. Do not run it against the default source directory and accidentally omit external declarations or include unrelated clusters. An example session may prepare the files, but its synthetic controller/inventory is not an executable live target.

## Negative local check

A valid example is intentionally accepted for offline initialization and doctor. For a real reproducible refusal, create a separate JSON input with `management_context` removed and run `init` against a new scratch case path. Expect exit 2 with `management_context is required` and no case file. Do not use an untouched valid example as a negative test or change it to live mode. The lab suite exercises the same rejection before any source/cloud operation.
