#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

import yaml

from lablib import (
    load_yaml,
    render_addon_resources,
    render_cluster,
    render_storage_resources,
    validate_environment,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Chapter 4 Cluster API declarations")
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "rendered")
    parser.add_argument("--allow-example", action="store_true", help="render documentation fixtures only")
    args = parser.parse_args()

    contract = load_yaml(args.contract)
    errors = validate_environment(contract, require_live=not args.allow_example)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    args.output.mkdir(parents=True, exist_ok=True)
    addon_output = args.output / "addons"
    addon_output.mkdir(parents=True, exist_ok=True)
    versions = load_yaml(ROOT / "VERSIONS.yaml")
    storage_path = ROOT / "addons/local-path-provisioner/v0.0.37.yaml"
    storage_manifest = storage_path.read_text(encoding="utf-8")
    expected_hash = versions["local_path_provisioner"]["manifest_sha256"]
    actual_hash = hashlib.sha256(storage_path.read_bytes()).hexdigest()
    if actual_hash != expected_hash:
        print(f"ERROR: local-path manifest hash mismatch: {actual_hash}", file=sys.stderr)
        return 2
    addon_inputs = (
        (
            "cert-manager",
            ROOT / "addons/cert-manager/v1.20.3.yaml",
            versions["cert_manager_manifest_sha256"],
            "lab.example.invalid/certificate-baseline",
            "cert-manager",
        ),
        (
            "contour",
            ROOT / "addons/contour/v1.33.7.yaml",
            versions["contour"]["manifest_sha256"],
            "lab.example.invalid/ingress-baseline",
            "contour",
        ),
    )
    verified_addons = []
    for addon_name, addon_path, addon_hash, selector_label, selector_value in addon_inputs:
        actual_hash = hashlib.sha256(addon_path.read_bytes()).hexdigest()
        if actual_hash != addon_hash:
            print(f"ERROR: {addon_name} manifest hash mismatch: {actual_hash}", file=sys.stderr)
            return 2
        addon_manifest = addon_path.read_text(encoding="utf-8")
        if addon_name == "contour":
            contour_objects = [item for item in yaml.safe_load_all(addon_manifest) if item]
            envoy_services = [
                item for item in contour_objects
                if item.get("kind") == "Service"
                and item.get("metadata", {}).get("namespace") == "projectcontour"
                and item.get("metadata", {}).get("name") == "envoy"
            ]
            if len(envoy_services) != 1:
                print("ERROR: Contour payload must define exactly one projectcontour/envoy Service", file=sys.stderr)
                return 2
            envoy_service = envoy_services[0]
            if (
                envoy_service.get("spec", {}).get("type") != "ClusterIP"
                or "externalTrafficPolicy" in envoy_service.get("spec", {})
                or envoy_service.get("metadata", {}).get("annotations")
            ):
                print("ERROR: Chapter 4 Envoy Service must be private ClusterIP without external load-balancer settings", file=sys.stderr)
                return 2
        verified_addons.append(
            (addon_name, addon_manifest, selector_label, selector_value)
        )
    for overlay_path in sorted((ROOT / "overlays").glob("*.yaml")):
        overlay = load_yaml(overlay_path)
        document = render_cluster(contract, overlay)
        output = args.output / f"{document['metadata']['name']}.yaml"
        output.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
        print(output)
        storage_documents = render_storage_resources(contract, overlay, storage_manifest)
        storage_output = addon_output / f"{document['metadata']['name']}-storage.yaml"
        storage_output.write_text(
            yaml.safe_dump_all(storage_documents, sort_keys=False), encoding="utf-8"
        )
        print(storage_output)
        for addon_name, addon_manifest, selector_label, selector_value in verified_addons:
            addon_documents = render_addon_resources(
                contract,
                overlay,
                addon_manifest,
                addon_name=addon_name,
                selector_label=selector_label,
                selector_value=selector_value,
            )
            addon_path = addon_output / f"{document['metadata']['name']}-{addon_name}.yaml"
            addon_path.write_text(
                yaml.safe_dump_all(addon_documents, sort_keys=False), encoding="utf-8"
            )
            print(addon_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
