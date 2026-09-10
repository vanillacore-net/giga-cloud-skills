# Chapter 3 learning environment

This lab carries the complete practical path behind Chapter 3. We create one OpenStack IaaS request through three alternative interfaces, inspect the resulting service states and remove the disposable resources safely.

The reference request contains `web-01`, security group `web-https`, one 1 GiB Cinder volume and one floating IP. It does not install a web service. The lab proves the IaaS resource chain only.

## Choose one creation path

Walkthrough 01 is shared discovery. Walkthroughs 02 and 03 form the Horizon path. Walkthrough 04 is the OpenStackClient alternative. Walkthrough 05 is the OpenTofu alternative. Run only one creation path in a clean project unless you deliberately choose distinct resource names.

1. [Discovery and environment contract](walkthroughs/01-discovery.md)
2. [Horizon security policy and storage](walkthroughs/02-horizon-security-storage.md)
3. [Horizon compute and networking](walkthroughs/03-horizon-compute-networking.md)
4. [OpenStackClient provisioning](walkthroughs/04-cli-provisioning.md)
5. [OpenTofu automation](walkthroughs/05-opentofu-automation.md)
6. [Combined validation](walkthroughs/06-combined-validation.md)
7. [Cleanup and absence proof](walkthroughs/07-cleanup.md)

Use the paths as follows:

```text
01 -> 02 -> 03 -> 06 -> 07   Horizon
01 -> 04 -> 06 -> 07         OpenStackClient
01 -> 05 -> 06 -> 07         OpenTofu
```

## Static verification

```bash
./scripts/offline-validate.sh

tofu fmt -check -recursive opentofu
TOFU_DATA_DIR=/tmp/chapter3-tofu-data \
  tofu -chdir=opentofu init -backend=false
TOFU_DATA_DIR=/tmp/chapter3-tofu-data \
  tofu -chdir=opentofu validate
```

These checks parse the public examples, verify the walkthrough contract, check shell syntax and validate the OpenTofu provider schema. They do not create cloud resources.

## Live prerequisites

Live use requires:

- an approved disposable OpenStack project;
- a protected `clouds.yaml` profile;
- permission to create and delete one server, one volume, one security group, one port and one floating IP;
- separately discovered Nova and Cinder availability zones;
- enough quota and real capacity;
- operator approval for the client CIDR and cleanup decision.

Copy `environment-contract.example.yaml` to the ignored `environment-contract.yaml`, replace every environment-specific value and set `example_only: false`. The preflight rejects the example contract for live work.

## Evidence boundary

A successful client command proves only that its immediate API call returned successfully. The lab accepts the request only after stable identifiers connect Nova, Neutron and Cinder records. A floating IP does not prove login access or an HTTPS service.

No credentials, tokens, endpoints, state, plans or live environment contracts belong in Git. Genuine reference-lab screenshots are public-safe evidence, but their addresses and catalogue values are not universal defaults.
