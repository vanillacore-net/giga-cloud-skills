# Chapter 3 practical walkthroughs

The walkthroughs provide three alternative creation paths for one IaaS request. Start with discovery, choose Horizon, OpenStackClient or OpenTofu, then run combined validation and the matching cleanup path.

| Step | Purpose | Companion video |
|---|---|---|
| [01](01-discovery.md) | Discover and approve inputs | C3-P1 |
| [02](02-horizon-security-storage.md) | Create policy and storage in Horizon | C3-P2 |
| [03](03-horizon-compute-networking.md) | Launch and connect the VM in Horizon | C3-P3 |
| [04](04-cli-provisioning.md) | Provision through OpenStackClient | C3-P4 |
| [05](05-opentofu-automation.md) | Review and apply the declaration | C3-P5 |
| [06](06-combined-validation.md) | Prove the resource chain | C3-P6 |
| [07](07-cleanup.md) | Delete safely and prove absence | C3-P7 |

Each walkthrough states its starting state, stopping conditions and evidence needed for the next step. Live commands require a completed local `environment-contract.yaml`; example values are refused.
