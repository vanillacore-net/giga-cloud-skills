"""Offline integration and refusal tests. Only this lab's temporary tree is written.

Case state is injected in memory because installed/public lab directories are
not legal runtime session locations. Real renderer, lifecycle, Helm, openssl,
and curl processes run; no cloud, cluster or Ansible process is started.
"""
import argparse
import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import ssl
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import unittest
from unittest.mock import patch
import yaml

LAB = Path(__file__).resolve().parents[1]
BOOTSTRAP_INPUT = os.environ.get('CH5_BOOTSTRAP_REPO')
if not BOOTSTRAP_INPUT:
    raise RuntimeError('Set CH5_BOOTSTRAP_REPO to the reviewed Bootstrap checkout before running offline tests')
BOOTSTRAP = Path(BOOTSTRAP_INPUT).resolve()
spec = importlib.util.spec_from_file_location('platform_lab', LAB / 'scripts/platform.py')
assert spec is not None and spec.loader is not None
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class PlatformTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='offline-', dir=LAB)
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        fixture = yaml.safe_load((BOOTSTRAP / 'tests/fixtures/non-default-pod-cidr.yml').read_text())
        # Fixtures are test inputs, not configuration or provenance for a live image.
        environment = {'openstack': {'region_name': 'OfflineRegion'}, 'gitops': {
            'repository_url': 'https://git.example.test/platform/bootstrap.git',
            'management_revision': p.PIN, 'foundation_revision': p.PIN, 'spoke_revision': 'main'},
            'cluster_foundations': fixture['cluster_foundations'], 'management_monitoring': {'remote_write_receiver': False},
            'bootstrap_environment': 'offline', 'bootstrap_profile': 'integration-test'}
        routing = environment['cluster_foundations']['govstack_routing']
        routing.update(repository_url=environment['gitops']['repository_url'], revision=p.PIN, routes=[])
        self.environment = self.root / 'environment.yml'
        self.environment.write_text(yaml.safe_dump(environment))
        self.inventory = self.root / 'inventory.yml'
        self.inventory.write_text('all: {hosts: {}}\n')
        self.outputs = self.root / 'outputs.json'
        self.outputs.write_text(json.dumps({key: {'value': 'offline-' + key} for key in ('network_id', 'subnet_id', 'ssh_key_name', 'seed_security_group_id')}))
        self.image = self.root / 'image.json'
        self.image.write_text(json.dumps({'id': '12345678-1234-1234-1234-123456789abc', 'status': 'active', 'kubernetes_version': 'v1.36.3'}))
        configs = {}
        for index, (role, name) in enumerate(p.CLUSTERS.items()):
            config = {'cluster': {'name': name, 'role': 'loadbalancer' if role == 'loadbalancer' else 'spoke',
                'namespace': 'govstack-clusters', 'kubernetes_version': 'v1.36.3',
                'control_plane': {'replicas': 1, 'flavor': 'offline-control'}, 'workers': {'replicas': 1, 'flavor': 'offline-worker'},
                'openstack': {'identity_secret': name + '-openstack', 'child_cloud_secret': name + '-cloud',
                    'resource_tag': 'govstack.itu.int:cluster-token=offline-' + name + '-123456789',
                    'network_mode': 'existing', 'image': 'state', 'machine_template_revision': 'r1', 'control_plane_template_revision': 'r1'},
                'gateway': {'enabled': False}, 'routing': routing,
                'networking': {'api_vip': f'172.20.{index}.10', 'api_server_port': 6443, 'pod_cidr': f'172.2{index}.0.0/16',
                              'service_cidr': f'10.{index + 80}.0.0/16', 'service_vip_range': f'172.20.{index}.100-172.20.{index}.110', 'service_vip_cidr': f'172.20.{index}.96/27'}}}
            path = self.root / (name + '.yml')
            path.write_text(yaml.safe_dump(config))
            configs[role] = str(path)
        self.case = {'schema': 'platform-session/v1', 'mode': 'example', 'bootstrap_repo': str(BOOTSTRAP),
            'environment_config': str(self.environment), 'inventory': str(self.inventory), 'infrastructure_outputs': str(self.outputs),
            'image_metadata': str(self.image), 'management_context': 'offline-management',
            'management_server': 'https://management.example.test:6443', 'clusters': p.CLUSTERS.copy(), 'cluster_configs': configs,
            'domains': {'mediator': 'mediator.example.test', 'examples': 'apps.example.test'},
            'tls': {'mode': 'trusted', 'issuer': {'name': 'reviewed-issuer', 'kind': 'ClusterIssuer'}},
            'routing': {'private_ingress': {'mediator': '172.20.1.100', 'examples': '172.20.2.100'},
                        'probe_image': 'registry.example.test/http-echo@sha256:' + 'a' * 64}}
        self.output = self.root / 'generated/spokes'
        self.location = '/var/tmp/chapter5-runtime/case.json'  # only a virtual external path; never written

    def args(self, command, **kwargs):
        return argparse.Namespace(command=command, case=self.location, timeout=60, target='all', **kwargs)

    def prepared(self):
        with patch.object(p, 'output_root', return_value=self.output), contextlib.redirect_stdout(io.StringIO()):
            p.render(self.case, BOOTSTRAP, self.args('render'))

    def test_session_positive(self):
        self.assertEqual(p.validate(self.case, Path(self.location))['clusters'], p.CLUSTERS)

    def test_session_forbids_real_secret(self):
        self.case['credentials'] = {'application_credential_secret': 'never-save-this'}
        with self.assertRaisesRegex(p.Refused, 'never in case'):
            p.validate(self.case, Path(self.location))

    def test_session_rejects_case_in_installed_lab(self):
        with self.assertRaisesRegex(p.Refused, 'outside'):
            p.validate(self.case, self.root / 'case.json')

    def test_relative_input_rejected(self):
        self.case['inventory'] = 'hosts.yml'
        with self.assertRaisesRegex(p.Refused, 'absolute'):
            p.validate(self.case, Path(self.location))

    def test_wrong_cluster_mapping_rejected(self):
        self.case['clusters'] = {'mediator': 'wrong'}
        with self.assertRaises(p.Refused):
            p.validate(self.case, Path(self.location))

    def test_exact_source_pin(self):
        self.assertEqual(p.pinned(self.case), BOOTSTRAP)
        with patch.object(p, 'run', return_value='0' * 40):
            with self.assertRaisesRegex(p.Refused, 'exactly'):
                p.pinned(self.case)

    def test_modified_tracked_source_rejected(self):
        with patch.object(p, 'run', side_effect=[p.PIN, 'scripts/render-spoke-manifests.py']):
            with self.assertRaisesRegex(p.Refused, 'modified'):
                p.pinned(self.case)

    def test_render_three_named_clusters_real_upstream(self):
        self.prepared()
        for name in p.CLUSTERS.values():
            docs = list(yaml.safe_load_all((self.output / name / 'cluster.yaml').read_text()))
            self.assertEqual(next(x for x in docs if x['kind'] == 'GovStackSpoke')['metadata']['name'], name)
            apps = list(yaml.safe_load_all((self.output / name / 'foundations.yaml').read_text()))
            cert = next(x for x in apps if x['kind'] == 'Application' and x['metadata']['name'].endswith('-cert-manager'))
            self.assertEqual(cert['spec']['destination']['name'], name)

    def test_wrong_image_version_rejected(self):
        self.image.write_text(json.dumps({'id': '12345678-1234-1234-1234-123456789abc', 'status': 'active', 'kubernetes_version': 'v1.35.1'}))
        with patch.object(p, 'output_root', return_value=self.output), self.assertRaisesRegex(p.Refused, 'image version'):
            p.render(self.case, BOOTSTRAP, self.args('render'))

    def test_bootstrap_preparation_never_starts_ansible(self):
        args = self.args('bootstrap', stage='all', execute=False, confirm=None)
        args.target = 'management'
        with patch.object(p, 'run', side_effect=AssertionError('process unexpectedly started')), contextlib.redirect_stdout(io.StringIO()) as out:
            p.bootstrap(self.case, BOOTSTRAP, args)
        self.assertIn('20-bootstrap-infrastructure.yml', out.getvalue())
        self.assertIn('PREPARED', out.getvalue())

    def test_bootstrap_without_confirmation_rejected(self):
        args = self.args('bootstrap', stage='infrastructure', execute=True, confirm=None)
        args.target = 'management'
        with patch.object(p, 'run', side_effect=AssertionError('process unexpectedly started')), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(p.Refused, 'confirmation'):
                p.bootstrap(self.case, BOOTSTRAP, args)

    def test_example_bootstrap_rejected_even_with_confirmation(self):
        args = self.args('bootstrap', stage='infrastructure', execute=True, confirm='bootstrap:management')
        args.target = 'management'
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(p.Refused, 'example'):
            p.bootstrap(self.case, BOOTSTRAP, args)

    def test_child_credential_path_refuses_before_process(self):
        args = self.args('bootstrap', stage='all', execute=False, confirm=None)
        args.target = 'mediator'
        with patch.object(p, 'run', side_effect=AssertionError('process unexpectedly started')), self.assertRaisesRegex(p.Refused, 'CREDENTIAL_BOOTSTRAP_BLOCKED'):
            p.bootstrap(self.case, BOOTSTRAP, args)

    def test_scale_positive_and_named_write_confirmation(self):
        self.prepared()
        args = self.args('scale', workers=3, control_plane=None, write=False, confirm=None)
        args.target = 'mediator'
        target = self.output / 'information-mediator/cluster.yaml'
        before = target.read_bytes()
        with patch.object(p, 'output_root', return_value=self.output), contextlib.redirect_stdout(io.StringIO()):
            p.lifecycle(self.case, BOOTSTRAP, args)
            self.assertEqual(target.read_bytes(), before)
            args.write = True
            args.confirm = 'scale:example-workloads'
            with self.assertRaisesRegex(p.Refused, 'scale:information-mediator'):
                p.lifecycle(self.case, BOOTSTRAP, args)
            self.assertEqual(target.read_bytes(), before)
            args.confirm = 'scale:information-mediator'
            p.lifecycle(self.case, BOOTSTRAP, args)
        spec = next(x for x in yaml.safe_load_all(target.read_text()) if x['kind'] == 'GovStackSpoke')['spec']
        self.assertEqual(spec['workers']['replicas'], 3)

    def test_invalid_control_plane_step(self):
        self.prepared()
        args = self.args('scale', workers=None, control_plane=5, write=False, confirm=None)
        args.target = 'examples'
        with patch.object(p, 'output_root', return_value=self.output), self.assertRaisesRegex(p.Refused, '1<->3 or 3<->5'):
            p.lifecycle(self.case, BOOTSTRAP, args)

    def test_replace_is_prepare_only(self):
        self.prepared()
        args = self.args('replace', pool='workers', write=False, confirm=None)
        args.target = 'examples'
        target = self.output / 'example-workloads/cluster.yaml'
        before = target.read_bytes()
        with patch.object(p, 'output_root', return_value=self.output), contextlib.redirect_stdout(io.StringIO()):
            p.lifecycle(self.case, BOOTSTRAP, args)
        self.assertEqual(target.read_bytes(), before)

    def test_upgrade_matching_image_preserves_local_inputs(self):
        self.prepared()
        image = self.root / 'next-image.json'
        image.write_text(json.dumps({'id': '12345678-1234-1234-1234-123456789abd', 'status': 'active', 'kubernetes_version': 'v1.37.1'}))
        args = self.args('upgrade', image=str(image), kubernetes_version='v1.37.1', write=False, confirm=None)
        args.target = 'examples'
        target = Path(self.case['cluster_configs']['examples'])
        before = target.read_bytes()
        with patch.object(p, 'output_root', return_value=self.output), contextlib.redirect_stdout(io.StringIO()):
            p.lifecycle(self.case, BOOTSTRAP, args)
        self.assertEqual(target.read_bytes(), before)

    def test_routing_uses_private_envoy_and_per_cluster_certificates(self):
        with patch.object(p, 'output_root', return_value=self.output), contextlib.redirect_stdout(io.StringIO()):
            p.route(self.case, BOOTSTRAP, self.args('route'))
        directory = self.output.parent / 'routing'
        values = yaml.safe_load((directory / 'edge-values.yaml').read_text())
        self.assertEqual(len(values['routes']), 2)
        for role in ('mediator', 'examples'):
            route = next(x for x in values['routes'] if x['name'] == p.CLUSTERS[role])
            self.assertEqual(route['backendAddress'], self.case['routing']['private_ingress'][role])
            docs = list(yaml.safe_load_all((directory / (p.CLUSTERS[role] + '-probe.yaml')).read_text()))
            self.assertEqual(next(x for x in docs if x['kind'] == 'Certificate')['spec']['dnsNames'], [self.case['domains'][role]])
            self.assertEqual(next(x for x in docs if x['kind'] == 'HTTPProxy')['spec']['routes'][0]['services'][0]['name'], 'chapter5-probe')
        helm_docs = list(yaml.safe_load_all((directory / 'edge-rendered.yaml').read_text()))
        config = next(x for x in helm_docs if x and x['kind'] == 'ConfigMap')['data']['envoy.yaml']
        self.assertIn('tls_inspector', config)
        self.assertIn('information-mediator', config)

    def test_duplicate_ingress_rejected(self):
        self.case['routing']['private_ingress']['examples'] = self.case['routing']['private_ingress']['mediator']
        with self.assertRaisesRegex(p.Refused, 'must differ'):
            p.route(self.case, BOOTSTRAP, self.args('route'))

    def test_context_gate_rejects_wrong_endpoint(self):
        fake = {'clusters': [{'cluster': {'server': 'https://wrong.example.test'}}], 'contexts': [{'name': self.case['management_context']}]}
        with patch.object(p, 'run', return_value=json.dumps(fake)), self.assertRaisesRegex(p.Refused, 'management_server'):
            p.context_gate(self.case)

    def test_probe_example_never_contacts_network(self):
        args = self.args('probe')
        args.target = 'mediator'
        with patch.object(p, 'run', side_effect=AssertionError('process unexpectedly started')), self.assertRaisesRegex(p.Refused, 'example'):
            p.probe(self.case, args)

    def test_handoff_marks_prepared_not_live(self):
        self.prepared()
        with patch.object(p, 'output_root', return_value=self.output), contextlib.redirect_stdout(io.StringIO()):
            p.handoff(self.case, BOOTSTRAP, self.args('handoff', live=False))
        result = json.loads((self.output.parent / 'handoff.json').read_text())
        self.assertEqual(result['evidence'], 'prepared-only')
        self.assertEqual(result['clusters'], p.CLUSTERS)

    def handoff_objects(self):
        self.prepared()
        self.case.update(mode='live', case_id='offline-handoff-case')
        objects = []
        for name in p.CLUSTERS.values():
            desired = next(x for x in yaml.safe_load_all((self.output / name / 'cluster.yaml').read_text())
                           if x and x.get('kind') == 'GovStackSpoke')
            obj = copy.deepcopy(desired)
            obj['metadata'].update(uid='offline-' + name, generation=4)
            obj['status'] = {'phase': 'Ready', 'observedGeneration': 4, 'clusterUID': 'cluster-' + name,
                             'conditions': [], **{pool: {'desired': obj['spec'][pool]['replicas'],
                                                        'ready': obj['spec'][pool]['replicas']}
                                                for pool in ('controlPlane', 'workers')}}
            objects.append(obj)
        return objects

    def live_handoff(self, objects):
        (self.output.parent / 'handoff.json').unlink(missing_ok=True)
        with patch.object(p, 'output_root', return_value=self.output), \
             patch.object(p, 'context_gate', return_value=('offline-management', self.case['management_server'])), \
             patch.object(p, 'run', side_effect=[json.dumps(obj) for obj in objects]), \
             patch.object(p, 'probe') as probes, contextlib.redirect_stdout(io.StringIO()):
            p.handoff(self.case, BOOTSTRAP, self.args('handoff', live=True))
        return probes

    def test_handoff_rejects_stale_ready_generation(self):
        objects = self.handoff_objects()
        objects[0]['status']['observedGeneration'] = 3
        with self.assertRaisesRegex(p.Refused, 'generation'):
            self.live_handoff(objects)
        self.assertFalse((self.output.parent / 'handoff.json').exists())

    def test_handoff_rejects_changed_desired_spec(self):
        baseline = self.handoff_objects()
        for pool in ('controlPlane', 'workers'):
            for field, value in (('replicas', 3), ('rolloutAfter', '2026-10-01T00:00:00Z')):
                with self.subTest(pool=pool, field=field):
                    objects = copy.deepcopy(baseline)
                    objects[0]['spec'][pool][field] = value
                    with self.assertRaisesRegex(p.Refused, 'desired'):
                        self.live_handoff(objects)

    def test_handoff_rejects_incomplete_ready_counts(self):
        baseline = self.handoff_objects()
        for pool in ('controlPlane', 'workers'):
            for field in ('desired', 'ready'):
                with self.subTest(pool=pool, field=field):
                    objects = copy.deepcopy(baseline)
                    objects[0]['status'][pool][field] = 0
                    with self.assertRaisesRegex(p.Refused, 'count'):
                        self.live_handoff(objects)

    def test_handoff_rejects_missing_identity_or_deletion(self):
        baseline = self.handoff_objects()
        for field, value in (('uid', None), ('generation', None), ('deletionTimestamp', '2026-10-01T00:00:00Z')):
            with self.subTest(field=field):
                objects = copy.deepcopy(baseline)
                objects[0]['metadata'][field] = value
                with self.assertRaises(p.Refused):
                    self.live_handoff(objects)

    def test_handoff_partial_live_scope_and_snapshots(self):
        objects = self.handoff_objects()
        probes = self.live_handoff(objects)
        result = json.loads((self.output.parent / 'handoff.json').read_text())
        self.assertEqual(result['schema'], 'chapter5-handoff/v1')
        self.assertEqual(result['evidence'], 'partial-live-readback')
        self.assertEqual(result['case_id'], self.case['case_id'])
        self.assertEqual(result['evidence_scope'], 'GovStackSpoke readback and two HTTPS edge marker probes only')
        self.assertIn('runtime acceptance', ' '.join(result['limitations']))
        self.assertIn('backend/Envoy/Service/Pod identity', ' '.join(result['limitations']))
        self.assertEqual(probes.call_count, 2)
        self.assertEqual([call.args[1].target for call in probes.call_args_list], ['mediator', 'examples'])
        for role, obj in zip(p.CLUSTERS, objects):
            self.assertEqual(result['spoke_snapshots'][role]['uid'], obj['metadata']['uid'])
            self.assertEqual(result['spoke_snapshots'][role]['generation'], 4)
            self.assertEqual(result['spoke_snapshots'][role]['status'], obj['status'])

    def test_retire_never_deletes(self):
        with patch.object(p, 'run', side_effect=AssertionError('process unexpectedly started')), self.assertRaisesRegex(p.Refused, 'RETIRE_BLOCKED'):
            p.retirement_blocker(BOOTSTRAP)

    def test_bounded_subprocess(self):
        with self.assertRaisesRegex(p.Refused, 'exceeded 1s'):
            p.run([sys.executable, '-c', 'import time; time.sleep(30)'], timeout=1)

    def test_probe_local_tls_real_curl(self):
        # Failing regression test for configurable HTTPS port: no privileged bind,
        # no cloud, DNS or public network connection.
        cert, key = self.root / 'certificate.pem', self.root / 'key.pem'
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
                        '-subj', '/CN=offline.example.org', '-addext', 'subjectAltName=DNS:offline.example.org',
                        '-keyout', str(key), '-out', str(cert)], check=True, capture_output=True, timeout=15)
        class Handler(BaseHTTPRequestHandler):
            body = b'information-mediator'
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-Length', str(len(self.body)))
                self.end_headers()
                self.wfile.write(self.body)
            def log_message(self, format, *args):
                pass
        server = HTTPServer(('127.0.0.1', 0), Handler)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            self.case.update(mode='live', tls={'mode': 'lab-ca', 'ca_file': str(cert)})
            self.case['domains']['mediator'] = 'offline.example.org'
            self.case['routing'].update(public_edge='127.0.0.1', public_edge_port=server.server_port)
            args = self.args('probe')
            args.target = 'mediator'
            with contextlib.redirect_stdout(io.StringIO()) as out:
                p.probe(self.case, args)
            self.assertIn('PROBE_OK', out.getvalue())
            Handler.body = b'wrong-cluster'
            with self.assertRaisesRegex(p.Refused, 'wrong response marker'):
                p.probe(self.case, args)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

if __name__ == '__main__':
    unittest.main(verbosity=2)
