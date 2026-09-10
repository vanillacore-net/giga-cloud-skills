# 02: Security policy and persistent storage in Horizon

**Starting state:** Walkthrough 01 is accepted, Horizon is open in the approved project and the selected values match `environment-contract.yaml`.

**End state:** Security group `web-https` contains the intended HTTPS ingress rule and volume `web-01-data` is `Available`.

**Companion video:** [C3-P2](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/VIDEO_SCOPES.md#user-content-c3-p2-create-security-policy-and-storage-in-horizon)

## Create the security group

1. Open **Project -> Network -> Security Groups**.
2. Select **Create Security Group**.
3. Enter `web-https` as **Name**.
4. Enter `Allow HTTPS from the documentation client range` as **Description**.
5. Select **Create Security Group**.

The [reference form](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/graphics/horizon/horizon-security-group-create-live.png) shows those values. In the new group's actions, select **Manage Rules**, then **Add Rule**:

- **Rule:** `Custom TCP Rule`
- **Direction:** `Ingress`
- **Open Port:** `Port`
- **Port:** `443`
- **Remote:** `CIDR`
- **CIDR:** the `approved_https_cidr` value from `environment-contract.yaml`. The reference lab uses `198.51.100.0/24`.

Select **Add**. Confirm in the [rule list](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/graphics/horizon/horizon-security-group-rules-live.png) that the result is IPv4, TCP, ingress, port 443 and the stated CIDR. This Horizon version derives IPv4 from the CIDR. The default IPv4 and IPv6 egress rules may remain because they govern traffic leaving the port.[1]

## Create the data volume

1. Open **Project -> Volumes -> Volumes**.
2. Select **Create Volume**.
3. Enter `web-01-data` as **Volume Name**.
4. Leave **Volume Source** at `No source, empty volume`.
5. Select the volume type from the environment contract. The reference lab uses `__DEFAULT__`.
6. Enter `1` GiB as **Size**.
7. Select the Cinder availability zone from the environment contract. It is `nova` in the reference lab.
8. Select **Create Volume**.

The [reference volume form](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/graphics/horizon/horizon-volume-create-live.png) shows the complete request. Allow up to two minutes for status **Available**. If Horizon reports **Error**, or the volume remains in an intermediate state after the local timeout, open its details and messages and stop.

## Check the result

Open the security-group rule list and volume details again. Record the security-group ID and volume ID from the detail URLs or equivalent detail fields if the deployment exposes them. Do not record credentials or internal endpoints.

**Stop when:** the rule differs from the approved client range, the group contains unintended ingress, or the volume does not reach **Available** within the local timeout.

**Evidence for the next step:** exact rule fields, volume name, size, type, Cinder availability zone, `Available` status and stable IDs where Horizon exposes them.

[1] [OpenStackClient security-group rule reference](https://docs.openstack.org/python-openstackclient/latest/cli/command-objects/security-group-rule.html)
