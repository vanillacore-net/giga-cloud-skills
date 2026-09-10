# Seed infrastructure with OpenTofu

This module owns the disposable IaaS foundation used in the Chapter 4 walkthrough: one private management network, its router, a restricted jump host, a private seed VM, ports, security groups, one key pair and one floating IP for the jump host. The reference lab requires a jump host because it assumes no direct private operator access. Sites with an approved VPN or direct private access can adapt the module and omit it. The module does not install Kubernetes; Ansible owns the guest configuration in the next step.

Copy `terraform.tfvars.example` to the ignored file `terraform.tfvars` and replace every `REPLACE_` value with an ID or value approved during discovery. OpenTofu uses the named `clouds.yaml` profile; credentials do not belong in this directory or in state-variable files.

```bash
# Format and validate the declarations before contacting OpenStack.
tofu fmt -check
tofu init
tofu validate

# Save a plan so that the reviewed change is exactly what will be applied.
tofu plan -out=seed.tfplan

# Read the complete plan. Confirm image and flavor IDs, fixed addresses,
# security-group sources, Nova availability zone and all replacements.
tofu show seed.tfplan

# Apply only the plan that was reviewed above.
tofu apply seed.tfplan

# Export stable outputs for the Ansible inventory and evidence record.
tofu output -json > ../../artifacts/seed-outputs.json
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
OpenTofu has been successfully initialized!
Success! The configuration is valid.
Plan: <n> to add, 0 to change, 0 to destroy.
Apply complete! Resources: <n> added, 0 changed, 0 destroyed.
```

Do not commit `terraform.tfvars`, `seed.tfplan`, `.terraform`, state files or generated outputs. Protect the state backend because OpenTofu state can contain infrastructure identifiers and derived configuration.
