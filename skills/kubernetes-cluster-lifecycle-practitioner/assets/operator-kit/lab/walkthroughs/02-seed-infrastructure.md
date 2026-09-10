# 2. Seed infrastructure

Video companion: [C4-P2](https://git.vanillacore.net/giga/content/src/commit/b56cad92b74b4335de99879415d437b97ab677cd/chapter-4/VIDEO_SCOPES.md#c4-p2-seed-infrastructure-review-and-apply-the-opentofu-plan)

## Purpose

The seed cannot appear from an unexplained prerequisite. OpenTofu creates its private network placement, stable port and protected administration path as one reviewable change. Ansible owns the guest configuration in the next step.

```bash
: "${GIGA_OPERATOR_KIT:=$PWD}"
cd "$GIGA_OPERATOR_KIT"
set -euo pipefail
test -r lab-session.env
. ./lab-session.env
cd foundation/opentofu/bootstrap
test -r "$OS_CLIENT_CONFIG_FILE"

# Create the ignored local input file and replace every discovery placeholder.
cp terraform.tfvars.example terraform.tfvars

# Format and validate the declarations before contacting OpenStack.
tofu fmt -check
tofu init
tofu validate

# Save the proposed infrastructure change. A saved plan prevents the applied
# change from drifting away from the reviewed image, flavor, address and rules.
tofu plan -out=seed.tfplan

# Inspect every create, replace and destroy action. Reject unexpected public
# exposure, unrestricted SSH, a missing Nova AZ or an unapproved image UUID.
tofu show seed.tfplan

# Apply exactly the reviewed plan.
tofu apply seed.tfplan

# Record stable outputs for inventory and later absence checks.
mkdir -p ../../../artifacts
tofu output -json > ../../../artifacts/seed-outputs.json
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
OpenTofu has been successfully initialized!
Success! The configuration is valid.
Plan: <n> to add, 0 to change, 0 to destroy.
Apply complete! Resources: <n> added, 0 changed, 0 destroyed.
```

The saved JSON has this general form; the values come from the current OpenStack project:

```json
{
  "seed_private_ip": {"sensitive": false, "type": "string", "value": "<seed-private-ip>"},
  "seed_server_id": {"sensitive": false, "type": "string", "value": "<seed-server-uuid>"},
  "gateway_security_group_id": {"sensitive": false, "type": "string", "value": "<security-group-uuid>"}
}
```

The reference lab requires a jump host because the operator is assumed to have no direct private access to the management network. The module gives that host the only floating IP; the seed has a fixed private address and no direct public API. The OpenStack router provides outbound access for package and image downloads, while ingress remains constrained by security groups. A site with an approved VPN or direct private access can remove the jump host, but must adapt the module, inventory and kubeconfig-copy procedure together.

Use those outputs for two separate checks. The seed server ID and private IP must match an `ACTIVE` Nova server and its attached Neutron port. Separately, the gateway security-group ID must identify an SSH ingress rule limited to the reviewed administration-source CIDR. The second check applies only to this reference topology, because environments with direct private access can omit the jump host.

```bash
# Compare the declared seed ID with Nova and its attached Neutron port.
SEED_ID=$(tofu output -raw seed_server_id)
SEED_PRIVATE_IP=$(tofu output -raw seed_private_ip)
GATEWAY_SECURITY_GROUP_ID=$(tofu output -raw gateway_security_group_id)
openstack --os-cloud "$OS_CLOUD" server show "$SEED_ID" -f json
openstack --os-cloud "$OS_CLOUD" port list --server "$SEED_ID" \
  --fixed-ip "ip-address=$SEED_PRIVATE_IP" -f json
openstack --os-cloud "$OS_CLOUD" security group rule list "$GATEWAY_SECURITY_GROUP_ID" -f json
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
{"id":"<seed-server-uuid>","status":"ACTIVE"}
[{"id":"<port-uuid>","fixed_ips":["10.42.0.20"]}]
[{"protocol":"tcp","port_range_min":22,"remote_ip_prefix":"<admin-cidr>"}]
```

## Evidence gate

We continue when the seed server is ACTIVE on the intended fixed port, the gateway security-group rules restrict SSH to the reviewed administration source CIDR, and the state and saved outputs are protected. This inspection proves the configured rule boundary, not reachability from every possible source. OpenTofu success does not prove that Kubernetes prerequisites exist inside the VM.
