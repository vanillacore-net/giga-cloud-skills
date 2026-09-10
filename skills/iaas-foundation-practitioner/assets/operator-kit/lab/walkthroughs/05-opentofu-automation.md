# 05: Review and apply the OpenTofu declaration

**Starting state:** Walkthrough 01 is accepted. No same-named resources from another path exist. The build host has OpenTofu and access to the protected cloud profile.

**End state:** A reviewed saved plan has been applied, and stable output IDs are stored for independent validation.

**Companion video:** [C3-P5](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/VIDEO_SCOPES.md#user-content-c3-p5-review-and-apply-the-opentofu-declaration)

## Define the local inputs

From `$GIGA_OPERATOR_KIT/opentofu`:

```bash
set -euo pipefail
umask 077
cp terraform.tfvars.example terraform.tfvars
```

Replace the profile, image ID, flavor, networks, client CIDR, volume type and the separate Nova and Cinder availability-zone values with those approved in `../environment-contract.yaml`. Never copy credentials into the variable file.

## Validate and plan

```bash
tofu init
tofu fmt -check
tofu validate
tofu plan -out web-01.tfplan
```

Read the plan as a change request. Confirm that it contains one VM, one security group and ingress rule, one data volume and attachment, one floating IP and one association. Confirm image ID, flavor, network, both availability zones, source CIDR and names. Stop on an unexpected replacement, deletion or provider target.

The reference recipe currently plans seven managed resources. Data sources are lookups and are not counted as managed resources. The exact provider selection is pinned in `.terraform.lock.hcl`.

## Apply the reviewed plan

```bash
tofu apply web-01.tfplan
```

Do not regenerate the plan between review and apply. Capture the outputs:

```bash
mkdir -p ../evidence
python3 - <<'PY'
import json, pathlib, subprocess
outputs = {
    'cloud': 'openstack_cloud',
    'server_id': 'server_id',
    'port_id': 'port_id',
    'security_group_id': 'security_group_id',
    'floating_ip_id': 'floating_ip_id',
    'volume_id': 'volume_id',
}
data = {
    key: subprocess.check_output(['tofu', 'output', '-raw', output], text=True).strip()
    for key, output in outputs.items()
}
empty = [key for key, value in data.items() if not value]
if empty:
    raise SystemExit(f'empty OpenTofu outputs: {empty}')
pathlib.Path('../evidence/resource-ids.json').write_text(json.dumps(data, indent=2) + '\n')
PY
```

## Interpret the evidence

A successful apply means the provider accepted the planned operations. It does not prove that a service is reachable, that the floating IP has an approved route or that storage is usable inside the guest. Continue to Walkthrough 06 for API read-back across Nova, Neutron and Cinder.

State is ignored because it can contain sensitive values. Team operation requires a protected remote backend with locking, encryption and access control. Git preserves the declaration and review history, not live state.

**Stop when:** formatting or validation fails, the plan differs from the approved request, apply fails or an expected output is empty.

**Evidence for the next step:** reviewed plan decision, successful apply and `../evidence/resource-ids.json` generated from OpenTofu outputs.
