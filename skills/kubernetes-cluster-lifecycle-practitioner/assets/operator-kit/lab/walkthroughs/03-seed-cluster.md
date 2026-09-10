# 3. Seed cluster rollout

Video companion: [C4-P3](https://git.vanillacore.net/giga/content/src/commit/b56cad92b74b4335de99879415d437b97ab677cd/chapter-4/VIDEO_SCOPES.md#c4-p3-seed-cluster-configure-the-vm-and-initialize-kubernetes)

## Purpose

Ansible makes the VM preparation repeatable. kubeadm then consumes one explicit cluster definition. Calico implements the Pod network that kubeadm deliberately does not install.

An Ansible playbook is an ordered YAML declaration of the hosts and configuration tasks to apply. Each task calls a module. This excerpt from `seed.yaml` selects the inventory host, enables privilege escalation and declares the package state:

```yaml
- name: Configure and initialise the Chapter 4 seed cluster
  hosts: management-seed
  become: true

  tasks:
    - name: Install container and repository prerequisites
      ansible.builtin.apt:
        name: [ca-certificates, curl, gpg, containerd]
        state: present
        update_cache: true
```

The complete playbook continues with kernel, containerd, package, kubeadm and Calico tasks. Re-running a state-oriented module such as `ansible.builtin.apt` does not reinstall packages that already satisfy the declaration.

An Ansible inventory maps logical host names and groups to connection data. In this reference lab, `management-seed` maps to the seed's private address and `ansible_ssh_common_args` supplies the jump-host `ProxyJump`. If the operator already has direct private access, remove that field rather than inventing a gateway.

```bash
: "${GIGA_OPERATOR_KIT:=$PWD}"
cd "$GIGA_OPERATOR_KIT"
set -euo pipefail
test -r lab-session.env
. ./lab-session.env
cd foundation/ansible

# Copy site-specific files that are ignored by Git.
cp inventory.example.yaml inventory.yaml
mkdir -p group_vars
cp group_vars/all.example.yaml group_vars/all.yaml

# Replace the gateway address, or remove ansible_ssh_common_args when direct
# private access is approved. Check the parsed host graph before any play runs.
ansible-inventory -i inventory.yaml --graph

# Install the exact Ansible collections used by the checked-in playbook.
ansible-galaxy collection install -r requirements.yaml

# Check parser, module and inventory resolution before changing the VM.
ansible-playbook -i inventory.yaml seed.yaml --syntax-check
ansible-playbook -i inventory.yaml seed.yaml --check --diff

# Apply containerd, host prerequisites, package pins, kubeadm and Calico.
ansible-playbook -i inventory.yaml seed.yaml
```

The checked-in example inventory produces this real parser output:



Representative success output (shortened; values in angle brackets are environment-specific):

```text
@all:
  |--@ungrouped:
  |  |--management-seed
```

The rendered kubeadm document defines this Kubernetes cluster. `kubeadm.k8s.io/v1beta4` is the configuration schema supported by the selected Kubernetes release. `v1.36.3` is the cluster version. `10.42.0.20:6443` is the stable single-node learning endpoint. `10.242.0.0/16` is the Pod range consumed by Calico, and `10.98.0.0/16` is the virtual Service range. Production management clusters normally replace the single endpoint with a highly available address and use more than one control-plane Node.

The playbook installs Calico `v3.32.1`, the same version used for child clusters. It downloads the pinned Tigera operator manifest, verifies its SHA-256 value, waits for the Installation API, and applies a separate `Installation` resource with the declared Pod CIDR. There is no unidentified `install-cni.sh` step in this bootstrap path.

We retrieve the kubeconfig without printing it:

```bash
# Create local credentials with restrictive permissions from the first byte.
umask 077

# Reference lab: copy through the jump host because the seed has no floating IP.
scp -o ProxyJump=ubuntu@REPLACE_WITH_GATEWAY_PUBLIC_IP \
  ubuntu@10.42.0.20:.kube/config ./management.kubeconfig

# Direct-private-access alternative: use this instead, not in addition.
# scp ubuntu@10.42.0.20:.kube/config ./management.kubeconfig

# Select the explicit file and inspect its context before any mutable command.
test -r "$KUBECONFIG"
kubectl --kubeconfig "$KUBECONFIG" config get-contexts
kubectl --kubeconfig "$KUBECONFIG" config view --minify \
  -o jsonpath='{.clusters[0].cluster.server}{"\n"}'
kubectl --kubeconfig "$KUBECONFIG" config current-context
../../scripts/require-context.sh "$KUBECONFIG" "$MANAGEMENT_CONTEXT"

# Prove API, Node, DNS and CNI health before installing lifecycle controllers.
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" cluster-info
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" get nodes -o wide
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" -n kube-system get pods -o wide
kubectl --kubeconfig "$KUBECONFIG" --context "$MANAGEMENT_CONTEXT" get tigerastatus
```

The checked-in kubeadm configuration produces `kubernetes-admin@kubernetes`. Confirm that the preceding commands show that context and the seed API address before continuing. If the kubeadm cluster or user name was changed, put the reviewed `current-context` in `MANAGEMENT_CONTEXT` inside the ignored session file. Later helpers stop on a mismatch.

Volatile hashes and ages vary. A successful result has this shape:



Representative success output (shortened; values in angle brackets are environment-specific):

```text
$ kubectl --kubeconfig "$KUBECONFIG" get nodes
NAME              STATUS   ROLES           AGE     VERSION
management-seed   Ready    control-plane   <age>   v1.36.3

$ kubectl --kubeconfig "$KUBECONFIG" -n kube-system get pods -l k8s-app=kube-dns
NAME                 READY   STATUS    RESTARTS   AGE
coredns-<pod-hash>   1/1     Running   0          <age>
coredns-<pod-hash>   1/1     Running   0          <age>

$ kubectl --kubeconfig "$KUBECONFIG" get tigerastatus
NAME        AVAILABLE   PROGRESSING   DEGRADED   SINCE
apiserver   True        False         False      <age>
calico      True        False         False      <age>
ippools     True        False         False      <age>
```

## Evidence gate

We continue only with an authenticated API, a Ready Node, running CoreDNS and healthy Calico status. `Pending`, repeated restarts, `AVAILABLE=False`, `DEGRADED=True` or `NotReady` stop the path. A present kubeconfig file does not prove that the API is reachable.
