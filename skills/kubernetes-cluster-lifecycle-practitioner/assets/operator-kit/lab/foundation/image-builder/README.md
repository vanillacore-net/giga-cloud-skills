# Build the Kubernetes-ready CAPO machine image

CAPO points Nova at a Glance image, but CAPO does not turn an arbitrary cloud image into a Kubernetes Node. The kubeadm bootstrap data expects a compatible operating system with cloud-init and the required host software and configuration. The preferred path in this learning package is Kubernetes SIGs Image Builder, which installs and pins the container runtime, kubelet, kubeadm and supporting packages into a tested artifact.

The general Ubuntu cloud image used by the gateway and seed is the input to this build. The resulting CAPI image is the separate artifact used for every CAPI control-plane and worker Machine at the matching Kubernetes version.

The commands below pin Image Builder to the reviewed source revision used by this package. Building an image creates a temporary OpenStack VM and can take many minutes.

```bash
# Clone the upstream build definitions, then select the reviewed revision.
git clone https://github.com/kubernetes-sigs/image-builder.git
cd image-builder
git checkout 96bd49f71859ff7863f08ba4dc3321c560f8802b

# Install the OpenStack image-build dependencies declared by the project.
cd images/capi
make deps-openstack

# Copy the public-safe example outside the clone and replace every value found
# during discovery. Do not place OpenStack credentials in this JSON file.
cp "${GIGA_OPERATOR_KIT:?Set GIGA_OPERATOR_KIT to the operator-kit lab directory}/foundation/image-builder/openstack-vars.example.json" /secure/work/openstack-vars.json

# Build the exact Ubuntu 24.04 / Kubernetes v1.36.3 artifact.
PACKER_VAR_FILES=/secure/work/openstack-vars.json   make build-openstack-ubuntu-2404
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
Installed plugin github.com/hashicorp/openstack <pinned-version>
Build openstack.ubuntu finished.
Artifact ID: <openstack-region>/<image-uuid>
```

Resolve the resulting image UUID rather than relying on its display name. Attach evidence that allows the artifact to be reviewed later:

```bash
# Resolve the one image created by the reviewed build.
openstack --os-cloud "$OS_CLOUD" image list   --name capi-ubuntu-2404-kube-v1.36.3 --status active

# Record the immutable UUID and inspect all current properties.
OPENSTACK_IMAGE_ID="REPLACE_WITH_UNIQUE_RESULT_UUID"
openstack --os-cloud "$OS_CLOUD" image show "$OPENSTACK_IMAGE_ID" -f json

# Store non-secret provenance on the private image. Sites may use a separate
# signed image catalogue instead of custom Glance properties.
openstack --os-cloud "$OS_CLOUD" image set   --property org.opencontainers.image.revision=96bd49f71859ff7863f08ba4dc3321c560f8802b   --property io.kubernetes.version=v1.36.3   "$OPENSTACK_IMAGE_ID"
```

Representative success output (shortened; values in angle brackets are environment-specific):

```text
project_id: <openstack-project-uuid>
image: <approved-image-uuid>  capi-ubuntu-2404-kube-<version>  active
network: <private-network-uuid>  private
subnet: <private-subnet-uuid>  10.41.0.0/24
```

A different image is valid only when the operator can prove equivalent prerequisites, version compatibility, cloud-init behaviour and lifecycle ownership. "Cloud-init enabled" by itself is not that proof.
