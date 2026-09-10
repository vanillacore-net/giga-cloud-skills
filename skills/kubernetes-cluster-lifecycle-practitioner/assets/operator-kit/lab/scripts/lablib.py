from __future__ import annotations

import ipaddress
from pathlib import Path
import re
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER_PREFIXES = ("REPLACE_", "placeholder")
ZERO_UUID_PREFIX = "00000000-0000-0000-0000-"


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a YAML mapping in {path}")
    return value


def _is_placeholder(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return value.startswith(PLACEHOLDER_PREFIXES) or value.startswith(ZERO_UUID_PREFIX)


def validate_environment(contract: dict[str, Any], require_live: bool) -> list[str]:
    errors: list[str] = []
    lab = contract.get("lab", {})
    cloud = contract.get("openstack", {})
    clusters = contract.get("clusters", [])

    if require_live and lab.get("example_only") is not False:
        errors.append("example contract cannot be used for a live operation")
    if len(clusters) != 2:
        errors.append("contract must describe exactly the loadbalancer and service-a clusters")

    paths = {
        "openstack.credential_secret_name": cloud.get("credential_secret_name"),
        "openstack.image_id": cloud.get("image_id"),
        "openstack.control_plane_flavor": cloud.get("control_plane_flavor"),
        "openstack.worker_flavor": cloud.get("worker_flavor"),
        "openstack.availability_zone": cloud.get("availability_zone"),
        "openstack.ssh_key_name": cloud.get("ssh_key_name"),
        "openstack.security_group_id": cloud.get("security_group_id"),
    }
    for cluster in clusters:
        name = cluster.get("name", "unnamed")
        for key in ("network_id", "subnet_id"):
            paths[f"clusters.{name}.{key}"] = cluster.get(key)
        if "image_id" in cluster:
            paths[f"clusters.{name}.image_id"] = cluster.get("image_id")

    if require_live:
        for path, value in paths.items():
            if not value or _is_placeholder(value):
                errors.append(f"live contract has unresolved value: {path}")

    networks: list[tuple[str, ipaddress._BaseNetwork]] = []
    for path, value in (
        ("lab.management_cidr", lab.get("management_cidr")),
        ("lab.management_pod_cidr", lab.get("management_pod_cidr")),
        ("lab.management_service_cidr", lab.get("management_service_cidr")),
        ("lab.transit_cidr", lab.get("transit_cidr")),
    ):
        try:
            networks.append((path, ipaddress.ip_network(value, strict=True)))
        except Exception:
            errors.append(f"invalid CIDR: {path}")

    seen_names: set[str] = set()
    for cluster in clusters:
        name = cluster.get("name")
        if not name or name in seen_names:
            errors.append(f"duplicate or missing cluster name: {name}")
            continue
        seen_names.add(name)
        if cluster.get("role") != name:
            errors.append(f"cluster role must equal its reviewed overlay name: {name}")
        version = cluster.get("kubernetes_version")
        if version is not None and not re.fullmatch(r"v[1-9][0-9]*\.[0-9]+\.[0-9]+", str(version)):
            errors.append(f"invalid Kubernetes version: clusters.{name}.kubernetes_version")
        local_networks: dict[str, ipaddress._BaseNetwork] = {}
        for key in ("node_cidr", "pod_cidr", "service_cidr"):
            try:
                network = ipaddress.ip_network(cluster.get(key), strict=True)
                local_networks[key] = network
                networks.append((f"clusters.{name}.{key}", network))
            except Exception:
                errors.append(f"invalid CIDR: clusters.{name}.{key}")
        try:
            vip = ipaddress.ip_address(cluster.get("api_vip"))
            if "node_cidr" in local_networks and vip not in local_networks["node_cidr"]:
                errors.append(f"API VIP for {name} is outside its node CIDR")
        except Exception:
            errors.append(f"invalid API VIP: clusters.{name}.api_vip")
        for key in ("control_plane_replicas", "worker_replicas"):
            value = cluster.get(key)
            if not isinstance(value, int) or value < 1:
                errors.append(f"{name}.{key} must be a positive integer")

    for index, (first_name, first) in enumerate(networks):
        for second_name, second in networks[index + 1 :]:
            if first.version == second.version and first.overlaps(second):
                errors.append(f"CIDR overlap: {first_name} {first} and {second_name} {second}")
    return errors


def render_cluster(contract: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    requested = overlay.get("cluster")
    cluster = next((item for item in contract["clusters"] if item["name"] == requested), None)
    if cluster is None:
        raise ValueError(f"overlay refers to unknown cluster: {requested}")
    cloud = contract["openstack"]
    versions = load_yaml(ROOT / "VERSIONS.yaml")
    kubernetes_version = cluster.get("kubernetes_version", versions["kubernetes"])
    image_id = cluster.get("image_id", cloud["image_id"])
    identity_ref = {
        "type": "Secret",
        "name": cloud["credential_secret_name"],
        "cloudName": cloud["cloud_name"],
        "region": cloud["region"],
    }
    variables = [
        {"name": "identityRef", "value": identity_ref},
        {"name": "networkID", "value": cluster["network_id"]},
        {"name": "subnetID", "value": cluster["subnet_id"]},
        {"name": "apiVIP", "value": cluster["api_vip"]},
        {"name": "imageID", "value": image_id},
        {"name": "controlPlaneFlavor", "value": cloud["control_plane_flavor"]},
        {"name": "workerFlavor", "value": cloud["worker_flavor"]},
        {"name": "availabilityZone", "value": cloud["availability_zone"]},
        {"name": "sshKeyName", "value": cloud["ssh_key_name"]},
        {"name": "securityGroupID", "value": cloud["security_group_id"]},
    ]
    return {
        "apiVersion": "cluster.x-k8s.io/v1beta2",
        "kind": "Cluster",
        "metadata": {
            "name": cluster["name"],
            "namespace": cluster["namespace"],
            "labels": {
                "lab.example.invalid/managed-by": "chapter4-capi-openstack-lab",
                "lab.example.invalid/role": cluster["role"],
                "lab.example.invalid/storage-baseline": "local-path",
                "lab.example.invalid/certificate-baseline": "cert-manager",
                "lab.example.invalid/ingress-baseline": "contour",
            },
            "annotations": {
                "lab.example.invalid/ownership-token": contract["lab"]["ownership_token"],
            },
        },
        "spec": {
            "clusterNetwork": {
                "pods": {"cidrBlocks": [cluster["pod_cidr"]]},
                "services": {"cidrBlocks": [cluster["service_cidr"]]},
            },
            "topology": {
                "classRef": {"name": "openstack-runtime", "namespace": "capi-lab-blueprints"},
                "version": kubernetes_version,
                "controlPlane": {"replicas": cluster["control_plane_replicas"]},
                "workers": {
                    "machineDeployments": [
                        {
                            "class": "general-worker",
                            "name": "workers",
                            "replicas": cluster["worker_replicas"],
                            "failureDomain": cloud["availability_zone"],
                        }
                    ]
                },
                "variables": variables,
            },
        },
    }


def render_storage_resources(
    contract: dict[str, Any], overlay: dict[str, Any], manifest: str
) -> list[dict[str, Any]]:
    requested = overlay.get("cluster")
    cluster = next((item for item in contract["clusters"] if item["name"] == requested), None)
    if cluster is None:
        raise ValueError(f"overlay refers to unknown cluster: {requested}")
    namespace = cluster["namespace"]
    selector = {"lab.example.invalid/storage-baseline": "local-path"}
    managed_labels = {
        "lab.example.invalid/managed-by": "chapter4-capi-openstack-lab",
        "lab.example.invalid/addon": "local-path-storage",
    }
    config_map = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": "local-path-storage",
            "namespace": namespace,
            "labels": managed_labels,
        },
        "data": {"local-path-storage.yaml": manifest},
    }
    resource_set = {
        "apiVersion": "addons.cluster.x-k8s.io/v1beta2",
        "kind": "ClusterResourceSet",
        "metadata": {
            "name": "local-path-storage",
            "namespace": namespace,
            "labels": managed_labels,
        },
        "spec": {
            "strategy": "Reconcile",
            "clusterSelector": {"matchLabels": selector},
            "resources": [{"name": "local-path-storage", "kind": "ConfigMap"}],
        },
    }
    return [config_map, resource_set]


