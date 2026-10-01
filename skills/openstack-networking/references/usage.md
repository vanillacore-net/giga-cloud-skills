# OpenStack networking: build and verify tenant connectivity

Use existing Neutron services for tenant networks, subnets, routers, ports,
security groups, and floating IPs. This is not control-plane or host networking.
Linux/macOS CLI and Windows WSL share the procedure. The toolkit CLI syntax
baseline is python-openstackclient 8.2.0; extensions and policy remain cloud-specific.

## Start with a connectivity matrix

Ask which source must reach which destination, protocol, port, and access path.
Teach network/subnet/router/floating-IP distinctions only as they affect that goal.
A fixed address is not a floating IP; a router is not automatically a VPN endpoint.
For work mode, deliver the approved topology, resource IDs, and connectivity checks.
For challenge/review mode, test assumptions about ingress, routing, and isolation.
Do not require public exposure when private connectivity satisfies the task.

## Before: scope, address plan, and ownership

1. Read local `references/operations-api.md` for supported actions and exact fields.
   Reuse the corroborated `openstack-context/v1` case/project/region/profile and
   timeout. Keep detailed evidence in the protected coordinator work directory.
2. Obtain caller-selected existing network, router, external network, and port UUIDs
   as needed. Resolve names explicitly; do not select the first external network.
3. For a new subnet, choose a CIDR that does not overlap peer, VPN, or routed ranges.
   Example documentation range `192.0.2.0/24` is illustrative, not a deployment default.
   Choose IP version, gateway, DHCP, DNS resolvers, and allocation pool deliberately;
   reserve infrastructure addresses and confirm guest requirements.
4. Confirm permitted external connectivity, floating-IP quota/budget, and availability
   of router gateway operations. Do not infer write permission from a successful list.
5. Corroborate ownership of existing networks, ports, routers, and security groups
   through controller/state records and metadata. A caller-supplied owner alone is
   insufficient. Unknown owner blocks mutation; managed objects go to their owner.
6. Record baseline interfaces, gateway, routes, attached ports, and existing rules.
   For shared dependencies, identify impact beyond the two target VMs.

Use scoped read examples without requiring global list/catalog permissions:

```sh
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" network show "$NETWORK_ID" -f json
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" subnet show "$SUBNET_ID" -f json
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" router show "$ROUTER_ID" -f json
openstack --os-cloud "$CLOUD" --os-region-name "$REGION" port show "$PORT_ID" -f json
```

If listing is denied but a supplied UUID can be shown, continue within that scope.
Record 403 per action; request narrow help for unavailable dependencies rather
than changing identities, disabling TLS, or declaring the cloud wholly read-only.

## Change example: one subnet, one router, two VMs, one floating IP

Agree these parameters before preparing a change:
- One tenant network and subnet with approved non-overlapping addresses and DNS.
- One router, its internal subnet interface, and caller-selected external gateway.
- Compute creates two VMs on the verified network using automatically created ports;
  capture and verify both port UUIDs and subnet/fixed addresses afterward.
  Precreated-port attachment and standalone port creation are unsupported by the
  helper; if required, stop and hand off to the authorized owner workflow.
- Exactly one floating IP associated with the selected first VM port/fixed address.
  The second VM remains private; do not allocate a second IP for symmetry.
- SSH admitted only from the approved VPN client CIDR, not `0.0.0.0/0` or `::/0`.
  Apply the same restriction to IPv6 if used; inspect inherited/default rules too.
- Any workload-facing public service must have a separately agreed protocol/port
  and source scope; a floating IP does not justify opening SSH to the Internet.

Clarify “VPN-only SSH”: prefer the routed private VPN path for both VMs.
If the operator means SSH to the floating IP from a VPN egress address instead,
record that distinction and allow only its approved source CIDR, not an assumed one.
Verify VPN return routes, source NAT behavior, and guest SSH/firewall requirements.
Do not deploy VPNaaS implicitly: an existing approved VPN/bastion can provide access.

Prepare dependencies in order: network, subnet, router/interface/gateway, security
rules, then compute with automatically created ports, capture and verify those ports,
then floating-IP association with the selected port. Do not prepare port-create
requests or precreated-port VM attachment; hand those requirements to the owner.
Use separate supported plans where the contract cannot express the entire topology.
Record UUIDs as each stage succeeds, and re-inspect dependencies before the next.
Partial success is real state; never restart the whole workflow blindly.

```sh
WORK="$WORK_DIR"
cd "$WORK"
OPS="$WORK/scripts/openstack_ops.py"
python3 "$OPS" inspect --context "$WORK/context.json" --domain "$DOMAIN" --evidence "$WORK/network-before.json"
python3 "$OPS" prepare --context "$WORK/context.json" --request "$WORK/request.json" --plan "$WORK/network-plan.json"
python3 "$OPS" execute --plan "$WORK/network-plan.json" --approve "$APPROVAL_SHA256" --evidence "$WORK/network-after.json"
```

Select `DOMAIN` and request/action keys from `references/operations-api.md` only.
Review scope, ownership, target UUIDs, ingress changes, cost, and recovery impact.
Approve the exact generated SHA256; changed state or parameters require a new plan.
Do not replace unsupported operations with an unapproved raw CLI mutation.

## After: topology evidence and traffic evidence are different

Show subnet CIDR/DHCP/DNS, router interface/gateway, both VM port UUIDs/fixed IPs,
security-group rules, and the single floating-IP association in protected evidence.
Check both VMs obtain the intended addressing and required DNS/service reachability.
From the approved VPN path, test SSH on both VMs without printing private keys.
Use an authorized negative check for non-VPN SSH; do not scan unrelated addresses.
An API object state proves configuration, not packet flow or tenant isolation.
When guest/VPN testing is unavailable, mark it pending with the responsible owner.
For a private-only alternative, omit external gateway/FIP if unnecessary; retain
network, subnet, port, and approved private-path verification.

## Failure and safe recovery

- No external network permission/service: offer private-only networking, or have
  the operator supply an authorized external UUID. Do not assume “public” exists.
- No router-create permission: use a caller-selected existing router only if owner
  and allowed attachment are corroborated; otherwise hand off that dependency.
- Port down: inspect binding/attachment evidence available to the tenant; correlate
  compute state before suggesting a new network or detaching a live server port.
- SSH timeout: check VPN routes, effective source, SGs, guest firewall/listener,
  then return path. A ping failure alone does not identify which layer is broken.
- FIP association failure: reconcile existing association and fixed address first;
  do not allocate duplicates after a timeout or overwrite another VM's association.
- Cleanup: separately approve owned dependencies in reverse order; never delete
  a shared router/network merely because it appeared in this case's evidence.

## Official documentation

- OpenStackClient Network v2 Commands: https://docs.openstack.org/python-openstackclient/latest/cli/command-objects/network/v2/index.html
- Neutron Introduction to Networking: https://docs.openstack.org/neutron/latest/admin/intro-os-networking.html
- Neutron Security Groups: https://docs.openstack.org/neutron/latest/admin/intro-os-networking.html#security-groups
