# 03: Compute and networking in Horizon

**Starting state:** Walkthrough 02 completed successfully. The approved image, flavor, network, Nova availability zone, security group and volume exist or are selectable.

**End state:** `web-01` is `Active`, `web-01-data` is attached, and the allocated floating IP maps to the VM's Neutron port.

**Companion video:** [C3-P3](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/VIDEO_SCOPES.md#user-content-c3-p3-launch-and-connect-the-vm-in-horizon)

## Launch the VM

Open **Project -> Compute -> Instances**, select **Launch Instance**, then complete the wizard:

1. **Details:** enter `web-01`, choose the Nova availability zone from the contract and keep **Count** at `1`.
2. **Source:** choose **Image**, move the approved image from **Available** to **Allocated**, and set **Create New Volume** to **No**.
3. **Flavor:** move the approved flavor to **Allocated**.
4. **Networks:** move the approved project network to **Allocated**.
5. **Security Groups:** move `web-https` to **Allocated**. Remove `default` from **Allocated** if Horizon selected it automatically.
6. Select **Launch Instance**.

The genuine reference forms are available for [Details](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/graphics/horizon/horizon-launch-details-live.png), [Source](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/graphics/horizon/horizon-launch-source-live.png), [Flavor](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/graphics/horizon/horizon-launch-flavor-live.png), [Networks](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/graphics/horizon/horizon-launch-network-live.png) and [Security Groups](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/graphics/horizon/horizon-launch-security-group-live.png). These images show reference-lab values, not portable defaults.

Allow up to three minutes for **Active** and **Running**. Stop on **Error** or timeout, then inspect the instance fault and action log before retrying.

## Attach the volume

1. Open **Project -> Volumes -> Volumes**.
2. For `web-01-data`, select **Manage Attachments**.
3. Select `web-01` and confirm.
4. Allow up to two minutes for **In-use** and an **Attached To** value naming `web-01`.

The [reference result](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/graphics/horizon/horizon-volume-attached-live.png) proves the intended attachment in the test environment. Stop on **Error** or timeout.

## Allocate and associate a floating IP

1. Open **Project -> Network -> Floating IPs**.
2. If no unassociated address exists, select **Allocate IP To Project**, choose the approved external pool and confirm. Record the returned address.
3. Return to **Project -> Compute -> Instances**.
4. For `web-01`, select **Associate Floating IP**.
5. Select the recorded address and the `web-01` port or its fixed address.
6. Select **Associate**.
7. Return to **Project -> Network -> Floating IPs** and confirm that the address maps to the intended port with status **Active**.

The [reference result](https://git.vanillacore.net/giga/content/src/commit/65055f17aaf13cf1944e2f4c4e1180dd3b94478a/chapter-3/graphics/horizon/horizon-floating-ip-result-live.png) shows `172.16.2.170` mapped to the reference VM port at `192.168.0.123`. Another cloud will allocate different addresses.

## Record evidence

Open **Project -> Network -> Ports**, locate the port by its device or fixed address and inspect its details. Record the server, port, security-group, floating-IP and volume identifiers where available. Walkthrough 06 uses OpenStackClient for the final cross-service read-back because dashboard status alone cannot compare every stable identifier.

**Stop when:** any selected item is only available rather than allocated, the VM or volume reaches an error state, the floating IP remains unbound, or the port does not carry `web-https`.

**Evidence for the next step:** active server, one intended VM port, intended security group, active floating-IP mapping and attached data volume.
