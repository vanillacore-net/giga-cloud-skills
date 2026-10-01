"""Validate independent operational skill installation and coordinator wiring."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOMAINS = ['environment', 'compute', 'networking', 'storage', 'troubleshooting']


class UsagePackageTests(unittest.TestCase):
    def test_skills_have_operation_contract_not_lab_only_gate(self):
        for domain in DOMAINS:
            path = ROOT / 'skills' / f'openstack-{domain}' / 'SKILL.md'
            self.assertTrue(path.is_file(), f'usage skill missing: {domain}')
            text = path.read_text()
            for term in ['openstack-operation-record/v1', 'inspect', 'prepare', 'execute', 'references/usage.md', 'assets/operator-kit/', 'challenge', 'attempt', 'stop before']:
                self.assertIn(term, text, domain)
            self.assertNotIn('approved disposable project', text)

    def test_contract_and_plugin_versions_integrate_all_five(self):
        contract = json.loads((ROOT / 'learning-contract.json').read_text())
        for domain in DOMAINS:
            self.assertIn(f'openstack-{domain}', contract['expected_skills'])
            self.assertEqual(contract['openstack_usage']['domains'][domain], f'openstack-{domain}')
        for client in ['.claude-plugin', '.codex-plugin']:
            self.assertEqual(json.loads((ROOT / client / 'plugin.json').read_text())['version'], contract['package_version'])

    def test_coordinator_references_operational_router_and_record(self):
        guide = (ROOT / 'skills/giga-cloud-learning-guide/SKILL.md').read_text()
        self.assertIn('scripts/route_openstack.py', guide)
        self.assertIn('openstack-operation-record/v1', guide)
        self.assertIn('existing resources', guide)

    def test_every_independent_install_runs_without_repository(self):
        canonical = ROOT / 'runtime/openstack_ops.py'
        self.assertTrue(canonical.is_file(), 'operational runtime missing')
        digest = hashlib.sha256(canonical.read_bytes()).hexdigest()
        for domain in DOMAINS:
            source = ROOT / 'skills' / f'openstack-{domain}'
            script = source / 'assets/operator-kit/scripts/openstack_ops.py'
            self.assertTrue(script.is_file(), f'standalone runtime missing: {domain}')
            self.assertEqual(hashlib.sha256(script.read_bytes()).hexdigest(), digest)
            with tempfile.TemporaryDirectory() as directory:
                import shutil
                installed = Path(directory) / source.name
                shutil.copytree(source, installed)
                result = subprocess.run(['python3', str(installed / 'assets/operator-kit/scripts/openstack_ops.py'), '--help'], capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
            for path in source.rglob('*.md'):
                self.assertNotRegex(path.read_text(), r'\.\./\.\./(?:runtime|docs|skills)/')

    def test_usage_references_match_the_documented_work_copy_layout(self):
        for domain in DOMAINS:
            text = (ROOT / 'skills' / f'openstack-{domain}' / 'references/usage.md').read_text()
            self.assertNotIn('$WORK/assets-copy/', text, domain)
            self.assertIn('WORK="$WORK_DIR"', text, domain)
            self.assertIn('OPS="$WORK/scripts/openstack_ops.py"', text, domain)

    def test_operator_manifests_cover_exact_final_bytes(self):
        for domain in DOMAINS:
            kit = ROOT / 'skills' / f'openstack-{domain}' / 'assets/operator-kit'
            manifest = kit / 'MANIFEST.sha256'
            self.assertTrue(manifest.is_file(), f'checksum manifest missing: {domain}')
            seen = set()
            for line in manifest.read_text().splitlines():
                expected, relative = line.split('  ', 1)
                file = kit / relative
                self.assertTrue(file.is_file())
                self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(), expected)
                seen.add(relative)
            actual = {str(p.relative_to(kit)) for p in kit.rglob('*') if p.is_file() and p.name != 'MANIFEST.sha256' and '__pycache__' not in p.parts}
            self.assertEqual(actual, seen)


if __name__ == '__main__':
    unittest.main()
