#!/usr/bin/env python3
"""Run deterministic route, handoff, and chapter-coverage checks."""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "learning-contract.json").read_text(encoding="utf-8"))
FIXTURES = json.loads((ROOT / "tests" / "learning-paths.json").read_text(encoding="utf-8"))


def route(prompt: str) -> str:
    lowered = prompt.casefold()
    scores = {
        chapter: sum(keyword.casefold() in lowered for keyword in spec["routing_keywords"])
        for chapter, spec in CONTRACT["chapters"].items()
    }
    best = max(scores.values())
    winners = [chapter for chapter, score in scores.items() if score == best]
    if best == 0 or len(winners) != 1:
        raise AssertionError(f"ambiguous route for {prompt!r}: {scores}")
    return winners[0]


def combined_skill_text(chapter: str) -> str:
    spec = CONTRACT["chapters"][chapter]
    names = [spec["primary_skill"], *spec["supporting_skills"]]
    return "\n".join(
        (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        for name in names
    ).casefold()


def yaml_contract(text: str, output: str) -> dict:
    pattern = rf"```yaml\n({re.escape(output)}:\n.*?\n)```"
    match = re.search(pattern, text, re.S)
    if not match:
        raise AssertionError(f"YAML contract not found for {output}")
    parsed = yaml.safe_load(match.group(1))
    value = parsed.get(output) if isinstance(parsed, dict) else None
    if not isinstance(value, dict):
        raise AssertionError(f"YAML contract is not a mapping for {output}")
    return value


def main() -> None:
    handoff_doc = (ROOT / "docs" / "handoff-contracts.md").read_text(encoding="utf-8")
    portable_doc = (
        ROOT / "skills" / "giga-cloud-learning-guide" / "references" / "chapter-contracts.md"
    ).read_text(encoding="utf-8")
    failures: list[str] = []

    for case in FIXTURES["cases"]:
        actual = route(case["prompt"])
        if actual != case["chapter"]:
            failures.append(f"{case['id']}: expected Chapter {case['chapter']}, got {actual}")
        spec = CONTRACT["chapters"][case["chapter"]]
        if spec["output"] != case["output"]:
            failures.append(f"{case['id']}: output mismatch")
        missing_checks = set(case["required_challenge_checks"]) - set(spec["challenge_checks"])
        if missing_checks:
            failures.append(f"{case['id']}: missing challenge checks {sorted(missing_checks)}")

    for chapter, spec in CONTRACT["chapters"].items():
        text = combined_skill_text(chapter)
        for term in spec["coverage_terms"]:
            if term.casefold() not in text:
                failures.append(f"Chapter {chapter}: coverage term absent: {term}")
        if spec["output"] not in handoff_doc:
            failures.append(f"Chapter {chapter}: handoff absent from docs: {spec['output']}")
        if spec["schema"] not in handoff_doc:
            failures.append(f"Chapter {chapter}: schema absent from docs: {spec['schema']}")
        primary_path = ROOT / "skills" / spec["primary_skill"]
        primary = (primary_path / "SKILL.md").read_text(encoding="utf-8")
        primary_package_text = "\n".join(
            path.read_text(encoding="utf-8") for path in primary_path.rglob("*.md")
        )
        if spec["schema"] not in primary_package_text:
            failures.append(f"Chapter {chapter}: primary skill package lacks schema {spec['schema']}")
        try:
            documented = yaml_contract(handoff_doc, spec["output"])
            candidates = {
                "primary": yaml_contract(primary_package_text, spec["output"]),
                "portable": yaml_contract(portable_doc, spec["output"]),
            }
            for label, candidate in candidates.items():
                missing_keys = set(documented) - set(candidate)
                if missing_keys:
                    failures.append(
                        f"Chapter {chapter}: {label} contract lacks handoff keys {sorted(missing_keys)}"
                    )
                for key in sorted(set(documented) & set(candidate)):
                    if type(documented[key]) is not type(candidate[key]):
                        failures.append(
                            f"Chapter {chapter}: {label} handoff type mismatch for {key}: "
                            f"docs={type(documented[key]).__name__}, "
                            f"{label}={type(candidate[key]).__name__}"
                        )
        except (AssertionError, yaml.YAMLError) as exc:
            failures.append(f"Chapter {chapter}: handoff contract parse failed: {exc}")
        for mode in CONTRACT["learning_modes"]:
            if mode.casefold() not in primary.casefold():
                failures.append(f"Chapter {chapter}: primary skill lacks mode {mode}")

    guide = (ROOT / "skills" / "giga-cloud-learning-guide" / "SKILL.md").read_text(encoding="utf-8").casefold()
    for marker in (
        "exactly one primary focused skill",
        "focused_skill_required",
        "validate each returned artifact",
        "reconciliation finding or decision gap",
        "architecture_learning_record",
        "challenge mode without a learner attempt",
    ):
        if marker not in guide:
            failures.append(f"meta-skill orchestration marker absent: {marker}")

    if CONTRACT["handoff_order"] != [
        CONTRACT["chapters"][str(number)]["output"] for number in range(1, len(CONTRACT["chapters"]) + 1)
    ]:
        failures.append("handoff order does not match configured chapter outputs")

    if failures:
        print("LEARNING PATH TESTS FAILED")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print(
        "LEARNING PATH TESTS PASSED: "
        f"{len(FIXTURES['cases'])} routes, {len(CONTRACT['chapters'])} chapter contracts, "
        f"{len(CONTRACT['handoff_order'])} handoffs"
    )


if __name__ == "__main__":
    main()
