from pathlib import Path
import json
import os
import re
import subprocess
import tempfile
import unittest

LAB = Path(__file__).resolve().parents[1]
CHAPTER = LAB.parent

class LabPackageTests(unittest.TestCase):
    @staticmethod
    def bash_block_after(path, marker):
        section = path.read_text(encoding="utf-8").split(marker, 1)[1]
        match = re.search(r"```bash\n(.*?)\n```", section, re.S)
        if not match:
            raise AssertionError(f"no Bash block after {marker} in {path}")
        return match.group(1)

    def test_required_files(self):
        required = [
            LAB / "README.md", LAB / "VERSIONS.yaml", LAB / "environment-contract.example.yaml",
            LAB / "scripts/preflight.py", LAB / "scripts/verify-resource-chain.sh",
            LAB / "scripts/verify-absence.sh",
        ]
        required += sorted((LAB / "walkthroughs").glob("0[1-7]-*.md"))
        self.assertEqual(13, len(required))
        for path in required:
            self.assertTrue(path.is_file(), path)

    def test_all_local_markdown_links_resolve(self):
        lab_markdown = [path for path in LAB.rglob("*.md") if ".terraform" not in path.parts]
        for source in lab_markdown:
            text = source.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                target_path, separator, fragment = target.partition("#")
                if not target_path or "://" in target_path or target_path.startswith("mailto:"):
                    continue
                resolved = (source.parent / target_path).resolve()
                self.assertTrue(resolved.exists(), f"{source}: {target_path}")
                if separator and resolved.suffix == ".md":
                    self.assertTrue(fragment.startswith("user-content-"), f"{source}: Forgejo fragment lacks user-content- prefix: {target}")
                    headings = re.findall(r"^#{1,6}\s+(.+?)\s*$", resolved.read_text(encoding="utf-8"), re.M)
                    slugs = {
                        "user-content-" + re.sub(r"-+", "-", re.sub(r"[^a-z0-9\s-]", "", heading.lower()).strip().replace(" ", "-"))
                        for heading in headings
                    }
                    self.assertIn(fragment, slugs, f"{source}: missing fragment target {target}")

    def test_portable_source_record(self):
        source = (LAB.parent / "SOURCE.md").read_text(encoding="utf-8")
        self.assertIn("65055f17aaf13cf1944e2f4c4e1180dd3b94478a", source)
        self.assertIn("chapter-3/lab", source)

    def test_example_contract_requires_explicit_override(self):
        command = ["python3", str(LAB / "scripts/preflight.py"), str(LAB / "environment-contract.example.yaml")]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("example contract refused", result.stderr)
        result = subprocess.run([*command, "--allow-example"], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_resource_chain_helper_accepts_exact_ids_and_rejects_mismatch(self):
        fake = r'''#!/usr/bin/env python3
import json, os, sys
a = sys.argv[1:]
joined = ' '.join(a)
column = a[a.index('-c') + 1] if '-c' in a else ''
if 'server show' in joined and column == 'status': print('ACTIVE')
elif 'port list' in joined: print('other-port' if os.getenv('FAKE_BAD_PORT') else 'port-1')
elif 'port show' in joined: print(json.dumps({'device_id': 'server-1', 'status': 'ACTIVE', 'security_group_ids': ['sg-10' if os.getenv('FAKE_BAD_SG') else 'sg-1']}))
elif 'floating ip show' in joined: print(json.dumps({'port_id': 'port-1', 'status': 'ACTIVE'}))
elif 'volume show' in joined: print(json.dumps({'attachments': [{'server_id': 'server-10' if os.getenv('FAKE_BAD_VOLUME') else 'server-1'}], 'status': 'in-use'}))
else:
    print('unexpected fake call: ' + joined, file=sys.stderr)
    raise SystemExit(3)
'''
        with tempfile.TemporaryDirectory() as directory:
            command_path = Path(directory) / "openstack"
            command_path.write_text(fake, encoding="utf-8")
            command_path.chmod(0o755)
            env = {**os.environ, "PATH": f"{directory}:{os.environ['PATH']}"}
            command = [str(LAB / "scripts/verify-resource-chain.sh"), "cloud", "server-1", "port-1", "sg-1", "fip-1", "volume-1"]
            result = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            result = subprocess.run(command, env={**env, "FAKE_BAD_PORT": "1"}, capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("recorded port does not match", result.stderr)
            result = subprocess.run(command, env={**env, "FAKE_BAD_SG": "1"}, capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("security group is not attached", result.stderr)
            result = subprocess.run(command, env={**env, "FAKE_BAD_VOLUME": "1"}, capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("volume attachment does not reference", result.stderr)

    def test_opentofu_evidence_handoff_uses_validator_schema(self):
        walkthrough = LAB / "walkthroughs/05-opentofu-automation.md"
        block = self.bash_block_after(walkthrough, "Capture the outputs:")
        fake = """#!/bin/sh
[ "$1" = output ] && [ "$2" = -raw ] || exit 2
printf '%s\\n' "value-$3"
"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            opentofu = root / "opentofu"
            opentofu.mkdir()
            command_path = root / "tofu"
            command_path.write_text(fake, encoding="utf-8")
            command_path.chmod(0o755)
            env = {**os.environ, "PATH": f"{root}:{os.environ['PATH']}"}
            result = subprocess.run(["bash", "-c", block], cwd=opentofu, env=env, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            evidence = json.loads((root / "evidence/resource-ids.json").read_text())
            required = {"cloud", "server_id", "port_id", "security_group_id", "floating_ip_id", "volume_id"}
            self.assertEqual(required, set(evidence))
            self.assertEqual("value-openstack_cloud", evidence["cloud"])

    def test_cleanup_loads_complete_evidence_in_fresh_shell(self):
        walkthrough = LAB / "walkthroughs/07-cleanup.md"
        block = self.bash_block_after(walkthrough, "## OpenStackClient path")
        complete = {
            "cloud": "cloud-1", "server_id": "server-1", "port_id": "port-1",
            "security_group_id": "sg-1", "floating_ip_id": "fip-1", "volume_id": "volume-1",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "evidence").mkdir()
            evidence_path = root / "evidence/resource-ids.json"
            evidence_path.write_text(json.dumps(complete), encoding="utf-8")
            result = subprocess.run(["bash", "-c", block], cwd=root, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            evidence_path.write_text(json.dumps({key: value for key, value in complete.items() if key != "cloud"}), encoding="utf-8")
            result = subprocess.run(["bash", "-c", block], cwd=root, capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)

    def test_discovery_captures_current_usage_and_image_status(self):
        text = (LAB / "walkthroughs/01-discovery.md").read_text(encoding="utf-8")
        for service in ("compute", "volume", "network"):
            self.assertIn(f"quota show --{service} --usage", text)
        self.assertIn('token issue -f value -c project_id', text)
        self.assertIn('ACTIVE_PROJECT_NAME=$(openstack --os-cloud "$CLOUD" project show "$PROJECT_ID"', text)
        self.assertIn('[ "$ACTIVE_PROJECT_NAME" = "$CONTRACT_PROJECT_NAME" ]', text)
        self.assertRegex(text, r'image show "\$IMAGE_NAME"[\s\\]+-f json -c id -c status')

    def test_discovery_rejects_project_scope_mismatch(self):
        walkthrough = LAB / "walkthroughs/01-discovery.md"
        block = self.bash_block_after(walkthrough, "## Verify identity and quota")
        fake = r'''#!/usr/bin/env python3
import json, sys
joined = ' '.join(sys.argv[1:])
if 'token issue' in joined and '-f json' in joined:
    print(json.dumps({'expires': '2030-01-01T00:00:00+0000', 'project_id': 'project-1'}))
elif 'token issue' in joined:
    print('project-1')
elif 'project show' in joined:
    print('demo')
elif 'quota show' in joined:
    print('{}')
else:
    raise SystemExit(2)
'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "preflight.py").write_text((LAB / "scripts/preflight.py").read_text(), encoding="utf-8")
            command_path = root / "openstack"
            command_path.write_text(fake, encoding="utf-8")
            command_path.chmod(0o755)
            env = {**os.environ, "PATH": f"{root}:{os.environ['PATH']}"}
            contract = root / "environment-contract.yaml"
            contract.write_text("project_name: demo\n", encoding="utf-8")
            result = subprocess.run(["bash", "-c", block], cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            contract.write_text("project_name: other-project\n", encoding="utf-8")
            result = subprocess.run(["bash", "-c", block], cwd=root, env=env, capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("does not match contract project", result.stderr)

    def test_all_documented_bash_blocks_parse(self):
        sources = [LAB / "README.md", *sorted((LAB / "walkthroughs").glob("*.md")), LAB / "opentofu/README.md"]
        for source in sources:
            text = source.read_text(encoding="utf-8")
            for number, block in enumerate(re.findall(r"```bash\n(.*?)\n```", text, re.S), 1):
                result = subprocess.run(["bash", "-n"], input=block, text=True, capture_output=True)
                self.assertEqual(0, result.returncode, f"{source} Bash block {number}: {result.stderr}")

    def test_no_em_dash_in_new_markdown(self):
        lab_markdown = [path for path in LAB.rglob("*.md") if ".terraform" not in path.parts]
        sources = lab_markdown
        for source in sources:
            self.assertNotIn("—", source.read_text(encoding="utf-8"), source)

if __name__ == "__main__":
    unittest.main()
