#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True)


def ids(rows: list[dict]) -> set[str]:
    values: set[str] = set()
    for row in rows:
        value = row.get("ID") or row.get("Id") or row.get("id") or row.get("Volume ID")
        if value:
            values.add(str(value))
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture stable OpenStack IDs before deleting a CAPI-owned cluster.")
    parser.add_argument("kubeconfig")
    parser.add_argument("context")
    parser.add_argument("namespace")
    parser.add_argument("cluster")
    parser.add_argument("os_cloud")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if os.environ.get("CONFIRM_MANAGEMENT_CONTEXT") != args.context:
        raise SystemExit(f"set CONFIRM_MANAGEMENT_CONTEXT={args.context}")

    kubectl = ["kubectl", "--kubeconfig", args.kubeconfig, "--context", args.context, "-n", args.namespace]
    cluster = json.loads(run(*kubectl, "get", "cluster", args.cluster, "-o", "json"))
    machines = json.loads(run(*kubectl, "get", "openstackmachines.infrastructure.cluster.x-k8s.io", "-o", "json"))["items"]
    machines = [item for item in machines if item.get("metadata", {}).get("labels", {}).get("cluster.x-k8s.io/cluster-name") == args.cluster]
    server_ids = {item.get("status", {}).get("instanceID") for item in machines} - {None}
    if not server_ids:
        raise SystemExit("no OpenStackMachine instance IDs found; do not delete without pre-deletion evidence")

    port_ids: set[str] = set()
    volume_ids: set[str] = set()
    for server_id in server_ids:
        port_ids |= ids(json.loads(run("openstack", "--os-cloud", args.os_cloud, "port", "list", "--server", server_id, "-f", "json")))
        volume_ids |= ids(json.loads(run("openstack", "--os-cloud", args.os_cloud, "server", "volume", "list", server_id, "-f", "json")))

    infra_name = cluster["spec"]["infrastructureRef"]["name"]
    infra = json.loads(run(*kubectl, "get", "openstackcluster.infrastructure.cluster.x-k8s.io", infra_name, "-o", "json"))
    vip = infra.get("spec", {}).get("apiServerFixedIP") or infra.get("spec", {}).get("controlPlaneEndpoint", {}).get("host")
    if not vip:
        raise SystemExit("OpenStackCluster has no API VIP to identify its API load balancer")
    loadbalancer_ids = ids(json.loads(run("openstack", "--os-cloud", args.os_cloud, "loadbalancer", "list", "--vip-address", vip, "-f", "json")))
    if not loadbalancer_ids:
        raise SystemExit(f"no API load balancer found for VIP {vip}")

    record = {
        "cluster": args.cluster,
        "namespace": args.namespace,
        "captured_before_deletion": True,
        "server_ids": sorted(server_ids),
        "port_ids": sorted(port_ids),
        "volume_ids": sorted(volume_ids),
        "loadbalancer_ids": sorted(loadbalancer_ids),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + "\n")
    args.output.chmod(0o600)
    print(f"captured {len(server_ids)} servers, {len(port_ids)} ports, {len(volume_ids)} volumes and {len(loadbalancer_ids)} API load balancers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
