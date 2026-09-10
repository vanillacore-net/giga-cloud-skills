#!/usr/bin/env python3
"""Validate the portable Chapter 3 and Chapter 4 operator kits."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "learning-contract.json").read_text(encoding="utf-8"))
ERRORS: list[str] = []

REQUIRED = {
    "3": {
        "lab/README.md",
        "lab/VERSIONS.yaml",
        "lab/environment-contract.example.yaml",
        "lab/scripts/offline-validate.sh",
        "lab/scripts/preflight.py",
        "lab/scripts/verify-resource-chain.sh",
        "lab/scripts/verify-absence.sh",
        "lab/opentofu/main.tf",
        "lab/walkthroughs/01-discovery.md",
        "lab/walkthroughs/07-cleanup.md",
        "SOURCE.md",
        "MANIFEST.sha256",
    },
    "4": {
        "lab/README.md",
        "lab/VERSIONS.yaml",
        "lab/environment-contract.example.yaml",
        "lab/hub-spoke-contract.example.yaml",
        "lab/lab-session.env.example",
        "lab/addons/cert-manager/v1.20.3.yaml",
        "lab/addons/contour/v1.33.7.yaml",
        "lab/addons/local-path-provisioner/v0.0.37.yaml",
        "lab/scripts/offline-validate.sh",
        "lab/scripts/preflight.py",
        "lab/scripts/preflight-readonly.sh",
        "lab/scripts/install-providers.sh",
        "lab/scripts/install-management-ingress.sh",
        "lab/scripts/render-manifests.py",
        "lab/scripts/render-path-contract.py",
        "lab/scripts/scale-workers.sh",
        "lab/scripts/upgrade-cluster.sh",
        "lab/scripts/install-argocd.sh",
        "lab/scripts/cleanup.sh",
        "lab/foundation/opentofu/bootstrap/main.tf",
        "lab/foundation/ansible/seed.yaml",
        "lab/manifests/base/clusterclass.yaml",
        "lab/manifests/probe/storage-smoke.yaml",
        "lab/walkthroughs/01-discovery.md",
        "lab/walkthroughs/09-cleanup.md",
        "SOURCE.md",
        "THIRD_PARTY_NOTICES.md",
        "MANIFEST.sha256",
    },
}


def fail(message: str) -> None:
    ERRORS.append(message)


def verify_manifest(kit: Path) -> None:
    manifest = kit / "MANIFEST.sha256"
    if not manifest.is_file():
        fail(f"{kit.relative_to(ROOT)}: missing MANIFEST.sha256")
        return
    seen: set[Path] = set()
    for number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            fail(f"{manifest.relative_to(ROOT)}:{number}: invalid checksum line")
            continue
        expected, relative = match.groups()
        path = kit / relative
        seen.add(path)
        if not path.is_file():
            fail(f"{manifest.relative_to(ROOT)}: missing {relative}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            fail(f"{manifest.relative_to(ROOT)}: checksum mismatch for {relative}")
    actual_files = {p for p in kit.rglob("*") if p.is_file() and p != manifest and "__pycache__" not in p.parts}
    if actual_files != seen:
        missing = sorted(str(p.relative_to(kit)) for p in actual_files - seen)
        stale = sorted(str(p.relative_to(kit)) for p in seen - actual_files)
        fail(f"{manifest.relative_to(ROOT)}: inventory mismatch missing={missing} stale={stale}")


def verify_local_links(kit: Path) -> None:
    for source in kit.rglob("*.md"):
        text = source.read_text(encoding="utf-8")
        for raw in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            target = raw.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            resolved = (source.parent / target).resolve()
            if not resolved.exists():
                fail(f"{source.relative_to(ROOT)}: unresolved local link {raw}")


def verify_static_files(kit: Path) -> None:
    for path in kit.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        if path.suffix == ".py":
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
            except SyntaxError as exc:
                fail(f"{path.relative_to(ROOT)}: Python syntax error: {exc}")
        elif path.suffix in {".yaml", ".yml"}:
            try:
                list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
            except yaml.YAMLError as exc:
                fail(f"{path.relative_to(ROOT)}: YAML parse error: {exc}")
        elif path.suffix == ".sh":
            result = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
            if result.returncode:
                fail(f"{path.relative_to(ROOT)}: shell parse failed: {result.stderr.strip()}")


def run_offline(kit: Path) -> None:
    try:
        with tempfile.TemporaryDirectory(prefix="giga-operator-pycache-") as pycache:
            env = os.environ.copy()
            env["PYTHONPYCACHEPREFIX"] = pycache
            result = subprocess.run(
                ["bash", "scripts/offline-validate.sh"],
                cwd=kit / "lab",
                env=env,
                capture_output=True,
                text=True,
                timeout=360,
            )
    except (OSError, subprocess.TimeoutExpired) as exc:
        fail(f"{kit.relative_to(ROOT)}: offline validation could not complete: {exc}")
        return
    if result.returncode:
        fail(
            f"{kit.relative_to(ROOT)}: offline validation failed\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def main() -> None:
    workflows = CONTRACT.get("operator_workflows", {})
    if workflows.get("operations") != ["assess", "prepare", "provision", "validate", "maintain", "cleanup"]:
        fail("learning-contract.json: operator operation order is incomplete")
    if workflows.get("execution_levels") != ["explain", "prepare", "execute"]:
        fail("learning-contract.json: execution levels are incomplete")

    for chapter, spec in workflows.get("chapters", {}).items():
        kit = ROOT / spec["kit"]
        if not kit.is_dir():
            fail(f"Chapter {chapter}: missing operator kit {spec['kit']}")
            continue
        for relative in REQUIRED.get(chapter, set()):
            if not (kit / relative).is_file():
                fail(f"Chapter {chapter}: missing required operator file {relative}")
        source_path = kit / "SOURCE.md"
        if source_path.is_file():
            source = source_path.read_text(encoding="utf-8")
            if spec["source_commit"] not in source:
                fail(f"Chapter {chapter}: source commit absent from SOURCE.md")
        combined = "\n".join(
            path.read_text(encoding="utf-8", errors="replace")
            for path in kit.rglob("*")
            if path.is_file() and path.suffix in {".md", ".py", ".sh", ".yaml", ".yml", ".tf"}
        )
        if "git rev-parse --show-toplevel)/chapter-" in combined:
            fail(f"Chapter {chapter}: repository-root execution assumption remains")
        verify_manifest(kit)
        verify_local_links(kit)
        verify_static_files(kit)
        run_offline(kit)

    for chapter in ("3", "4"):
        spec = CONTRACT["operator_workflows"]["chapters"][chapter]
        skill = (ROOT / "skills" / spec["skill"] / "SKILL.md").read_text(encoding="utf-8")
        for marker in ("assets/operator-kit/", "protected working directory", "execution: execute", "explicit operation approval"):
            if marker not in skill:
                fail(f"Chapter {chapter}: practitioner lacks operator marker {marker!r}")

    if ERRORS:
        print("OPERATOR KIT TESTS FAILED")
        for error in ERRORS:
            print(f"- {error}")
        raise SystemExit(1)

    print("OPERATOR KIT TESTS PASSED: 2 kits, 6 operations, checksums and offline validation")


if __name__ == "__main__":
    main()
