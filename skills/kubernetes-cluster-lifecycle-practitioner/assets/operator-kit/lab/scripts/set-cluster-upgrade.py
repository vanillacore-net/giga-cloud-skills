#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re
import uuid

import yaml


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Set a per-cluster Kubernetes version and machine image in a Chapter 4 contract"
    )
    parser.add_argument("contract", type=Path)
    parser.add_argument("cluster")
    parser.add_argument("kubernetes_version")
    parser.add_argument("image_id")
    args = parser.parse_args()

    if not re.fullmatch(r"v[1-9][0-9]*\.[0-9]+\.[0-9]+", args.kubernetes_version):
        parser.error("kubernetes_version must be an explicit release such as v1.37.1")
    try:
        image_id = uuid.UUID(args.image_id)
    except ValueError:
        parser.error("image_id must be a Glance image UUID")
    if image_id.int == 0:
        parser.error("image_id must not be the all-zero documentation UUID")

    contract = yaml.safe_load(args.contract.read_text(encoding="utf-8"))
    clusters = contract.get("clusters", [])
    selected = [cluster for cluster in clusters if cluster.get("name") == args.cluster]
    if len(selected) != 1:
        parser.error(f"contract must contain exactly one cluster named {args.cluster}")

    selected[0]["kubernetes_version"] = args.kubernetes_version
    selected[0]["image_id"] = str(image_id)
    args.contract.write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
