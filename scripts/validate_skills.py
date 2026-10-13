#!/usr/bin/env python3
"""Validate the distributable GIGA learning-skill package."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
CONTRACT_PATH = ROOT / "learning-contract.json"
REQUIRED_FRONTMATTER = {
    "name",
    "description",
    "version",
    "author",
    "license",
    "platforms",
    "metadata",
}
BANNED_PATTERNS = {
    "internal editorial skill": r"decision-path-authoring|comparison-and-dependencies|causal-claim-and-term-integrity|modular-learning-package|cloud-product-control-pass",
    "private vault path": r"AI_Knowledge/|\.pi/secrets|forgejo-vanillacore",
    "private Notion path": r"notion\.com/p/",
    "machine-local home path": r"/home/[A-Za-z0-9._-]+/",
    "credential assignment": r"(?im)^[ \t]*(password|token|secret|private_key|auth_url)[ \t]*[:=][ \t]*[^<\s][^\n]*$",
}
SCAN_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py"}
errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
        return {}


def load_yaml(path: Path) -> object:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        fail(f"{path.relative_to(ROOT)}: invalid YAML: {exc}")
        return None


def frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(f"{path.relative_to(ROOT)}: frontmatter must start at byte 0")
        return {}, text
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        fail(f"{path.relative_to(ROOT)}: missing frontmatter terminator")
        return {}, text
    try:
        data = yaml.safe_load(parts[0][4:])
    except yaml.YAMLError as exc:
        fail(f"{path.relative_to(ROOT)}: invalid frontmatter YAML: {exc}")
        return {}, parts[1]
    if not isinstance(data, dict):
        fail(f"{path.relative_to(ROOT)}: frontmatter is not a mapping")
        return {}, parts[1]
    return data, parts[1]


contract = load_json(CONTRACT_PATH)
expected_skills = set(contract.get("expected_skills", []))
actual_skills = {path.name for path in SKILLS.iterdir() if path.is_dir()}
if expected_skills != actual_skills:
    fail(
        "skill inventory mismatch: "
        f"missing={sorted(expected_skills - actual_skills)}, "
        f"unexpected={sorted(actual_skills - expected_skills)}"
    )

manifests = [ROOT / ".claude-plugin" / "plugin.json", ROOT / ".codex-plugin" / "plugin.json"]
manifest_data = [load_json(path) for path in manifests]
for path, data in zip(manifests, manifest_data):
    for key in ("name", "version", "description"):
        if not data.get(key):
            fail(f"{path.relative_to(ROOT)}: missing {key}")
if len(manifest_data) == 2:
    if manifest_data[0].get("version") != manifest_data[1].get("version"):
        fail("plugin manifest versions differ")
    if manifest_data[1].get("skills") != "./skills/":
        fail(".codex-plugin/plugin.json: skills must be ./skills/")
    if manifest_data[1].get("version") != contract.get("package_version"):
        fail("plugin and learning-contract versions differ")

skill_frontmatter: dict[str, dict] = {}
for name in sorted(actual_skills):
    folder = SKILLS / name
    spec = folder / "SKILL.md"
    metadata_path = folder / "agents" / "openai.yaml"
    if not spec.exists():
        fail(f"{name}: missing SKILL.md")
        continue
    data, body = frontmatter(spec)
    skill_frontmatter[name] = data
    missing = REQUIRED_FRONTMATTER - set(data)
    if missing:
        fail(f"{name}: missing frontmatter keys: {', '.join(sorted(missing))}")
    if data.get("name") != name:
        fail(f"{name}: frontmatter name does not match directory")
    description = data.get("description")
    if not isinstance(description, str) or not description.endswith(".") or len(description) > 60:
        fail(f"{name}: description must be one sentence of at most 60 characters")
    if not isinstance(data.get("platforms"), list) or not data.get("platforms"):
        fail(f"{name}: platforms must be a non-empty list")
    if not isinstance(data.get("metadata"), dict) or not data["metadata"].get("provider"):
        fail(f"{name}: metadata.provider is required by the Skills Marketplace")
    hermes = data.get("metadata", {}).get("hermes", {}) if isinstance(data.get("metadata"), dict) else {}
    if not isinstance(hermes.get("tags"), list) or not hermes.get("tags"):
        fail(f"{name}: metadata.hermes.tags must be a non-empty list")
    related = hermes.get("related_skills", [])
    if not isinstance(related, list):
        fail(f"{name}: related_skills must be a list")
    else:
        for sibling in related:
            if sibling not in actual_skills:
                fail(f"{name}: unknown related skill {sibling}")
    if not body.strip():
        fail(f"{name}: empty instructions")
    lowered_body = body.casefold()
    if "challenge" not in lowered_body or "attempt" not in lowered_body or "stop before" not in lowered_body:
        fail(f"{name}: challenge mode must hold correction until a learner attempt")
    if "## When to use" not in body and "## When to Use" not in body:
        fail(f"{name}: missing distinct When to use section")
    if "## Verification" not in body:
        fail(f"{name}: missing Verification section")
    if not metadata_path.exists():
        fail(f"{name}: missing agents/openai.yaml")
    else:
        metadata = load_yaml(metadata_path)
        if not isinstance(metadata, dict) or not metadata.get("interface", {}).get("display_name"):
            fail(f"{name}: Codex metadata lacks interface.display_name")

    for ref in re.findall(r"`references/([A-Za-z0-9_./-]+\.md)`", body):
        if not (folder / "references" / ref).exists():
            fail(f"{name}: missing referenced file references/{ref}")

for chapter, spec in contract.get("chapters", {}).items():
    names = [spec.get("primary_skill"), *spec.get("supporting_skills", [])]
    for name in names:
        if name not in actual_skills:
            fail(f"Chapter {chapter}: unknown skill {name}")
    output = spec.get("output")
    primary_path = SKILLS / str(spec.get("primary_skill")) / "SKILL.md"
    if output and primary_path.exists() and output not in primary_path.read_text(encoding="utf-8"):
        fail(f"Chapter {chapter}: primary skill does not name output {output}")
    if not spec.get("routing_keywords") or not spec.get("coverage_terms") or not spec.get("challenge_checks"):
        fail(f"Chapter {chapter}: incomplete route or coverage contract")

handoff_doc = (ROOT / "docs" / "handoff-contracts.md").read_text(encoding="utf-8")
for output in contract.get("handoff_order", []):
    if output not in handoff_doc:
        fail(f"docs/handoff-contracts.md: missing {output}")
for axis in contract.get("review_axes", []):
    if axis not in handoff_doc:
        fail(f"docs/handoff-contracts.md: missing review axis {axis}")

for path in ROOT.rglob("*"):
    if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
        continue
    if path.resolve() == Path(__file__).resolve():
        continue
    if path.suffix not in SCAN_SUFFIXES:
        continue
    text = path.read_text(encoding="utf-8")
    for label, pattern in BANNED_PATTERNS.items():
        if re.search(pattern, text):
            fail(f"{path.relative_to(ROOT)}: prohibited {label}")

if errors:
    print("VALIDATION FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print(
    "VALIDATION PASSED: "
    f"{len(actual_skills)} skills, {len(contract.get('chapters', {}))} chapter contracts, "
    f"{len(manifests)} plugin manifests"
)
