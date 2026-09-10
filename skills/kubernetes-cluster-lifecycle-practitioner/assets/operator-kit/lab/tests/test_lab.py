from __future__ import annotations

import importlib.util
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_lablib():
    path = ROOT / "scripts" / "lablib.py"
    spec = importlib.util.spec_from_file_location("lablib", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lablib = load_lablib()
        cls.contract = cls.lablib.load_yaml(ROOT / "environment-contract.example.yaml")

    def test_portable_source_record(self):
        source = (ROOT.parent / "SOURCE.md").read_text()
        self.assertIn("b56cad92b74b4335de99879415d437b97ab677cd", source)

    def test_required_companion_files_exist(self):
        required = {
            "README.md",
            "VERSIONS.yaml",
            "environment-contract.example.yaml",
            "hub-spoke-contract.example.yaml",
            "lab-session.env.example",
            "manifests/base/clusterclass.yaml",
            "manifests/probe/destination.yaml",
            "manifests/probe/storage-smoke.yaml",
            "addons/cert-manager/v1.20.3.yaml",
            "addons/contour/v1.33.7.yaml",
            "addons/local-path-provisioner/v0.0.37.yaml",
            "overlays/loadbalancer.yaml",
            "overlays/service-a.yaml",
            "scripts/offline-validate.sh",
            "scripts/preflight.py",
            "scripts/preflight-readonly.sh",
            "scripts/require-context.sh",
            "scripts/render-manifests.py",
            "scripts/render-clusters.sh",
            "scripts/install-providers.sh",
            "scripts/install-management-ingress.sh",
            "scripts/create-cloud-secret.sh",
            "scripts/apply.sh",
            "scripts/wait-for-cluster.sh",
            "scripts/install-cni.sh",
            "scripts/verify-resource-chain.sh",
            "scripts/set-worker-replicas.sh",
            "scripts/scale-workers.sh",
            "scripts/set-cluster-upgrade.py",
            "scripts/upgrade-cluster.sh",
            "scripts/prepare-path-probe.sh",
            "scripts/render-path-contract.py",
            "scripts/verify-hub-spoke.sh",
            "scripts/cleanup-path-probe.sh",
            "scripts/cleanup.sh",
            "scripts/wait-for-cluster-absence.sh",
            "scripts/verify-openstack-absence.sh",
            "scripts/capture-openstack-ids.py",
            "scripts/verify-management-api-path.sh",
            "scripts/install-argocd.sh",
            "scripts/prepare-gitops-repository.sh",
            "scripts/render-gitops.py",
            "scripts/register-argocd-cluster.sh",
            "scripts/unregister-argocd-cluster.sh",
            "gitops/repository-template/workloads/demo/deployment.yaml",
            "gitops/repository-template/workloads/demo/service.yaml",
            "foundation/opentofu/bootstrap/versions.tf",
            "foundation/opentofu/bootstrap/main.tf",
            "foundation/opentofu/bootstrap/variables.tf",
            "foundation/opentofu/bootstrap/outputs.tf",
            "foundation/opentofu/bootstrap/.terraform.lock.hcl",
            "foundation/ansible/seed.yaml",
            "foundation/ansible/group_vars/all.example.yaml",
            "foundation/ansible/templates/kubeadm-config.yaml.j2",
            "foundation/image-builder/README.md",
            "walkthroughs/README.md",
        }
        required.update(f"walkthroughs/{index:02d}-{slug}.md" for index, slug in enumerate((
            "discovery",
            "seed-infrastructure",
            "seed-cluster",
            "workload-configuration",
            "workload-rollout",
            "adjustments",
            "loadbalancer-edge",
            "argocd-cluster-workload-management",
            "cleanup",
        ), 1))
        missing = sorted(path for path in required if not (ROOT / path).is_file())
        self.assertEqual(missing, [])

    def test_requested_versions_are_pinned(self):
        versions = yaml.safe_load((ROOT / "VERSIONS.yaml").read_text())
        self.assertEqual(versions["cluster_api"], "v1.13.4")
        self.assertEqual(versions["cluster_api_contract"], "v1beta2")
        self.assertEqual(versions["cert_manager"], "v1.20.3")
        self.assertRegex(versions["cert_manager_manifest_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(versions["contour"]["version"], "v1.33.7")
        self.assertRegex(versions["contour"]["manifest_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(versions["openstack_provider"], "v0.14.6")
        self.assertEqual(versions["openstack_provider_contract"], "v1beta1")
        self.assertEqual(versions["openstack_resource_controller"]["version"], "v2.6.0")
        self.assertEqual(versions["kubernetes"], "v1.36.3")
        for value in (
            versions["clusterctl"]["linux_amd64_sha256"],
            versions["openstack_provider_components_sha256"],
            versions["openstack_resource_controller"]["install_sha256"],
            versions["calico"]["operator_manifest_sha256"],
            versions["argocd"]["install_manifest_sha256"],
            versions["argocd"]["linux_amd64_sha256"],
        ):
            self.assertRegex(value, r"^[0-9a-f]{64}$")
        self.assertEqual(versions["argocd"]["version"], "v3.5.2")
        self.assertEqual(versions["local_path_provisioner"]["version"], "v0.0.37")
        self.assertRegex(versions["local_path_provisioner"]["manifest_sha256"], r"^[0-9a-f]{64}$")

    def test_seed_foundation_uses_the_same_explicit_contract(self):
        variables = (ROOT / "foundation/opentofu/bootstrap/variables.tf").read_text()
        main = (ROOT / "foundation/opentofu/bootstrap/main.tf").read_text()
        seed_values = yaml.safe_load((ROOT / "foundation/ansible/group_vars/all.example.yaml").read_text())
        self.assertIn('default     = "10.42.0.0/24"', variables)
        self.assertIn("base_image_id", variables)
        self.assertIn("compute_availability_zone", variables)
        self.assertIn("image_id          = var.base_image_id", main)
        self.assertIn("availability_zone = var.compute_availability_zone", main)
        self.assertEqual(seed_values["kubernetes_version"], "v1.36.3")
        self.assertEqual(seed_values["kubeadm_config_api_version"], "kubeadm.k8s.io/v1beta4")
        self.assertEqual(seed_values["management_pod_cidr"], self.contract["lab"]["management_pod_cidr"])
        self.assertEqual(seed_values["management_service_cidr"], self.contract["lab"]["management_service_cidr"])
        self.assertEqual(seed_values["calico_version"], "v3.32.1")
        self.assertEqual(seed_values["calico_operator_sha256"], "f18e073794207d372606bc3ea6f8fd73972f86d6828f4ba666dfe0d4aa8ab07f")

    def test_argocd_declarations_are_rendered_with_bounded_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "gitops"
            subprocess.run(
                [
                    "python3", str(ROOT / "scripts/render-gitops.py"),
                    "--repo-url", "https://example.invalid/platform/config.git",
                    "--revision", "main",
                    "--output", str(output),
                    "--allow-example",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            files = sorted(output.glob("*.yaml"))
            self.assertEqual([p.name for p in files], ["01-project.yaml", "02-cluster-lifecycle.yaml", "03-workloads-applicationset.yaml"])
            project, lifecycle, workloads = [yaml.safe_load(p.read_text()) for p in files]
            self.assertEqual(project["kind"], "AppProject")
            self.assertEqual(project["spec"]["namespaceResourceBlacklist"], [{"group": "", "kind": "Secret"}])
            self.assertEqual(lifecycle["kind"], "Application")
            self.assertFalse(lifecycle["spec"]["syncPolicy"]["automated"]["prune"])
            self.assertEqual(workloads["kind"], "ApplicationSet")
            selector = workloads["spec"]["generators"][0]["clusters"]["selector"]["matchLabels"]
            self.assertEqual(selector, {"platform.vanillacore.net/workloads-enabled": "true"})
            self.assertEqual(workloads["spec"]["template"]["spec"]["destination"]["namespace"], "workload-demo")

        docs = (ROOT / "walkthroughs/08-argocd-cluster-workload-management.md").read_text()
        self.assertNotIn("deployment/argocd-application-controller successfully rolled out", docs)
        self.assertIn("statefulset rolling update complete", docs)

    def test_all_shell_helpers_parse(self):
        for script in sorted((ROOT / "scripts").glob("*.sh")):
            subprocess.run(["bash", "-n", str(script)], check=True, capture_output=True, text=True)

    def test_environment_contract_has_non_overlapping_cidrs(self):
        errors = self.lablib.validate_environment(self.contract, require_live=False)
        self.assertEqual(errors, [])
        networks = []
        for key in ("management_cidr", "management_pod_cidr", "management_service_cidr", "transit_cidr"):
            networks.append(ipaddress.ip_network(self.contract["lab"][key]))
        for cluster in self.contract["clusters"]:
            for key in ("node_cidr", "pod_cidr", "service_cidr"):
                networks.append(ipaddress.ip_network(cluster[key]))
        for index, first in enumerate(networks):
            for second in networks[index + 1 :]:
                self.assertFalse(first.overlaps(second), f"CIDRs overlap: {first} and {second}")

    def test_example_contract_is_rejected_for_live_use(self):
        errors = self.lablib.validate_environment(self.contract, require_live=True)
        self.assertTrue(any("example" in error.lower() for error in errors))
        self.assertTrue(any("unresolved" in error.lower() for error in errors))

    def test_rendered_clusters_have_pinned_version_ownership_and_class(self):
        for overlay_name in ("loadbalancer", "service-a"):
            overlay = self.lablib.load_yaml(ROOT / "overlays" / f"{overlay_name}.yaml")
            document = self.lablib.render_cluster(self.contract, overlay)
            self.assertEqual(document["apiVersion"], "cluster.x-k8s.io/v1beta2")
            self.assertEqual(document["kind"], "Cluster")
            self.assertEqual(document["spec"]["topology"]["version"], "v1.36.3")
            self.assertEqual(document["spec"]["topology"]["classRef"]["namespace"], "capi-lab-blueprints")
            labels = document["metadata"]["labels"]
            self.assertEqual(labels["lab.example.invalid/managed-by"], "chapter4-capi-openstack-lab")
            self.assertEqual(labels["lab.example.invalid/role"], overlay_name)
            self.assertEqual(document["metadata"]["annotations"]["lab.example.invalid/ownership-token"], self.contract["lab"]["ownership_token"])
            variables = {item["name"]: item["value"] for item in document["spec"]["topology"]["variables"]}
            self.assertEqual(variables["identityRef"]["type"], "Secret")
            self.assertNotIn("secret", {key.lower() for key in variables["identityRef"]})

    def test_renderer_emits_a_reconciled_storage_baseline_per_cluster(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "rendered"
            subprocess.run(
                [
                    "python3", str(ROOT / "scripts/render-manifests.py"),
                    "--contract", str(ROOT / "environment-contract.example.yaml"),
                    "--output", str(output),
                    "--allow-example",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            for name in ("loadbalancer", "service-a"):
                cluster = yaml.safe_load((output / f"{name}.yaml").read_text())
                self.assertEqual(cluster["metadata"]["labels"]["lab.example.invalid/storage-baseline"], "local-path")

                addon_path = output / "addons" / f"{name}-storage.yaml"
                documents = [item for item in yaml.safe_load_all(addon_path.read_text()) if item]
                self.assertEqual([item["kind"] for item in documents], ["ConfigMap", "ClusterResourceSet"])
                config_map, resource_set = documents
                self.assertEqual(config_map["metadata"]["namespace"], name)
                self.assertIn("docker.io/rancher/local-path-provisioner:v0.0.37", config_map["data"]["local-path-storage.yaml"])
                self.assertIn("docker.io/library/busybox:1.37.0", config_map["data"]["local-path-storage.yaml"])
                self.assertEqual(resource_set["apiVersion"], "addons.cluster.x-k8s.io/v1beta2")
                self.assertEqual(resource_set["metadata"]["namespace"], name)
                self.assertEqual(resource_set["spec"]["strategy"], "Reconcile")
                self.assertEqual(
                    resource_set["spec"]["clusterSelector"]["matchLabels"],
                    {"lab.example.invalid/storage-baseline": "local-path"},
                )

    def test_renderer_emits_certificate_and_ingress_baselines_per_child_cluster(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "rendered"
            subprocess.run(
                [
                    "python3", str(ROOT / "scripts/render-manifests.py"),
                    "--contract", str(ROOT / "environment-contract.example.yaml"),
                    "--output", str(output),
                    "--allow-example",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            for name in ("loadbalancer", "service-a"):
                cluster = yaml.safe_load((output / f"{name}.yaml").read_text())
                labels = cluster["metadata"]["labels"]
                self.assertEqual(labels["lab.example.invalid/certificate-baseline"], "cert-manager")
                self.assertEqual(labels["lab.example.invalid/ingress-baseline"], "contour")

                certificate_documents = [
                    item for item in yaml.safe_load_all((output / "addons" / f"{name}-cert-manager.yaml").read_text()) if item
                ]
                certificate_maps = [item for item in certificate_documents if item["kind"] == "ConfigMap"]
                certificate_sets = [item for item in certificate_documents if item["kind"] == "ClusterResourceSet"]
                self.assertGreaterEqual(len(certificate_maps), 2)
                self.assertEqual(len(certificate_sets), 1)
                self.assertEqual(
                    certificate_sets[0]["spec"]["clusterSelector"]["matchLabels"],
                    {"lab.example.invalid/certificate-baseline": "cert-manager"},
                )
                self.assertEqual(
                    len(certificate_sets[0]["spec"]["resources"]), len(certificate_maps)
                )
                self.assertTrue(all(len(json.dumps(item).encode()) < 900_000 for item in certificate_maps))
                certificate_payload = "\n".join(
                    value for item in certificate_maps for value in item["data"].values()
                )
                self.assertIn("quay.io/jetstack/cert-manager-controller:v1.20.3", certificate_payload)

                ingress_documents = [
                    item for item in yaml.safe_load_all((output / "addons" / f"{name}-contour.yaml").read_text()) if item
                ]
                ingress_map, ingress_set = ingress_documents
                self.assertEqual(ingress_map["kind"], "ConfigMap")
                self.assertEqual(ingress_set["kind"], "ClusterResourceSet")
                self.assertEqual(
                    ingress_set["spec"]["clusterSelector"]["matchLabels"],
                    {"lab.example.invalid/ingress-baseline": "contour"},
                )
                ingress_payload = next(iter(ingress_map["data"].values()))
                self.assertIn("ghcr.io/projectcontour/contour:v1.33.7", ingress_payload)
                self.assertNotIn("type: LoadBalancer", ingress_payload)
                payload_objects = [item for item in yaml.safe_load_all(ingress_payload) if item]
                envoy_service = next(
                    item for item in payload_objects
                    if item["kind"] == "Service" and item["metadata"]["name"] == "envoy"
                )
                self.assertEqual(envoy_service["spec"]["type"], "ClusterIP")
                self.assertNotIn("externalTrafficPolicy", envoy_service["spec"])
                self.assertNotIn("annotations", envoy_service["metadata"])

    def test_management_ingress_reuses_clusterctl_cert_manager_and_installs_contour(self):
        script = (ROOT / "scripts/install-management-ingress.sh").read_text()
        self.assertIn("addons/contour/v1.33.7.yaml", script)
        self.assertIn("rollout status deployment/contour", script)
        self.assertIn("rollout status daemonset/envoy", script)
        self.assertIn("spec.type", script)
        self.assertIn("status.loadBalancer.ingress", script)
        self.assertNotIn("cert-manager.yaml", script)

    def test_hub_spoke_probe_targets_workload_ingress(self):
        destination = (ROOT / "manifests/probe/destination.yaml").read_text()
        prepare = (ROOT / "scripts/prepare-path-probe.sh").read_text()
        verify = (ROOT / "scripts/verify-hub-spoke.sh").read_text()
        cleanup = (ROOT / "scripts/cleanup-path-probe.sh").read_text()
        contract = yaml.safe_load((ROOT / "hub-spoke-contract.example.yaml").read_text())
        self.assertIn("kind: Ingress", destination)
        self.assertIn("ingressClassName: contour", destination)
        self.assertIn('get "service/$ENVOY_SERVICE"', prepare)
        self.assertEqual(contract["destination"]["envoy_service"]["name"], "envoy")
        self.assertIn("destination.kubeconfig", prepare)
        self.assertIn("destination.api_server", prepare)
        self.assertIn("render-path-contract.py", (ROOT / "README.md").read_text())
        self.assertIn("require-context.sh", prepare)
        self.assertIn("CONFIRM_PATH_DESTINATION", prepare)
        self.assertIn("source.context", verify)
        self.assertIn("source.api_server", verify)
        self.assertIn("destination.kubeconfig", verify)
        self.assertIn("destination.context", verify)
        self.assertIn("destination.api_server", verify)
        self.assertIn("spec.clusterIP", verify)
        self.assertIn("spec.type", verify)
        self.assertIn("status.loadBalancer.ingress", verify)
        self.assertIn("spec.ingressClassName", verify)
        self.assertIn("spec.rules[0].http.paths[0].backend.service.name", verify)
        self.assertIn("CONFIRM_PATH_TEST", verify)
        self.assertNotIn("destination.url", verify)
        self.assertIn("require-context.sh", cleanup)
        self.assertIn("CONFIRM_PATH_TEST_CLEANUP", cleanup)
        self.assertIn('--context "$LOADBALANCER_CONTEXT"', cleanup)
        self.assertIn('--context "$SERVICE_A_CONTEXT"', cleanup)

    def test_path_contract_renderer_binds_contexts_and_api_servers(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            source = work / "loadbalancer.kubeconfig"
            destination = work / "service-a.kubeconfig"
            source.touch()
            destination.touch()
            kubectl = work / "kubectl"
            kubectl.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "for ((i=1;i<=$#;i++)); do [[ ${!i} == --context ]] && { j=$((i+1)); context=${!j}; }; done\n"
                "[[ $* == *'config current-context'* ]] && { printf '%s\\n' \"$context\"; exit 0; }\n"
                "[[ $* == *'config view'* ]] || exit 2\n"
                "[[ $* == *loadbalancer.kubeconfig* ]] && printf 'https://10.40.0.10:6443' || printf 'https://10.41.0.10:6443'\n"
            )
            kubectl.chmod(0o755)
            output = work / "contract.yaml"
            environment = os.environ.copy()
            environment["PATH"] = f"{work}:{environment['PATH']}"
            result = subprocess.run(
                [
                    "python3", str(ROOT / "scripts/render-path-contract.py"),
                    "--source-kubeconfig", str(source), "--source-context", "loadbalancer-admin@loadbalancer",
                    "--destination-kubeconfig", str(destination), "--destination-context", "service-a-admin@service-a",
                    "--output", str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
            rendered = yaml.safe_load(output.read_text())
            self.assertEqual(rendered["source"]["api_server"], "https://10.40.0.10:6443")
            self.assertEqual(rendered["destination"]["api_server"], "https://10.41.0.10:6443")
            self.assertEqual(rendered["source"]["context"], "loadbalancer-admin@loadbalancer")
            self.assertIn("Next: review the file", result.stdout)

    def test_shell_examples_have_session_setup_and_success_output(self):
        paths = sorted(ROOT.parent.rglob("*.md"))
        combined = "\n".join(path.read_text() for path in paths)
        self.assertNotRegex(combined, r"(?m)^export\s+")
        session = (ROOT / "lab-session.env.example").read_text()
        self.assertIn("MANAGEMENT_CONTEXT=", session)
        self.assertIn("SERVICE_A_CONTEXT=", session)
        self.assertIn("LOADBALANCER_CONTEXT=", session)
        self.assertNotIn("CONFIRM_", session)
        for path in paths:
            text = path.read_text()
            for match in re.finditer(r"```bash\n.*?\n```", text, flags=re.S):
                tail = text[match.end():]
                boundaries = [position for position in (
                    tail.find("\n```bash"), tail.find("\n## "), tail.find("\n### "), tail.find("\n#### ")
                ) if position >= 0]
                segment = tail[:min(boundaries)] if boundaries else tail
                self.assertIn("Representative success output", segment, f"missing output after shell block in {path}")
                self.assertIn("```text", segment, f"missing text output fence after shell block in {path}")

    def test_storage_smoke_probe_binds_writes_and_reads(self):
        documents = [
            item for item in yaml.safe_load_all((ROOT / "manifests/probe/storage-smoke.yaml").read_text()) if item
        ]
        self.assertEqual([item["kind"] for item in documents], ["Namespace", "PersistentVolumeClaim", "Pod"])
        claim = documents[1]
        pod = documents[2]
        self.assertEqual(claim["spec"]["storageClassName"], "local-path")
        self.assertEqual(claim["spec"]["accessModes"], ["ReadWriteOnce"])
        command = " ".join(pod["spec"]["containers"][0]["command"])
        self.assertIn("chapter-4-storage-ready", command)
        self.assertIn("grep", command)
        self.assertEqual(pod["spec"]["volumes"][0]["persistentVolumeClaim"]["claimName"], claim["metadata"]["name"])

    def test_upgrade_inputs_are_scoped_to_one_cluster(self):
        target_image = "11111111-1111-4111-8111-111111111111"
        with tempfile.TemporaryDirectory() as temporary_directory:
            contract_path = Path(temporary_directory) / "contract.yaml"
            contract_path.write_text((ROOT / "environment-contract.example.yaml").read_text())
            subprocess.run(
                [
                    str(ROOT / "scripts/set-cluster-upgrade.py"),
                    str(contract_path),
                    "service-a",
                    "v1.37.1",
                    target_image,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            contract = self.lablib.load_yaml(contract_path)
            service = self.lablib.render_cluster(contract, {"cluster": "service-a"})
            edge = self.lablib.render_cluster(contract, {"cluster": "loadbalancer"})
            self.assertEqual(service["spec"]["topology"]["version"], "v1.37.1")
            service_variables = {item["name"]: item["value"] for item in service["spec"]["topology"]["variables"]}
            edge_variables = {item["name"]: item["value"] for item in edge["spec"]["topology"]["variables"]}
            self.assertEqual(service_variables["imageID"], target_image)
            self.assertEqual(edge["spec"]["topology"]["version"], "v1.36.3")
            self.assertEqual(edge_variables["imageID"], self.contract["openstack"]["image_id"])

    def test_upgrade_helper_is_reviewed_bounded_and_verifies_the_result(self):
        script = (ROOT / "scripts/upgrade-cluster.sh").read_text()
        for required in (
            "validate-manifests.sh",
            "diff -f",
            "PREPARE_ONLY",
            "CONFIRM_UPGRADE",
            "rollout status",
            "MachinesUpToDate",
            "MachinesReady",
            "verify-resource-chain.sh",
            "clusterctl --kubeconfig",
        ):
            self.assertIn(required, script)
        self.assertGreaterEqual(script.count("rollout status"), 2)
        self.assertLess(script.index("validate-manifests.sh"), script.index("CONFIRM_UPGRADE"))
        self.assertLess(script.index("CONFIRM_UPGRADE"), script.index("apply -f"))
        self.assertLess(script.index("kubeadmcontrolplane"), script.index("machinedeployment"))
        self.assertNotIn("kubectl patch", script)
        walkthrough = (ROOT / "walkthroughs/06-adjustments.md").read_text()
        self.assertIn("evidence/upgrade/service-a.yaml", walkthrough)
        self.assertIn("remains explicitly `not-tested`", walkthrough)

    def _run_upgrade_prepare(
        self,
        temporary: Path,
        *,
        argument_namespace: str = "service-a",
        machine_version: str = "v1.36.3",
        node_version: str = "v1.36.3",
        child_matches: bool = True,
    ):
        target_image = "11111111-1111-4111-8111-111111111111"
        server_ids = [
            "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        ]
        node_ids = server_ids if child_matches else [
            "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
        ]
        labels = {"cluster.x-k8s.io/cluster-name": "service-a"}
        machines = []
        infrastructure = []
        nodes = []
        for index, identifier in enumerate(server_ids):
            name = f"machine-{index}"
            infra_name = f"openstack-machine-{index}"
            uid = f"uid-{index}"
            machines.append({
                "metadata": {"name": name, "namespace": "service-a", "uid": uid, "labels": labels},
                "spec": {
                    "version": machine_version,
                    "providerID": f"openstack:///{identifier}",
                    "infrastructureRef": {
                        "apiGroup": "infrastructure.cluster.x-k8s.io",
                        "kind": "OpenStackMachine",
                        "name": infra_name,
                    },
                },
            })
            infrastructure.append({
                "metadata": {
                    "name": infra_name,
                    "namespace": "service-a",
                    "labels": labels,
                    "ownerReferences": [{
                        "kind": "Machine", "name": name, "uid": uid, "controller": True,
                    }],
                },
                "status": {"instanceID": identifier, "ready": True},
            })
        for index, identifier in enumerate(node_ids):
            nodes.append({
                "metadata": {"name": f"node-{index}"},
                "spec": {"providerID": f"openstack:///{identifier}"},
                "status": {
                    "nodeInfo": {"kubeletVersion": node_version},
                    "conditions": [{"type": "Ready", "status": "True"}],
                },
            })
        machines_path = temporary / "machines.json"
        infrastructure_path = temporary / "openstackmachines.json"
        nodes_path = temporary / "nodes.json"
        machines_path.write_text(json.dumps({"items": machines}))
        infrastructure_path.write_text(json.dumps({"items": infrastructure}))
        nodes_path.write_text(json.dumps({"items": nodes}))

        fake_bin = temporary / "bin"
        fake_bin.mkdir()
        call_log = temporary / "calls.log"
        fake_kubectl = fake_bin / "kubectl"
        fake_kubectl.write_text(
            "#!/usr/bin/env bash\n"
            "printf '%s\\n' \"$*\" >> \"$CALL_LOG\"\n"
            "if [[ \" $* \" == *\" config current-context\"* ]]; then echo mgmt-context; exit 0; fi\n"
            "if [[ \"$*\" == *\"get cluster service-a -o jsonpath=\"* ]]; then printf v1.36.3; exit 0; fi\n"
            "if [[ \"$*\" == *\"get cluster service-a -o wide\"* ]]; then echo service-a; exit 0; fi\n"
            "if [[ \" $* \" == *\" get machines \"* ]]; then cat \"$MACHINES_JSON\"; exit 0; fi\n"
            "if [[ \" $* \" == *\" get openstackmachines.infrastructure.cluster.x-k8s.io \"* ]]; then cat \"$INFRA_JSON\"; exit 0; fi\n"
            "if [[ \" $* \" == *\" get nodes -o json \"* ]]; then cat \"$NODES_JSON\"; exit 0; fi\n"
            "if [[ \" $* \" == *\" diff -f \"* ]]; then exit 1; fi\n"
            "exit 0\n"
        )
        fake_kubectl.chmod(0o755)
        fake_openstack = fake_bin / "openstack"
        fake_openstack.write_text(
            "#!/usr/bin/env bash\n"
            "printf '%s\\n' \"$*\" >> \"$CALL_LOG\"\n"
            "if [[ \" $* \" == *\" image show \"* ]]; then printf '%s\\n' \"$FAKE_IMAGE\"; exit 0; fi\n"
            "previous=\n"
            "for argument in \"$@\"; do\n"
            "  if [[ \"$previous\" == show ]]; then printf '%s\\n' \"$argument\"; exit 0; fi\n"
            "  previous=$argument\n"
            "done\n"
            "exit 2\n"
        )
        fake_openstack.chmod(0o755)

        contract = json.loads(json.dumps(self.contract))
        contract["lab"]["example_only"] = False
        contract["lab"]["management_cluster_context"] = "mgmt-context"
        contract["openstack"].update({
            "credential_secret_name": "capo-cloud",
            "image_id": "22222222-2222-4222-8222-222222222222",
            "control_plane_flavor": "control-plane",
            "worker_flavor": "worker",
            "availability_zone": "az1",
            "ssh_key_name": "capi-key",
            "security_group_id": "33333333-3333-4333-8333-333333333333",
        })
        for index, cluster in enumerate(contract["clusters"], 1):
            cluster["network_id"] = f"44444444-4444-4444-8444-44444444444{index}"
            cluster["subnet_id"] = f"55555555-5555-4555-8555-55555555555{index}"
        contract_path = temporary / "contract.yaml"
        contract_path.write_text(yaml.safe_dump(contract, sort_keys=False))
        original = contract_path.read_text()
        management = temporary / "management.kubeconfig"
        child = temporary / "child.kubeconfig"
        management.write_text("management")
        child.write_text("child")
        output = temporary / "upgrade"
        environment = os.environ.copy()
        environment.update({
            "PATH": f"{fake_bin}:{environment['PATH']}",
            "CALL_LOG": str(call_log),
            "FAKE_IMAGE": target_image,
            "MACHINES_JSON": str(machines_path),
            "INFRA_JSON": str(infrastructure_path),
            "NODES_JSON": str(nodes_path),
            "CONFIRM_MANAGEMENT_CONTEXT": "mgmt-context",
            "PREPARE_ONLY": "yes",
        })
        result = subprocess.run(
            [
                str(ROOT / "scripts/upgrade-cluster.sh"),
                str(contract_path), argument_namespace, "service-a", "v1.37.1", target_image,
                str(management), "mgmt-context", str(child), "openstack",
                "kube-system", "coredns", str(output),
            ],
            text=True,
            capture_output=True,
            env=environment,
            check=False,
        )
        calls = call_log.read_text().splitlines() if call_log.exists() else []
        return result, contract_path, original, output, calls, target_image

    def test_upgrade_prepare_only_renders_without_apply_or_contract_change(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            result, contract_path, original, output, calls, target_image = self._run_upgrade_prepare(
                Path(temporary_directory)
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("prepare-only complete", result.stdout)
            self.assertEqual(contract_path.read_text(), original)
            rendered = yaml.safe_load((output / "service-a.yaml").read_text())
            self.assertEqual(rendered["spec"]["topology"]["version"], "v1.37.1")
            variables = {item["name"]: item["value"] for item in rendered["spec"]["topology"]["variables"]}
            self.assertEqual(variables["imageID"], target_image)
            apply_calls = [call for call in calls if " apply " in f" {call} "]
            self.assertTrue(apply_calls)
            self.assertTrue(all("--dry-run=server" in call for call in apply_calls))

    def test_upgrade_rejects_mismatched_namespace_incomplete_rollout_and_wrong_child(self):
        scenarios = (
            ({"argument_namespace": "other"}, "namespace mismatch"),
            ({"machine_version": "v1.35.9", "node_version": "v1.35.9"}, "has not converged"),
            ({"child_matches": False}, "no Kubernetes Node has providerID"),
        )
        for options, expected_error in scenarios:
            with self.subTest(options=options), tempfile.TemporaryDirectory() as temporary_directory:
                result, contract_path, original, _output, calls, _image = self._run_upgrade_prepare(
                    Path(temporary_directory), **options
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected_error, result.stderr)
                self.assertEqual(contract_path.read_text(), original)
                self.assertFalse(any(" apply " in f" {call} " for call in calls))

    def test_cluster_topology_is_enabled_by_installer(self):
        installer = (ROOT / "scripts" / "install-providers.sh").read_text()
        self.assertIn("export CLUSTER_TOPOLOGY=true", installer)
        self.assertLess(installer.index("export CLUSTER_TOPOLOGY=true"), installer.index('"$CLUSTERCTL" init'))

    def test_walkthroughs_have_explicit_fresh_shell_boundaries(self):
        texts = {path.name: path.read_text() for path in (ROOT / "walkthroughs").glob("*.md")}
        joined = "\n".join(texts.values())
        self.assertNotIn('CONFIRM_MANAGEMENT_CONTEXT="$(' , joined)
        for name in (
            "02-seed-infrastructure.md",
            "05-workload-rollout.md",
            "06-adjustments.md",
            "09-cleanup.md",
        ):
            self.assertIn('. ./lab-session.env', texts[name])
            self.assertIn('test -r "$OS_CLIENT_CONFIG_FILE"', texts[name])
        for name in (
            "03-seed-cluster.md",
            "04-workload-configuration.md",
            "05-workload-rollout.md",
            "06-adjustments.md",
            "07-loadbalancer-edge.md",
            "08-argocd-cluster-workload-management.md",
            "09-cleanup.md",
        ):
            self.assertNotIn("REPLACE_WITH_EXPECTED_MANAGEMENT_CONTEXT", texts[name])
            self.assertIn('. ./lab-session.env', texts[name])
            self.assertIn('"$MANAGEMENT_CONTEXT"', texts[name])
            self.assertIn("config current-context", texts[name])
            self.assertIn("require-context.sh", texts[name])
            self.assertNotRegex(texts[name], r"(?m)^export\s+")
        self.assertIn("set -euo pipefail", texts["05-workload-rollout.md"])
        self.assertIn("set -euo pipefail", texts["07-loadbalancer-edge.md"])

    def test_cleanup_stops_reconciliation_before_capi_deletion(self):
        cleanup = (ROOT / "walkthroughs/09-cleanup.md").read_text()
        stop_position = cleanup.index("delete application/child-cluster-lifecycle")
        unregister_position = cleanup.index("unregister-argocd-cluster.sh")
        capi_delete_position = cleanup.index("./scripts/cleanup.sh")
        self.assertLess(stop_position, unregister_position)
        self.assertLess(unregister_position, capi_delete_position)
        self.assertIn("APPROVED_REMOVAL_REVISION", cleanup)
        self.assertIn("--cascade=orphan", cleanup)

    def test_ownership_and_registration_cleanup_are_failure_aware(self):
        ownership = (ROOT / "scripts/verify-resource-chain.sh").read_text()
        self.assertIn("infrastructureRef", ownership)
        self.assertIn("ownerReferences", ownership)
        self.assertIn("controller') is True", ownership)
        register = (ROOT / "scripts/register-argocd-cluster.sh").read_text()
        self.assertIn("cleanup_on_exit", register)
        self.assertIn("REGISTRATION_COMMITTED=true", register)
        unregister = (ROOT / "scripts/unregister-argocd-cluster.sh").read_text()
        self.assertLess(unregister.index("delete rolebinding/"), unregister.index('delete secret "cluster-${NAME}"'))

    def test_resource_chain_verifier_joins_each_owner_pair(self):
        script = (ROOT / "scripts/verify-resource-chain.sh").read_text()
        match = re.search(r"<<'PY' > \"\$TMP/instance-ids\"\n(.*?)\nPY", script, flags=re.S)
        self.assertIsNotNone(match)
        verifier = match.group(1)
        cluster_label = {"cluster.x-k8s.io/cluster-name": "service-a"}
        machine = {
            "metadata": {"name": "machine-1", "namespace": "service-a", "uid": "uid-1", "labels": cluster_label},
            "spec": {
                "providerID": "openstack:///instance-1",
                "infrastructureRef": {"apiGroup": "infrastructure.cluster.x-k8s.io", "kind": "OpenStackMachine", "name": "infra-1"},
            },
        }
        infrastructure = {
            "metadata": {
                "name": "infra-1", "namespace": "service-a", "labels": cluster_label,
                "ownerReferences": [{"kind": "Machine", "name": "machine-1", "uid": "uid-1", "controller": True}],
            },
            "status": {"instanceID": "instance-1"},
        }
        node = {
            "metadata": {"name": "node-1"},
            "spec": {"providerID": "openstack:///instance-1"},
            "status": {"conditions": [{"type": "Ready", "status": "True"}]},
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "machines.json").write_text(json.dumps({"items": [machine]}))
            (root / "openstackmachines.json").write_text(json.dumps({"items": [infrastructure]}))
            (root / "nodes.json").write_text(json.dumps({"items": [node]}))
            good = subprocess.run(["python3", "-", str(root), "service-a", "service-a"], input=verifier, text=True, capture_output=True)
            self.assertEqual(good.returncode, 0, good.stderr)
            self.assertEqual(good.stdout.strip(), "instance-1")
            infrastructure["metadata"]["ownerReferences"][0]["uid"] = "wrong-owner"
            (root / "openstackmachines.json").write_text(json.dumps({"items": [infrastructure]}))
            bad = subprocess.run(["python3", "-", str(root), "service-a", "service-a"], input=verifier, text=True, capture_output=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn("controller ownerReference", bad.stderr)

    def test_argocd_registration_rolls_back_new_child_credentials_on_failure(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            call_log = root / "kubectl.log"
            fake_kubectl = fake_bin / "kubectl"
            fake_kubectl.write_text(
                "#!/usr/bin/env bash\n"
                "set -u\n"
                "printf '%s\\n' \"$*\" >> \"$KUBECTL_LOG\"\n"
                "if [[ \" $* \" == *\" config current-context\"* ]]; then [[ \" $* \" == *mgmt.kubeconfig* ]] && echo mgmt-context || echo child-context; exit 0; fi\n"
                "if [[ \" $* \" == *\" auth can-i \"* ]]; then echo yes; exit 0; fi\n"
                "if [[ \" $* \" == *\" -n argocd get secret cluster-service-a\"* ]]; then exit 1; fi\n"
                "if [[ \" $* \" == *\" create namespace \"* ]]; then printf 'apiVersion: v1\\nkind: Namespace\\nmetadata: {name: workload-demo}\\n'; exit 0; fi\n"
                "if [[ \" $* \" == *\" apply -f -\"* ]]; then cat >/dev/null; exit 0; fi\n"
                "if [[ \" $* \" == *\" get secret argocd-chapter-4-token \"* ]]; then printf dG9rZW4=; exit 0; fi\n"
                "if [[ \" $* \" == *\" config view \"* ]]; then printf '%s\\n' '{\"clusters\":[{\"cluster\":{\"server\":\"https://child.example\",\"certificate-authority-data\":\"Y2E=\"}}]}'; exit 0; fi\n"
                "if [[ \" $* \" == *mgmt.kubeconfig* && \" $* \" == *\" apply -f \"* ]]; then exit 42; fi\n"
                "exit 0\n"
            )
            fake_kubectl.chmod(0o755)
            mgmt = root / "mgmt.kubeconfig"
            child = root / "child.kubeconfig"
            mgmt.write_text("placeholder")
            child.write_text("placeholder")
            environment = os.environ.copy()
            environment["PATH"] = f"{fake_bin}:{environment['PATH']}"
            environment["KUBECTL_LOG"] = str(call_log)
            result = subprocess.run(
                [
                    str(ROOT / "scripts/register-argocd-cluster.sh"),
                    str(mgmt), "mgmt-context", str(child), "child-context",
                    "service-a", "workload", "workload-demo",
                ],
                text=True, capture_output=True, env=environment, check=False,
            )
            self.assertEqual(result.returncode, 42)
            calls = call_log.read_text()
            self.assertIn("delete secret cluster-service-a --ignore-not-found", calls)
            self.assertIn("delete rolebinding/argocd-chapter-4-manager role/argocd-chapter-4-manager --ignore-not-found", calls)
            self.assertIn("delete secret/argocd-chapter-4-token serviceaccount/argocd-chapter-4 --ignore-not-found", calls)

    def test_wait_timeout_fails_and_prints_diagnostics(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            fake_bin = Path(temporary_directory)
            call_log = fake_bin / "kubectl-calls.log"
            fake_kubectl = fake_bin / "kubectl"
            fake_kubectl.write_text(
                "#!/usr/bin/env bash\n"
                "printf '%s\\n' \"$*\" >> \"$KUBECTL_LOG\"\n"
                "if [[ \" $* \" == *\" wait \"* ]]; then exit 1; fi\n"
                "exit 0\n"
            )
            fake_kubectl.chmod(0o755)
            environment = os.environ.copy()
            environment["PATH"] = f"{fake_bin}:{environment['PATH']}"
            environment["KUBECTL_LOG"] = str(call_log)
            result = subprocess.run(
                [
                    str(ROOT / "scripts" / "wait-for-cluster.sh"),
                    "/tmp/example-kubeconfig",
                    "approved-context",
                    "service-a",
                    "service-a",
                    "1s",
                ],
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("did not reach Available", result.stderr)
            calls = call_log.read_text()
            self.assertIn("wait --for=condition=Available", calls)
            self.assertIn("openstackcluster,openstackmachine", calls)

    def test_base_manifests_have_pinned_api_contract(self):
        docs = [doc for doc in yaml.safe_load_all((ROOT / "manifests/base/clusterclass.yaml").read_text()) if doc]
        refs = {(doc["apiVersion"], doc["kind"]) for doc in docs}
        expected = {
            ("cluster.x-k8s.io/v1beta2", "ClusterClass"),
            ("controlplane.cluster.x-k8s.io/v1beta2", "KubeadmControlPlaneTemplate"),
            ("bootstrap.cluster.x-k8s.io/v1beta2", "KubeadmConfigTemplate"),
            ("infrastructure.cluster.x-k8s.io/v1beta1", "OpenStackClusterTemplate"),
            ("infrastructure.cluster.x-k8s.io/v1beta1", "OpenStackMachineTemplate"),
        }
        self.assertTrue(expected.issubset(refs))
        cluster_class = next(doc for doc in docs if doc["kind"] == "ClusterClass")
        variables = {item["name"] for item in cluster_class["spec"]["variables"]}
        self.assertEqual(variables, {"identityRef", "networkID", "subnetID", "apiVIP", "imageID", "controlPlaneFlavor", "workerFlavor", "availabilityZone", "sshKeyName", "securityGroupID"})

    def test_path_contract_defaults_to_not_tested_and_not_approved(self):
        contract = yaml.safe_load((ROOT / "hub-spoke-contract.example.yaml").read_text())
        self.assertTrue(contract["example_only"])
        self.assertFalse(contract["execution_approved"])
        self.assertEqual(contract["status"]["data_path"], "not-tested")

    def test_resource_id_fixture_cannot_pass_cleanup(self):
        record = json.loads((ROOT / "evidence/resource-ids.example.json").read_text())
        self.assertFalse(record["captured_before_deletion"])
        self.assertEqual(sum((record[key] for key in ("server_ids", "port_ids", "volume_ids", "loadbalancer_ids")), []), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
