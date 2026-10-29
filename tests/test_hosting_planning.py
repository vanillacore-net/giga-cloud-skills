"""Tests for the hosting planning skills and their results app."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
NEEDS = ROOT / "skills" / "hosting-needs-planning"
PLATFORM = ROOT / "skills" / "hosting-platform-planning"
APP = NEEDS / "assets" / "results-app"
EXAMPLES = NEEDS / "assets" / "examples"

# Event, venue, people and customer terms from the demonstration these skills
# were generalised from. Stored as truncated SHA-256 digests of lower-case words
# and word pairs, so the published test does not itself carry the terms.
FORBIDDEN_DIGESTS = {
    "1057a9604e04b274",
    "10e9354e07a0eaef",
    "264c8c381bf16c98",
    "5a43516885a4de85",
    "623b2b96c7d64680",
    "7357de1c8c6cbc6d",
    "8606cf38f741da32",
    "8be0b5445fca6eb1",
    "a11982a968e83beb",
    "a7996bbcd2b449e7",
    "b2caa99140be6270",
    "c2e5f933acd54308",
    "c77a783bff1b1abf",
    "dac4970ce624959f",
    "de0de82ac6a33803",
    "f434d56d24bbc7bf",
    "f972939e59ba116b",
    "fcf5fab8a3700e90",
}
PRIVATE_ADDRESS = re.compile(r"\b(?:10|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d+\.\d+")


def forbidden_terms(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+(?:\.[a-z0-9]+)*", text.casefold())
    candidates = set(words) | {f"{a} {b}" for a, b in zip(words, words[1:])}
    found = [c for c in candidates if hashlib.sha256(c.encode()).hexdigest()[:16] in FORBIDDEN_DIGESTS]
    found += PRIVATE_ADDRESS.findall(text)
    return sorted(found)


def build(cases: Path, out: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(APP / "build_app.py"), "--cases", str(cases), "--out", str(out), *extra],
        capture_output=True, text=True,
    )


class ResultsAppTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def test_builds_example_from_other_directory(self) -> None:
        out = self.tmp / "out"
        r = subprocess.run(
            [sys.executable, str(APP / "build_app.py"), "--cases", str(EXAMPLES / "cases"),
             "--out", str(out), "--config", str(EXAMPLES / "app.json")],
            capture_output=True, text=True, cwd=self.tmp,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        for page in ["index.html", "use-cases.html", "planning.html", "platform.html", "assets/app.css"]:
            self.assertTrue((out / page).is_file(), page)
        cases = (out / "use-cases.html").read_text()
        self.assertIn("Business permit applications", cases)
        self.assertIn("Public transport journey planner", cases)
        self.assertIn('class="open"', cases)

    def test_result_pages_start_empty_and_reload(self) -> None:
        out = self.tmp / "out"
        self.assertEqual(build(EXAMPLES / "cases", out).returncode, 0)
        for page in ["planning.html", "platform.html"]:
            text = (out / page).read_text()
            self.assertIn("Waiting for the agent", text)
            self.assertIn('http-equiv="refresh"', text)
            self.assertEqual(text.count("<main>"), 1)
            self.assertIn("<header", text)
            self.assertIn("<footer>", text)

    def test_static_mode_has_no_reload(self) -> None:
        out = self.tmp / "out"
        self.assertEqual(build(EXAMPLES / "cases", out, "--static").returncode, 0)
        self.assertNotIn("http-equiv", (out / "planning.html").read_text())

    def test_no_external_resources(self) -> None:
        out = self.tmp / "out"
        self.assertEqual(build(EXAMPLES / "cases", out, "--config", str(EXAMPLES / "app.json")).returncode, 0)
        for page in out.glob("*.html"):
            text = page.read_text()
            self.assertNotRegex(text, r'(src|href)="https?://(?!.*target="_blank")', page.name)
        self.assertNotIn("http", (out / "assets" / "app.css").read_text())

    def test_config_values_are_escaped(self) -> None:
        cfg = self.tmp / "app.json"
        cfg.write_text(json.dumps({"title": "<script>x</script>", "links": [{"label": "A&B", "href": "https://example.org/?a=1&b=2"}]}))
        out = self.tmp / "out"
        r = build(EXAMPLES / "cases", out, "--config", str(cfg))
        self.assertEqual(r.returncode, 0, r.stderr)
        index = (out / "index.html").read_text()
        self.assertNotIn("<script>", index)
        self.assertIn("&lt;script&gt;", index)
        self.assertIn("A&amp;B", index)

    def test_rejects_bad_input(self) -> None:
        empty = self.tmp / "empty"
        empty.mkdir()
        self.assertNotEqual(build(empty, self.tmp / "o1").returncode, 0)

        many = self.tmp / "many"
        many.mkdir()
        for i in range(5):
            (many / f"case-{i}.md").write_text(f"# Case {i}: S{i}\n\n- fact\n")
        self.assertNotEqual(build(many, self.tmp / "o2").returncode, 0)

        nofacts = self.tmp / "nofacts"
        nofacts.mkdir()
        (nofacts / "case-a.md").write_text("# Case A: Empty\n")
        self.assertNotEqual(build(nofacts, self.tmp / "o3").returncode, 0)

        for bad in [{"accent": "red"}, {"colour": "#000000"}, {"links": [{"label": "x", "href": "javascript:alert(1)"}]}]:
            cfg = self.tmp / "bad.json"
            cfg.write_text(json.dumps(bad))
            self.assertNotEqual(build(EXAMPLES / "cases", self.tmp / "o4", "--config", str(cfg)).returncode, 0, bad)

    def test_four_cases_get_four_colours(self) -> None:
        four = self.tmp / "four"
        four.mkdir()
        for i, letter in enumerate("ABCD"):
            (four / f"case-{letter.lower()}.md").write_text(f"# Case {letter}: Service {letter}\n\n- fact {i}\n")
        out = self.tmp / "out"
        self.assertEqual(build(four, out).returncode, 0)
        text = (out / "use-cases.html").read_text()
        for cls in ["card a", "card b", "card c", "card d"]:
            self.assertIn(cls, text)


class SkillContentTest(unittest.TestCase):
    def frontmatter(self, path: Path) -> dict:
        text = path.read_text()
        return yaml.safe_load(text.split("---", 2)[1])

    def test_skills_are_marketplace_ready(self) -> None:
        for skill in [NEEDS, PLATFORM]:
            fm = self.frontmatter(skill / "SKILL.md")
            self.assertEqual(fm["name"], skill.name)
            self.assertEqual(fm["metadata"]["provider"], "VanillaCore")
            self.assertTrue(fm["license"])
            self.assertRegex(fm["name"], r"^[a-z0-9-]{3,64}$")

    def test_outputs_and_handoff(self) -> None:
        contract = json.loads((ROOT / "learning-contract.json").read_text())
        hp = contract["hosting_planning"]
        for name, output in hp["outputs"].items():
            text = (ROOT / "skills" / name / "SKILL.md").read_text()
            self.assertIn(f"{output}:", text)
            self.assertIn(hp["result_pages"][name], text)
        self.assertIn("hosting_needs_plan", (PLATFORM / "SKILL.md").read_text())

    def test_each_skill_is_standalone(self) -> None:
        for skill in [NEEDS, PLATFORM]:
            text = (skill / "SKILL.md").read_text()
            for ref in re.findall(r"`(references/[\w./-]+|assets/[\w./-]+)`", text):
                if skill is PLATFORM and ref.startswith("assets/"):
                    continue
                self.assertTrue((skill / ref).exists(), f"{skill.name}: {ref}")
            self.assertNotIn("../", text)

    def test_page_rules_identical(self) -> None:
        self.assertEqual(
            (NEEDS / "references" / "page-rules.md").read_bytes(),
            (PLATFORM / "references" / "page-rules.md").read_bytes(),
        )

    def test_no_event_or_customer_specifics(self) -> None:
        for skill in [NEEDS, PLATFORM]:
            for path in skill.rglob("*"):
                if path.is_file() and path.suffix in {".md", ".py", ".css", ".json", ".yaml"}:
                    found = forbidden_terms(path.read_text())
                    self.assertEqual(found, [], f"{path.relative_to(ROOT)}: {len(found)} forbidden term(s)")

    def test_denylist_detects_terms(self) -> None:
        self.assertTrue(forbidden_terms("Shown at the Connectivity Forum."))
        self.assertTrue(forbidden_terms("served from 192.168.1.20"))
        self.assertFalse(forbidden_terms("Two citizen services, one label."))


if __name__ == "__main__":
    unittest.main()
