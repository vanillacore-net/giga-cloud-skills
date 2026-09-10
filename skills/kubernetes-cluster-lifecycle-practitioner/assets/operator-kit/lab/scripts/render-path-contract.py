#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]


def kubectl_value(kubeconfig: Path, context: str, *args: str) -> str:
    result = subprocess.run(
        ["kubectl", "--kubeconfig", str(kubeconfig), "--context", context, *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def bind_target(kubeconfig: Path, context: str, role: str) -> tuple[str, str]:
    if not kubeconfig.is_file():
        raise ValueError(f"{role} kubeconfig is not readable: {kubeconfig}")
    current = kubectl_value(kubeconfig, context, "config", "current-context")
    if current != context:
        raise ValueError(f"{role} kubeconfig current context is {current}, expected {context}")
    api_server = kubectl_value(
        kubeconfig,
        context,
        "config", "view", "--minify", "-o", "jsonpath={.clusters[0].cluster.server}",
    )
    if not api_server.startswith("https://"):
        raise ValueError(f"{role} API server is not an HTTPS URL: {api_server}")
    return str(kubeconfig.resolve()), api_server


def main() -> int:
    parser = argparse.ArgumentParser(description="Bind a Chapter 4 path contract to two confirmed kubeconfig contexts")
    parser.add_argument("--source-kubeconfig", type=Path, required=True)
    parser.add_argument("--source-context", required=True)
    parser.add_argument("--destination-kubeconfig", type=Path, required=True)
    parser.add_argument("--destination-context", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        source_path, source_api = bind_target(args.source_kubeconfig, args.source_context, "source")
        destination_path, destination_api = bind_target(args.destination_kubeconfig, args.destination_context, "destination")
    except (ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    contract = yaml.safe_load((ROOT / "hub-spoke-contract.example.yaml").read_text(encoding="utf-8"))
    contract["source"].update(
        kubeconfig=source_path,
        context=args.source_context,
        api_server=source_api,
    )
    contract["destination"].update(
        kubeconfig=destination_path,
        context=args.destination_context,
        api_server=destination_api,
    )
    args.output.write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")
    print(f"Path contract written: {args.output}")
    print(f"source: loadbalancer | {args.source_context} | {source_api}")
    print(f"destination: service-a | {args.destination_context} | {destination_api}")
    print("Next: review the file, replace network evidence, set example_only=false and execution_approved=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
