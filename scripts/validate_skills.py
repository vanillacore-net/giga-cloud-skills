#!/usr/bin/env python3
"""Validate published agent skills and reject internal Hermes content."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
REQUIRED = {"name", "description", "version", "metadata"}
for manifest in [ROOT / ".claude-plugin" / "plugin.json", ROOT / ".codex-plugin" / "plugin.json"]:
    if not manifest.exists():
        raise SystemExit(f"VALIDATION FAILED\n- missing plugin manifest: {manifest.relative_to(ROOT)}")
    if '"name"' not in manifest.read_text() or '"version"' not in manifest.read_text():
        raise SystemExit(f"VALIDATION FAILED\n- malformed plugin manifest: {manifest.relative_to(ROOT)}")
BANNED = [
    r"decision-path-authoring", r"comparison-and-dependencies",
    r"causal-claim-and-term-integrity", r"modular-learning-package",
    r"cloud-product-control-pass", r"AI_Knowledge/", r"notion\.com/p/",
    r"forgejo-vanillacore", r"\.pi/secrets",
]
errors = []
for skill in sorted(SKILLS.iterdir()):
    if not skill.is_dir():
        continue
    spec = skill / "SKILL.md"
    metadata = skill / "agents" / "openai.yaml"
    if not spec.exists():
        errors.append(f"{skill.name}: missing SKILL.md")
        continue
    if not metadata.exists():
        errors.append(f"{skill.name}: missing Codex metadata")
    text = spec.read_text()
    if not text.startswith("---\n"):
        errors.append(f"{skill.name}: frontmatter must start at byte 0")
        continue
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        errors.append(f"{skill.name}: missing frontmatter terminator")
        continue
    front, body = parts
    keys = {m.group(1) for m in re.finditer(r"^([A-Za-z_][\w-]*):", front, re.M)}
    missing = REQUIRED - keys
    if missing:
        errors.append(f"{skill.name}: missing frontmatter keys: {', '.join(sorted(missing))}")
    if not body.strip():
        errors.append(f"{skill.name}: empty instructions")
    for pattern in BANNED:
        if re.search(pattern, text, re.I):
            errors.append(f"{skill.name}: prohibited marker: {pattern}")
if errors:
    print("VALIDATION FAILED")
    print("\n".join(f"- {e}" for e in errors))
    sys.exit(1)
print(f"VALIDATION PASSED: {len(list(SKILLS.iterdir()))} published agent skills checked")
