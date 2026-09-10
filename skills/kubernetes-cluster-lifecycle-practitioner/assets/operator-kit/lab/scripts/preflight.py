#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from lablib import load_yaml, validate_environment


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Chapter 4 environment contract without contacting OpenStack.")
    parser.add_argument("contract", type=Path)
    parser.add_argument("--allow-example", action="store_true", help="permit the checked-in placeholder example for offline package tests")
    args = parser.parse_args()

    contract = load_yaml(args.contract)
    errors = validate_environment(contract, require_live=not args.allow_example)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 2

    clusters = ", ".join(item["name"] for item in contract["clusters"])
    mode = "example" if args.allow_example else "live"
    print(f"environment contract valid ({mode} mode): {clusters}; CIDRs do not overlap")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
