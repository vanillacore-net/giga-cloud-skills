# Seed guest configuration with Ansible

OpenTofu creates the VM. This playbook makes the guest state repeatable and observable: it checks cloud-init, DNS and time synchronisation; installs containerd and exact Kubernetes packages; holds those packages; renders and validates the kubeadm cluster definition; initializes the API; protects the administrative kubeconfig; installs the pinned Calico operator; declares the Pod network; and waits for a Ready Node.

Copy `inventory.example.yaml` to the ignored file `inventory.yaml`. Copy `group_vars/all.example.yaml` to `group_vars/all.yaml`, then verify that its values match `../../VERSIONS.yaml` and the approved environment contract.

```bash
# Install only the explicitly pinned collections used by the playbook.
ansible-galaxy collection install -r requirements.yaml

# Confirm the inventory path and variables without changing the VM.
ansible-inventory -i inventory.yaml --graph
ansible-playbook -i inventory.yaml seed.yaml --syntax-check

# Review the predicted changes. Some commands cannot provide perfect check mode,
# so this is an aid to review rather than proof that the live run will succeed.
ansible-playbook -i inventory.yaml seed.yaml --check --diff

# Apply the reviewed guest configuration and bootstrap the seed API.
ansible-playbook -i inventory.yaml seed.yaml
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
@all:
  |--@ungrouped:
  |  |--seed
playbook: seed.yaml
PLAY RECAP
seed : ok=<n> changed=<n> unreachable=0 failed=0
```

The example creates a single control-plane seed because the exercise needs a temporary place for the Cluster API controllers. It is not a production high-availability management topology. The reference architecture moves lifecycle and operations to a protected management cluster and retains the same declarative inputs.
