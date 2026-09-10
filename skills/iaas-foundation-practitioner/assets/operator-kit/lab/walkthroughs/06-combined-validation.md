# 06: Prove the cross-service resource chain

**Starting state:** One creation path has completed. `evidence/resource-ids.json` contains the cloud profile and stable IDs. For Horizon, use OpenStackClient to resolve and save the IDs before continuing.

**End state:** Nova, Neutron and Cinder records agree on the server, port, security group, floating IP and volume attachment.

**Companion video:** [C3-P6](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/VIDEO_SCOPES.md#user-content-c3-p6-prove-the-cross-service-resource-chain)

## Capture IDs after the Horizon path

If Horizon created the resources, use the approved profile:

```bash
set -euo pipefail
CLOUD=my-cloud
SERVER_ID=$(openstack --os-cloud "$CLOUD" server show web-01 -f value -c id)
PORT_IDS=$(openstack --os-cloud "$CLOUD" port list --server "$SERVER_ID" -f value -c ID)
set -- $PORT_IDS
[ "$#" -eq 1 ] || exit 1
PORT_ID=$1
SECURITY_GROUP_ID=$(openstack --os-cloud "$CLOUD" security group show web-https -f value -c id)
FIP_IDS=$(openstack --os-cloud "$CLOUD" floating ip list --port "$PORT_ID" -f value -c ID)
set -- $FIP_IDS
[ "$#" -eq 1 ] || exit 1
FIP_ID=$1
VOLUME_ID=$(openstack --os-cloud "$CLOUD" volume show web-01-data -f value -c id)
```

Save those values using the JSON command in Walkthrough 04.

## Run the stable-ID validator

```bash
python3 - <<'PY'
import json
v=json.load(open('evidence/resource-ids.json'))
required={'cloud','server_id','port_id','security_group_id','floating_ip_id','volume_id'}
missing=required-set(v)
if missing or any(not str(v[k]).strip() for k in required):
    raise SystemExit(f'invalid evidence file, missing={sorted(missing)}')
print('evidence file contains all required identifiers')
PY

./scripts/verify-resource-chain.sh \
  "$(python3 -c 'import json; print(json.load(open("evidence/resource-ids.json"))["cloud"])')" \
  "$(python3 -c 'import json; print(json.load(open("evidence/resource-ids.json"))["server_id"])')" \
  "$(python3 -c 'import json; print(json.load(open("evidence/resource-ids.json"))["port_id"])')" \
  "$(python3 -c 'import json; print(json.load(open("evidence/resource-ids.json"))["security_group_id"])')" \
  "$(python3 -c 'import json; print(json.load(open("evidence/resource-ids.json"))["floating_ip_id"])')" \
  "$(python3 -c 'import json; print(json.load(open("evidence/resource-ids.json"))["volume_id"])')"
```

The helper checks exact ID relationships and rejects zero or multiple ports. It requires the server to be `ACTIVE`, the port and floating IP to be `ACTIVE`, the expected security group on the port, and an `in-use` volume attachment referencing the same server.

## Acceptance boundary

This evidence proves the IaaS resource chain. It does not prove guest login, filesystem formatting, application readiness, DNS, TLS or client reachability. Those require the access input and workload procedure handed to the next layer.

**Stop when:** an API query fails, cardinality is not exactly one, IDs disagree, or a resource is not in its expected state.

**Evidence for cleanup:** preserve `evidence/resource-ids.json` until every deletion or retention decision has been verified.
