"""Positive network/storage operation fixtures and artifact-integrity regressions."""
import json
from pathlib import Path
from typing import Any, cast
import test_openstack_ops as offline
import unittest

RESOURCE = offline.RESOURCE
CREATED = offline.CREATED


class DomainOperationTests(unittest.TestCase):
    root: Path
    client: Path
    env: dict
    write = offline.OfflineTests.write
    run_cli = offline.OfflineTests.run_cli
    calls = offline.OfflineTests.calls
    prepare = offline.OfflineTests.prepare
    execute = offline.OfflineTests.execute

    def setUp(self):
        offline.OfflineTests.setUp(cast(Any, self))
        # This test-only client changes one explicit fixture field after the
        # emitted mutation. It does not authenticate or contact any cloud.
        update = '''if key=='volume set' and '--size' in cmd:
 cfg.setdefault('records',{}).setdefault('volume',{})['size']=int(cmd[cmd.index('--size')+1])
 (p/'fixture.json').write_text(json.dumps(cfg))
 print('{}'); sys.exit()
'''
        source = offline.FIXTURE.replace("if 'show' in cmd:", update + "if 'show' in cmd:")
        self.assertNotEqual(source, offline.FIXTURE)
        self.client.write_text(source)

    def test_network_creation_checkpoints_new_id_and_keeps_private_scope(self):
        self.write('fixture.json', {'records': {'network': {'router:external': False, 'shared': False}}})
        prepared = self.prepare('network-create', name='private-app')
        self.assertEqual(prepared.returncode, 0, prepared.stdout + prepared.stderr)
        result = self.execute()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        record = json.loads((self.root / 'evidence.json').read_text())
        self.assertEqual(record['status'], 'complete')
        self.assertIn(CREATED, record['resource_ids'])
        created = [call['argv'] for call in self.calls() if 'create' in call['argv']]
        self.assertEqual(len(created), 1)
        self.assertIn('--internal', created[0])
        self.assertIn('--no-share', created[0])
        self.assertFalse(any('delete' in call['argv'] for call in self.calls()))

    def test_volume_extension_changes_cinder_capacity_and_rechecks_exact_size(self):
        prepared = self.prepare('volume-extend', volume_id=RESOURCE, size_gib=100)
        self.assertEqual(prepared.returncode, 0, prepared.stdout + prepared.stderr)
        result = self.execute()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        record = json.loads((self.root / 'evidence.json').read_text())
        self.assertEqual(record['status'], 'complete')
        self.assertIn(RESOURCE, record['resource_ids'])
        self.assertTrue(any('--size' in call['argv'] and '100' in call['argv'] for call in self.calls()))
        self.assertFalse(any('remove' in call['argv'] or 'delete' in call['argv'] for call in self.calls()))
        self.assertNotIn('guest-filesystem-verified', result.stdout)

    def test_receipt_plan_cannot_be_replayed_in_a_different_work_root(self):
        self.assertEqual(self.prepare('server-start', server_id=RESOURCE).returncode, 0)
        different = self.root / 'other-protected-root'
        different.mkdir(mode=0o700)
        (different / 'plan.json').write_bytes((self.root / 'plan.json').read_bytes())
        plan = json.loads((self.root / 'plan.json').read_text())
        result = self.run_cli('--work-root', str(different), 'execute', '--plan', 'plan.json', '--approve', plan['sha256'], '--evidence', 'execution.json')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertFalse(any('start' in call['argv'] for call in self.calls()))


if __name__ == '__main__':
    unittest.main()
