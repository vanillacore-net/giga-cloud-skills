#!/usr/bin/env python3
"""Validate the flat Chapter 3 environment contract without reading credentials."""
from __future__ import annotations
import argparse
import ipaddress
import re
import sys
import uuid
from pathlib import Path

REQUIRED = {
    "schema", "example_only", "cloud_profile", "project_name", "vm_name",
    "security_group_name", "image_name", "image_id", "flavor_name",
    "vm_network_name", "floating_ip_network_name", "approved_https_cidr",
    "volume_name", "volume_type", "volume_size_gib",
    "compute_availability_zone", "volume_availability_zone",
}
FORBIDDEN_PARTS = ("password", "secret", "token", "auth_url", "private_key")

def parse_flat_yaml(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-") or ":" not in line:
            raise ValueError(f"line {number}: expected a flat key: value entry")
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if not key or not value:
            raise ValueError(f"line {number}: empty key or value")
        if key in values:
            raise ValueError(f"line {number}: duplicate key {key}")
        values[key] = value
    return values

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", type=Path)
    parser.add_argument("--allow-example", action="store_true")
    args = parser.parse_args()
    try:
        values = parse_flat_yaml(args.contract)
        missing = REQUIRED - values.keys()
        extra = values.keys() - REQUIRED
        if missing or extra:
            raise ValueError(f"missing={sorted(missing)} extra={sorted(extra)}")
        if values["schema"] != "chapter-3-environment/v1":
            raise ValueError("unsupported schema")
        is_example = values["example_only"].lower()
        if is_example not in {"true", "false"}:
            raise ValueError("example_only must be true or false")
        if is_example == "true" and not args.allow_example:
            raise ValueError("example contract refused for live use")
        uuid.UUID(values["image_id"])
        network = ipaddress.ip_network(values["approved_https_cidr"], strict=True)
        if network.version != 4:
            raise ValueError("approved_https_cidr must be IPv4")
        if int(values["volume_size_gib"]) <= 0:
            raise ValueError("volume_size_gib must be positive")
        for key, value in values.items():
            if any(part in key.lower() for part in FORBIDDEN_PARTS):
                raise ValueError(f"credential-like key is forbidden: {key}")
            if not re.search(r"\S", value):
                raise ValueError(f"empty value: {key}")
    except (OSError, ValueError) as exc:
        print(f"preflight failed: {exc}", file=sys.stderr)
        return 1
    print(f"preflight passed: {args.contract}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
