# 1. Discovery

Video companion: [C4-P1](https://git.vanillacore.net/giga/content/src/commit/b56cad92b74b4335de99879415d437b97ab677cd/chapter-4/VIDEO_SCOPES.md#c4-p1-discovery-turn-cloud-facts-into-an-environment-contract)

## Purpose

CAPI repeats whatever inputs it receives. Discovery prevents a reusable declaration from repeating the wrong project, image, flavor, availability zone or network design. It also creates one reviewable contract for the later OpenTofu, Ansible and CAPI stages.

Start in `chapter-4/lab`. Copy the example instead of editing it, because the resulting file contains site-specific identifiers and is ignored by Git.

```bash
# Enter the lab so every later relative path resolves to a checked-in file.
: "${GIGA_OPERATOR_KIT:=$PWD}"
cd "$GIGA_OPERATOR_KIT"
set -euo pipefail
test -r lab-session.env
. ./lab-session.env

# Select the reviewed clouds.yaml profile without printing its credentials.
test -r "$OS_CLIENT_CONFIG_FILE"

# Confirm the project identity. Selecting only project_id avoids printing a token.
openstack --os-cloud "$OS_CLOUD" token issue -f value -c project_id

# Inspect limits and current use. Quota headroom permits requests, but does not
# prove that the compute hosts have physical capacity at the requested time.
openstack --os-cloud "$OS_CLOUD" quota show -f yaml
openstack --os-cloud "$OS_CLOUD" usage show -f yaml

# Separate the general seed image from the Kubernetes-ready CAPI image.
# Names are labels, so record the unique UUID and current metadata.
openstack --os-cloud "$OS_CLOUD" image list --status active
openstack --os-cloud "$OS_CLOUD" image show REPLACE_WITH_IMAGE_UUID -f json

# Control-plane and worker Machines have different jobs. Inspect both selected
# flavors instead of assuming that one size is suitable for every machine group.
openstack --os-cloud "$OS_CLOUD" flavor show REPLACE_WITH_CONTROL_PLANE_FLAVOR -f json
openstack --os-cloud "$OS_CLOUD" flavor show REPLACE_WITH_WORKER_FLAVOR -f json

# Record the Nova fault-domain name used by every machine group.
openstack --os-cloud "$OS_CLOUD" availability zone list --compute

# Read the complete network relationship before choosing IDs and CIDRs.
openstack --os-cloud "$OS_CLOUD" network list
openstack --os-cloud "$OS_CLOUD" subnet list
openstack --os-cloud "$OS_CLOUD" router list
openstack --os-cloud "$OS_CLOUD" security group list
```

The read-back should expose unique IDs and state. This shortened shape uses angle brackets for environment-specific values; it is not evidence from an unapproved cloud:



Representative success output (shortened; values in angle brackets are environment-specific):

```text
$ openstack --os-cloud "$OS_CLOUD" image list --status active
+--------------+-----------------------------+--------+
| ID           | Name                        | Status |
+--------------+-----------------------------+--------+
| <image-uuid> | <approved-kubernetes-image> | active |
+--------------+-----------------------------+--------+

$ openstack --os-cloud "$OS_CLOUD" availability zone list --compute
+-----------+-------------+
| Zone Name | Zone Status |
+-----------+-------------+
| <nova-az> | available   |
+-----------+-------------+

$ openstack --os-cloud "$OS_CLOUD" network list
+----------------+---------------------------+--------+
| ID             | Name                      | Status |
+----------------+---------------------------+--------+
| <network-uuid> | <private-cluster-network> | ACTIVE |
+----------------+---------------------------+--------+
```

Copy `environment-contract.example.yaml` to `environment-contract.yaml`, replace every `REPLACE_` value, and record the exact IDs selected above. One completed child entry has this structure:

```yaml
openstack:
  image_id: <approved-kubernetes-image-uuid>
  control_plane_flavor: <control-plane-flavor-name-or-id>
  worker_flavor: <worker-flavor-name-or-id>
  availability_zone: <nova-availability-zone>
clusters:
  - name: service-a
    network_id: <private-network-uuid>
    subnet_id: <private-subnet-uuid>
    node_cidr: 10.41.0.0/24
    pod_cidr: 10.241.0.0/16
    service_cidr: 10.97.0.0/16
    api_vip: 10.41.0.10
```

The example uses these non-overlapping private ranges:

- management Nodes: `10.42.0.0/24`
- management Pods: `10.242.0.0/16`
- management Services: `10.98.0.0/16`
- edge and workload Node, Pod and Service ranges: the separate values already shown in the example contract

`172.0.0.0/16` is not an RFC 1918 private range and must not be used as a generic private example.

```bash
# Validate syntax, required IDs, ownership labels and CIDR non-overlap locally.
python3 scripts/preflight.py environment-contract.yaml

# Query the selected cloud without creating resources. The script explains what
# it checked and leaves quota sufficiency as an explicit operator decision.
./scripts/preflight-readonly.sh environment-contract.yaml "$OS_CLOUD"
```

A valid local contract ends with:



Representative success output (shortened; values in angle brackets are environment-specific):

```text
environment contract valid (live mode): loadbalancer, service-a; CIDRs do not overlap
```

The read-only cloud preflight then prints each selected image, flavor, availability zone, network, subnet and security group before ending with `read-only preflight completed; quota sufficiency still requires operator review`. Compare those values with the contract. Do not treat the final line as approval when an earlier read-back differs.

## Evidence gate

We continue only when the project ID, image UUIDs, flavor IDs, Nova availability zone, network and subnet IDs, security-group policy, API addresses and every CIDR are explicit. A successful command is not approval by itself.
