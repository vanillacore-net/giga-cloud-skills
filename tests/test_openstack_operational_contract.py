"""Operational regressions beyond simple success fixtures. All clients are fake."""
import json
import subprocess
import sys
from pathlib import Path
import test_openstack_ops as offline
import unittest

RESOURCE = offline.RESOURCE


class OperationalContractTests(unittest.TestCase):
    root: Path
    env: dict
    setUp = offline.OfflineTests.setUp
    write = offline.OfflineTests.write
    run_cli = offline.OfflineTests.run_cli
    calls = offline.OfflineTests.calls
    prepare = offline.OfflineTests.prepare
    execute = offline.OfflineTests.execute

    def test_inventory_contains_usable_values_but_never_credentials(self):
        self.write('fixture.json', {'lists': {'flavor list': [{'ID': RESOURCE, 'Name': 'apps-medium', 'RAM': 16384, 'Disk': 40, 'VCPUs': 4, 'password': 'TOP_SECRET', 'token': 'TOP_SECRET'}]}})
        result = self.run_cli('inspect', '--context', 'context.json', '--domain', 'environment', '--evidence', 'inventory.json')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('apps-medium', result.stdout)
        self.assertIn('16384', result.stdout)
        self.assertNotIn('TOP_SECRET', result.stdout)

    def test_live_controller_markers_override_claim_of_direct_ownership(self):
        self.write('fixture.json', {'records': {'server': {'properties': {'cluster.x-k8s.io/cluster-name': 'managed-cluster'}}}})
        result = self.prepare()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertFalse(any('stop' in call['argv'] for call in self.calls()))

    def test_resource_state_changed_since_prepare_needs_new_proposal(self):
        self.assertEqual(self.prepare('server-stop', server_id=RESOURCE).returncode, 0)
        self.write('fixture.json', {'status': 'SHUTOFF'})
        result = self.execute()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertFalse(any('stop' in call['argv'] for call in self.calls()))

    def test_invalid_action_type_fails_without_traceback(self):
        self.write('request.json', {'action': [], 'parameters': {}})
        result = self.run_cli('prepare', '--context', 'context.json', '--request', 'request.json', '--plan', 'invalid.json')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertFalse(self.calls())

    def test_nonexistent_work_root_fails_without_traceback(self):
        result = self.run_cli('--work-root', str(self.root / 'missing'), 'inspect', '--context', 'context.json', '--domain', 'environment', '--evidence', 'x.json')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_user_data_stays_bound_when_execute_caller_directory_differs(self):
        approved_file = self.root / 'init.yml'
        approved_file.write_text('#cloud-config\n{}')
        caller = self.root / 'different-caller'
        caller.mkdir(mode=0o700)
        (caller / 'init.yml').write_text('UNAPPROVED-CONTENT')
        source = offline.FIXTURE.replace("args=sys.argv[1:]", "args=sys.argv[1:]\nfrom pathlib import Path\nPath(os.environ['FIXTURE_ROOT'], 'client-cwd.txt').write_text(os.getcwd())")
        (self.root / 'fake-openstack').write_text(source)
        prepared = self.prepare('server-create', name='approved-vm', image_id=RESOURCE, flavor_id=RESOURCE, network_id=RESOURCE, security_group_id=RESOURCE, user_data_file='init.yml')
        self.assertEqual(prepared.returncode, 0, prepared.stdout + prepared.stderr)
        proposal = json.loads((self.root / 'plan.json').read_text())
        result = subprocess.run([sys.executable, str(offline.SCRIPT), '--work-root', str(self.root), 'execute', '--plan', 'plan.json', '--approve', proposal['sha256'], '--evidence', 'execution.json'], cwd=caller, env=self.env, capture_output=True, text=True, timeout=8)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        mutation = next(call['argv'] for call in self.calls() if '--user-data' in call['argv'])
        supplied = Path(mutation[mutation.index('--user-data') + 1])
        client_cwd = Path((self.root / 'client-cwd.txt').read_text())
        actual = supplied if supplied.is_absolute() else client_cwd / supplied
        self.assertEqual(actual.resolve(), approved_file.resolve())

    def test_profile_config_locator_is_preserved_without_os_overrides(self):
        self.env['OS_CLIENT_CONFIG_FILE'] = str(self.root / 'clouds-config.yaml')
        result = self.run_cli('inspect', '--context', 'context.json', '--domain', 'environment', '--evidence', 'config-check.json')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.calls()[0]['os_env'].get('OS_CLIENT_CONFIG_FILE'), self.env['OS_CLIENT_CONFIG_FILE'])
        self.assertNotIn('OS_TOKEN', self.calls()[0]['os_env'])


if __name__ == '__main__':
    unittest.main()