def render_addon_resources(
    contract: dict[str, Any],
    overlay: dict[str, Any],
    manifest: str,
    *,
    addon_name: str,
    selector_label: str,
    selector_value: str,
    max_payload_bytes: int = 600_000,
) -> list[dict[str, Any]]:
    requested = overlay.get("cluster")
    cluster = next((item for item in contract["clusters"] if item["name"] == requested), None)
    if cluster is None:
        raise ValueError(f"overlay refers to unknown cluster: {requested}")

    documents = [item.strip() for item in manifest.split("\n---") if item.strip()]
    if not documents:
        raise ValueError(f"{addon_name} manifest contains no Kubernetes resources")
    chunks: list[str] = []
    current: list[str] = []
    for document in documents:
        candidate = "\n---\n".join([*current, document]) + "\n"
        if current and len(candidate.encode("utf-8")) > max_payload_bytes:
            chunks.append("\n---\n".join(current) + "\n")
            current = [document]
        else:
            current.append(document)
    if current:
        chunks.append("\n---\n".join(current) + "\n")
    if any(len(chunk.encode("utf-8")) > max_payload_bytes for chunk in chunks):
        raise ValueError(f"one {addon_name} manifest document exceeds the payload limit")

    namespace = cluster["namespace"]
    managed_labels = {
        "lab.example.invalid/managed-by": "chapter4-capi-openstack-lab",
        "lab.example.invalid/addon": addon_name,
    }
    config_maps = []
    for index, chunk in enumerate(chunks, 1):
        name = addon_name if len(chunks) == 1 else f"{addon_name}-{index:02d}"
        config_maps.append(
            {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {"name": name, "namespace": namespace, "labels": managed_labels},
                "data": {f"{addon_name}.yaml": chunk},
            }
        )
    resource_set = {
        "apiVersion": "addons.cluster.x-k8s.io/v1beta2",
        "kind": "ClusterResourceSet",
        "metadata": {"name": addon_name, "namespace": namespace, "labels": managed_labels},
        "spec": {
            "strategy": "Reconcile",
            "clusterSelector": {"matchLabels": {selector_label: selector_value}},
            "resources": [
                {"name": item["metadata"]["name"], "kind": "ConfigMap"}
                for item in config_maps
            ],
        },
    }
    return [*config_maps, resource_set]
