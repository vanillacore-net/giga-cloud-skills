#!/usr/bin/env python3
"""Chapter 5: prepare locally; delegate platform changes to pinned Bootstrap.

Every command accepts --case. bootstrap is a plan unless --execute is supplied.
scale/replace/upgrade validate without writing unless --write is supplied. No
command commits, pushes, applies routing manifests, or deletes cloud resources.
"""
from __future__ import annotations
import argparse
import ipaddress
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import yaml

PIN = '1195f539afe5a1018be07d2e1865824c225ee407'
CLUSTERS = {'loadbalancer': 'loadbalancer', 'mediator': 'information-mediator', 'examples': 'example-workloads'}
LAB = Path(__file__).resolve().parents[1]
STAGES = {'infrastructure': '20-bootstrap-infrastructure.yml', 'gateway': '30-bootstrap-gateway.yml',
          'seed': '40-bootstrap-management-seed.yml', 'providers': '50-bootstrap-capi-capo.yml',
          'argocd': '60-bootstrap-argocd.yml', 'bridge': '61-bootstrap-spoke-management.yml',
          'dashboard': '62-deploy-dashboard-management.yml', 'image': '70-build-capo-image.yml'}

class Refused(Exception):
    pass


def require(condition, message):
    if not condition:
        raise Refused(message)


def run(command, cwd=None, timeout=120, env=None, stdin=None):
    """Kill the entire subprocess group at the deadline, including grandchildren."""
    require(1 <= timeout <= 7200, 'timeout must be 1..7200 seconds')
    process = subprocess.Popen([str(x) for x in command], cwd=cwd, env=env,
                               stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                               start_new_session=True)
    try:
        stdout, stderr = process.communicate(stdin, timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise Refused(f'command exceeded {timeout}s; stopped process group; inspect state before retry')
    require(process.returncode == 0, f'upstream command failed ({process.returncode}): {stderr.strip()}')
    return stdout


def absolute(value, label):
    require(isinstance(value, str) and Path(value).is_absolute(), f'{label} must be an absolute path')
    return Path(value).resolve()


def no_secrets(value):
    if isinstance(value, dict):
        for key, item in value.items():
            require(not re.search(r'^(password|token|private_key|application_credential_secret|client_secret|secret)$', key),
                    f'{key}: store credentials in files/environment; never in case.json')
            no_secrets(item)
    elif isinstance(value, list):
        for item in value:
            no_secrets(item)


def outside(path, roots, label):
    require(not any(path == root or path.is_relative_to(root) for root in roots),
            f'{label} must be outside the source checkout and installed lab')


def validate(case, location):
    require(case.get('schema') == 'platform-session/v1', 'schema must be platform-session/v1')
    no_secrets(case)
    repo = absolute(case.get('bootstrap_repo'), 'bootstrap_repo')
    require(case.get('clusters') == CLUSTERS, 'clusters must use the three Chapter 5 names')
    require(isinstance(case.get('cluster_configs'), dict) and set(case['cluster_configs']) == set(CLUSTERS),
            'cluster_configs must map loadbalancer, mediator and examples to files')
    for key in ('environment_config', 'inventory', 'infrastructure_outputs', 'image_metadata'):
        absolute(case.get(key), key)
    for role, path in case['cluster_configs'].items():
        absolute(path, f'cluster_configs.{role}')
    require(isinstance(case.get('management_context'), str) and case['management_context'], 'management_context is required')
    require(set(case.get('domains', {})) == {'mediator', 'examples'}, 'domains needs mediator and examples')
    for domain in case['domains'].values():
        require(isinstance(domain, str) and re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?', domain)
                and '.' in domain, 'domains must be explicit lower-case DNS hostnames, not wildcards')
    require(len(set(case['domains'].values())) == 2, 'each workload cluster needs a distinct hostname')
    require(isinstance(case.get('tls'), dict) and case['tls'].get('mode') in ('trusted', 'lab-ca'), 'tls.mode must be trusted or lab-ca')
    if case['tls']['mode'] == 'lab-ca':
        absolute(case['tls'].get('ca_file'), 'tls.ca_file')
    outside(location.resolve(), [repo, LAB], 'case.json')
    return case


def load_case(path):
    path = Path(path).expanduser().resolve()
    return validate(json.loads(path.read_text()), path)


def pinned(case):
    repo = Path(case['bootstrap_repo'])
    require(run(['git', 'rev-parse', 'HEAD'], cwd=repo).strip() == PIN, f'Bootstrap checkout must be exactly {PIN}')
    # Ignore untracked operator files but never execute modified tracked tools/templates.
    require(not run(['git', 'diff', '--name-only', 'HEAD'], cwd=repo).strip(), 'tracked Bootstrap source is modified; restore the pinned checkout')
    return repo


def yaml_file(path):
    document = yaml.safe_load(Path(path).read_text())
    require(isinstance(document, dict), f'{path}: expected YAML mapping')
    return document


def declaration(case, role):
    path = Path(case['cluster_configs'][role])
    spec = yaml_file(path).get('cluster', {})
    require(spec.get('name') == CLUSTERS[role], f'{role}: cluster.name must be {CLUSTERS[role]}')
    require(spec.get('namespace', 'govstack-clusters') == 'govstack-clusters', 'only govstack-clusters is supported')
    require(spec.get('role') == ('loadbalancer' if role == 'loadbalancer' else 'spoke'), f'{role}: wrong cluster.role')
    return path, spec


def output_root(case, location):
    root = absolute(case.get('output_root', str(Path(location).resolve().parent / 'generated/spokes')), 'output_root')
    outside(root, [Path(case['bootstrap_repo']).resolve(), LAB], 'output_root')
    return root


def confirm(args, target):
    expected = f'{args.command}:{target}'
    require(args.confirm == expected, f'confirmation required: --confirm {expected}')


def kubectl(case, *args, context=None):
    command = ['kubectl']
    if case.get('kubeconfig'):
        command += ['--kubeconfig', str(absolute(case['kubeconfig'], 'kubeconfig'))]
    command += ['--context', context or case['management_context'], '--request-timeout=20s', *args]
    return command


def context_gate(case):
    context = case['management_context']
    command = kubectl(case, 'config', 'view', '--minify', '-o', 'json')
    # config view is local: credentials are not emitted (--raw is deliberately absent).
    config = json.loads(run(command))
    require(len(config.get('clusters', [])) == 1 and len(config.get('contexts', [])) == 1, 'context selection must resolve exactly one cluster')
    server = config['clusters'][0]['cluster']['server']
    require(case.get('management_server') == server, 'management_server must match the explicitly reviewed context API endpoint')
    require(config['contexts'][0]['name'] == context, 'selected context differs from management_context')
    return context, server


def render(case, repo, args):
    roles = list(CLUSTERS) if args.target == 'all' else [args.target]
    root = output_root(case, args.case)
    environment = yaml_file(case['environment_config'])
    image = json.loads(Path(case['image_metadata']).read_text())
    require(re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', str(image.get('id', ''))), 'image metadata needs a real Glance UUID (not a display name)')
    require(image.get('status') == 'active', 'image metadata status must be active')
    for role in roles:
        config, spec = declaration(case, role)
        require(image.get('kubernetes_version') == spec.get('kubernetes_version'), 'image version must equal cluster Kubernetes version')
        require(not (root / CLUSTERS[role]).exists(), 'render destination exists; use a fresh external output_root or review lifecycle edits first')
        command = [sys.executable, repo / 'scripts/render-spoke-manifests.py', '--cluster', config,
                   '--environment', case['environment_config'], '--infrastructure-outputs', case['infrastructure_outputs'],
                   '--image', case['image_metadata'], '--output-root', root]
        print(run(command, timeout=args.timeout).strip())
        print(f'RENDERED {CLUSTERS[role]}: local manifests only; no reconciliation or credential creation')


def bootstrap(case, repo, args):
    environment = yaml_file(case['environment_config'])
    name = environment.get('bootstrap_environment')
    require(isinstance(name, str) and re.fullmatch(r'[a-z0-9][a-z0-9-]*', name), 'environment needs bootstrap_environment')
    if args.target != 'management':
        declaration(case, args.target)
        raise Refused('CREDENTIAL_BOOTSTRAP_BLOCKED: playbook 80 includes credential creation and child reconciliation; '
                      'there is no credential-only tag/flag. capo_dry_run_only stops AFTER credential/namespace/Secret writes '
                      'and waits for GitOps ownership if the declaration exists. Obtain an approved credential-only integration '
                      'or separately approved full transitional 80/90 procedure; do not publish a new Spoke first.')
    apply = getattr(args, 'apply', False)
    require(not apply or (args.execute and args.stage == 'infrastructure'),
            '--apply requires --execute and --stage infrastructure')
    selected = list(STAGES) if args.stage == 'all' else [args.stage]
    command = []
    for stage in selected:
        command = ['ansible-playbook', '-i', case['inventory'], repo / 'playbooks' / STAGES[stage],
                   '-e', '@' + case['environment_config'], '-e', json.dumps({'environment_config_file': case['environment_config'],
                    'infrastructure_outputs_file': case['infrastructure_outputs'], 'outputs_file': case['infrastructure_outputs'],
                    'image_file': case['image_metadata'], 'bootstrap_apply': bool(apply)})]
        print(json.dumps({'stage': stage, 'argv': [str(x) for x in command]}))
    if not args.execute:
        print('PREPARED bootstrap:management; no Ansible process started')
        return
    require(args.stage != 'all', 'execute one stage at a time and inspect its result; --stage all is preparation only')
    confirm(args, 'management:apply' if apply else 'management')
    require(case.get('mode') != 'example', 'example sessions can never execute bootstrap')
    require(environment.get('bootstrap_profile') == 'integration-test', 'pinned infrastructure supports disposable integration-test targets only')
    controller = environment.get('controller', {})
    require(controller.get('expected_hostname') == case.get('controller_hostname') and controller.get('inventory_host') == case.get('controller_inventory_host'),
            'explicit reviewed controller_hostname and controller_inventory_host must match environment')
    if args.stage not in ('infrastructure', 'gateway', 'seed'):
        context_gate(case)
        # Upstream Ansible reaches seed via SSH, not the local context. Match its API VIP to reviewed endpoint.
        from urllib.parse import urlparse
        require(urlparse(case['management_server']).hostname == environment.get('infrastructure', {}).get('api_vip'),
                'upstream seed API VIP must match reviewed management_server')
    print(run(command, cwd=repo, timeout=args.timeout).strip())
    print('UPSTREAM_COMPLETED: inspect recap and resource read-back before the next stage')


def lifecycle(case, repo, args):
    config, spec = declaration(case, args.target)
    root = output_root(case, args.case)
    target = CLUSTERS[args.target]
    command = [sys.executable, repo / 'scripts/spoke-lifecycle.py', args.command]
    if args.command == 'upgrade':
        image_path = absolute(args.image, '--image')
        command += ['--cluster', config, '--environment', case['environment_config'], '--infrastructure-outputs', case['infrastructure_outputs'],
                    '--image', image_path, '--kubernetes-version', args.kubernetes_version, '--output-root', root]
        if args.write:
            outside(config.resolve(), [repo.resolve(), LAB], 'upgrade declaration')
    else:
        command += ['--spoke', root / target]
        if args.command == 'scale':
            if args.workers is not None:
                command += ['--workers', str(args.workers)]
            if args.control_plane is not None:
                command += ['--control-plane', str(args.control_plane)]
        else:
            command += ['--pool', args.pool]
    if args.write:
        confirm(args, target)
    else:
        command += ['--dry-run']
    print(run(command, timeout=args.timeout).strip())
    print('LOCAL_CANDIDATE: no commit/push; no live rollout' if args.write else 'VALIDATED_ONLY: local inputs unchanged')


def route(case, repo, args):
    routing = case.get('routing', {})
    endpoints = routing.get('private_ingress', {})
    require(set(endpoints) == {'mediator', 'examples'}, 'routing.private_ingress needs both private per-cluster Envoy VIPs')
    for address in endpoints.values():
        ip = ipaddress.ip_address(address)
        require(ip.is_private and not ip.is_loopback and not ip.is_unspecified, 'private_ingress must be private non-loopback IP addresses')
    require(len(set(endpoints.values())) == 2, 'private ingress VIPs must differ')
    image = routing.get('probe_image', '')
    require(re.fullmatch(r'[^@\s]+@sha256:[0-9a-f]{64}', image), 'routing.probe_image must be digest-pinned and serve HTTP on port 8080')
    environment = yaml_file(case['environment_config'])
    edge_image = environment['cluster_foundations']['govstack_routing']['image']
    values = {'image': edge_image, 'routes': [{'name': CLUSTERS[role], 'domains': [case['domains'][role]],
               'backendAddress': endpoints[role], 'httpPort': 80, 'httpsPort': 443} for role in ('mediator', 'examples')],
              'status': {'enabled': False, 'hostname': ''}}
    destination = output_root(case, args.case).parent / 'routing'
    require(not destination.exists(), 'routing destination exists; review it or choose fresh output_root')
    issuer = case['tls'].get('issuer')
    require(isinstance(issuer, dict) and issuer.get('name') and issuer.get('kind') in ('Issuer', 'ClusterIssuer'), 'tls.issuer requires explicit name and kind; issuer creation/credentials are separate')
    # Validate the actual upstream Helm chart BEFORE publishing any local file.
    rendered = run(['helm', 'template', 'chapter5-edge', repo / 'charts/govstack-envoy-routing',
                    '--namespace', 'envoy-system', '-f', '-'], stdin=yaml.safe_dump(values), timeout=args.timeout)
    destination.mkdir(parents=True, mode=0o700)
    (destination / 'edge-values.yaml').write_text(yaml.safe_dump(values, sort_keys=False))
    (destination / 'edge-rendered.yaml').write_text(rendered)
    for role in ('mediator', 'examples'):
        marker = CLUSTERS[role]
        namespace = 'chapter5-probe'
        metadata = {'name': 'chapter5-probe', 'namespace': namespace}
        objects = [
            {'apiVersion': 'v1', 'kind': 'Namespace', 'metadata': {'name': namespace}},
            {'apiVersion': 'apps/v1', 'kind': 'Deployment', 'metadata': metadata,
             'spec': {'replicas': 2, 'selector': {'matchLabels': {'app': 'chapter5-probe'}}, 'template': {
                 'metadata': {'labels': {'app': 'chapter5-probe'}}, 'spec': {'containers': [{
                     'name': 'probe', 'image': image, 'args': ['-listen=:8080', '-text=' + marker],
                     'ports': [{'containerPort': 8080}], 'readinessProbe': {'httpGet': {'path': '/', 'port': 8080}}}]}}}},
            {'apiVersion': 'v1', 'kind': 'Service', 'metadata': metadata, 'spec': {'selector': {'app': 'chapter5-probe'}, 'ports': [{'port': 80, 'targetPort': 8080}]}},
            {'apiVersion': 'cert-manager.io/v1', 'kind': 'Certificate', 'metadata': metadata,
             'spec': {'secretName': 'chapter5-probe-tls', 'dnsNames': [case['domains'][role]], 'issuerRef': issuer}},
            {'apiVersion': 'projectcontour.io/v1', 'kind': 'HTTPProxy', 'metadata': metadata, 'spec': {
                'virtualhost': {'fqdn': case['domains'][role], 'tls': {'secretName': 'chapter5-probe-tls'}},
                'routes': [{'conditions': [{'prefix': '/'}], 'services': [{'name': 'chapter5-probe', 'port': 80}]}]}}
        ]
        (destination / f'{marker}-probe.yaml').write_text(yaml.safe_dump_all(objects, sort_keys=False))
    print(f'ROUTING_PREPARED {destination}: edge -> private Envoy -> Service -> Pods; TLS terminates per spoke; no apply')


def status(case, args):
    context_gate(case)
    resources = ['govstackspokes', 'clusters.cluster.x-k8s.io', 'machines.cluster.x-k8s.io']
    for resource in resources:
        selector = [] if args.target == 'all' else ['-l', 'govstack.itu.int/spoke=' + CLUSTERS[args.target]]
        print(run(kubectl(case, '-n', 'govstack-clusters', 'get', resource, *selector, '-o', 'json'), timeout=args.timeout))
    print('STATUS_READ: cluster readiness does not prove application routing')


def probe(case, args):
    require(case.get('mode') != 'example', 'example sessions cannot contact endpoints; exercise HTTP/TLS with tests instead')
    role = args.target
    domain = case['domains'][role]
    require(not domain.endswith(('.test', '.invalid')), 'reserved example domains are prepare-only')
    public_ip = str(ipaddress.ip_address(case.get('routing', {}).get('public_edge', '')))
    port = case.get('routing', {}).get('public_edge_port', 443)
    require(type(port) is int and 1 <= port <= 65535, 'public_edge_port must be 1..65535')
    require(ipaddress.ip_address(public_ip).version == 4, 'this probe contract currently requires an IPv4 public_edge')
    command = ['curl', '--silent', '--show-error', '--fail', '--noproxy', '*', '--connect-timeout', '5', '--max-time', '20',
               '--resolve', f'{domain}:{port}:{public_ip}', f'https://{domain}:{port}/']
    if case['tls']['mode'] == 'lab-ca':
        command += ['--cacert', case['tls']['ca_file']]
    body = run(command, timeout=min(args.timeout, 25)).strip()
    require(body == CLUSTERS[role], f'wrong response marker: expected {CLUSTERS[role]}')
    print(f'PROBE_OK {domain}: verified TLS and exact {CLUSTERS[role]} marker')


def retirement_blocker(repo):
    # Pinned source contract: dynamic ownership allowlist cannot describe the
    # renderer templates reliably; parent source review records exact details.
    require((repo / 'scripts/build-capi-allowlist.py').is_file() and (repo / 'scripts/delete-spoke-resources.sh').is_file(), 'teardown source contract missing')
    raise Refused('RETIRE_BLOCKED at pinned Bootstrap: teardown allowlist and fixed Application destinations '
                  'do not cover the rendered foundation contract. No delete command was started. Keep the Git '
                  'declaration and identities until a reviewed upstream fix plus renderer-to-teardown tests '
                  'prove exact UID ownership, workload-argocd/foundation-admission destinations, resource absence '
                  'and identity revocation. Do not use reset or strip finalizers as a workaround.')


def handoff(case, repo, args):
    root = output_root(case, args.case)
    for role in CLUSTERS:
        require((root / CLUSTERS[role] / 'cluster.yaml').is_file(), f'render {role} before exporting handoff')
    snapshots = {}
    if args.live:
        require(case.get('mode') != 'example', 'example cannot produce live evidence')
        context_gate(case)
        for role, name in CLUSTERS.items():
            declarations = [doc for doc in yaml.safe_load_all((root / name / 'cluster.yaml').read_text())
                            if isinstance(doc, dict) and doc.get('kind') == 'GovStackSpoke'
                            and doc.get('metadata', {}).get('name') == name]
            require(len(declarations) == 1, f'{name}: expected exactly one rendered desired GovStackSpoke')
            desired = declarations[0]['spec']
            obj = json.loads(run(kubectl(case, '-n', 'govstack-clusters', 'get', 'gss', name, '-o', 'json'), timeout=args.timeout))
            metadata, observed, actual = obj.get('metadata', {}), obj.get('status', {}), obj.get('spec', {})
            require(metadata.get('name') == name and metadata.get('namespace') == 'govstack-clusters',
                    f'{name}: unexpected readback identity')
            require(isinstance(metadata.get('uid'), str) and bool(metadata['uid']) and not metadata.get('deletionTimestamp'),
                    f'{name}: missing UID or deleting resource')
            generation = metadata.get('generation')
            require(type(generation) is int and generation > 0
                    and type(observed.get('observedGeneration')) is int
                    and observed['observedGeneration'] == generation, f'{name}: stale or missing observed generation')
            require(observed.get('phase') == 'Ready', f'{name} is not Ready')
            for pool in ('controlPlane', 'workers'):
                expected, current = desired.get(pool, {}), actual.get(pool, {})
                require(type(expected.get('replicas')) is int and expected['replicas'] >= 0
                        and type(current.get('replicas')) is int
                        and all(expected.get(key) == current.get(key) for key in ('replicas', 'rolloutAfter')),
                        f'{name}: {pool} differs from rendered desired spec')
                counts = observed.get(pool, {})
                require(all(type(counts.get(key)) is int and counts[key] == current['replicas']
                            for key in ('desired', 'ready')), f'{name}: {pool} status counts do not match desired replicas')
            snapshots[role] = {'uid': metadata['uid'], 'generation': generation,
                               'spec': actual, 'status': observed}
        for role in ('mediator', 'examples'):
            probe(case, argparse.Namespace(target=role, timeout=args.timeout))
    result = {'schema': 'chapter5-handoff/v1', 'case_id': case.get('case_id'), 'bootstrap_revision': PIN,
              'evidence': 'partial-live-readback' if args.live else 'prepared-only',
              'evidence_scope': 'GovStackSpoke readback and two HTTPS edge marker probes only' if args.live
                                else 'local rendered artifacts only; no live checks',
              'limitations': ['Not full backend/Envoy/Service/Pod identity verification or runtime acceptance.',
                              'Not a canonical platform_runtime_record/v1; construct and validate that record separately.'],
              'spoke_snapshots': snapshots,
              'clusters': CLUSTERS, 'domains': case['domains'], 'management_context': case['management_context'],
              'path': 'public edge -> private per-cluster Envoy -> Service -> Pods (intended topology, not identity-verified)',
              'tls': case['tls'],
              'chapter6_scope': 'Information Mediator and example applications are not installed by Chapter 5'}
    destination = root.parent / 'handoff.json'
    require(not destination.exists(), 'handoff already exists; do not silently replace evidence')
    destination.write_text(json.dumps(result, indent=2) + '\n')
    print(f'HANDOFF {destination}: {result["evidence"]}')


def parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='command', required=True)
    for command in ('init', 'doctor', 'bootstrap', 'render', 'route', 'probe', 'status', 'scale', 'replace', 'upgrade', 'retire', 'handoff'):
        s = sub.add_parser(command)
        s.add_argument('--case', default=str(Path.home() / '.local/state/chapter5/case.json'), help='absolute external session file')
        s.add_argument('--timeout', type=int, default=120, help='subprocess/group deadline in seconds (1..7200)')
        if command == 'init':
            s.add_argument('--inputs', required=True, help='operator-authored platform-session/v1 JSON; no secrets')
        if command == 'doctor':
            s.add_argument('--offline', action='store_true', help='local source/input checks only (default also offline)')
        if command in ('render', 'status'):
            s.add_argument('--target', choices=[*CLUSTERS, 'all'], default='all')
        if command == 'bootstrap':
            s.add_argument('--target', choices=['management', *CLUSTERS], required=True)
            s.add_argument('--stage', choices=['all', *STAGES], default='all')
            s.add_argument('--execute', action='store_true', help='run ONE upstream Management stage; mutates remote systems')
            s.add_argument('--apply', action='store_true', help='infrastructure only: enable upstream OpenTofu apply after separate approval')
            s.add_argument('--confirm', help='bootstrap:management, or bootstrap:management:apply for infrastructure apply; never saved in case')
        if command in ('scale', 'replace', 'upgrade', 'retire', 'probe'):
            s.add_argument('--target', choices=['mediator', 'examples'] if command == 'probe' else list(CLUSTERS), required=True)
        if command in ('scale', 'replace', 'upgrade'):
            s.add_argument('--write', action='store_true', help='write local candidate only, never commit/push')
            s.add_argument('--confirm', help='literal operation:actual-cluster-name')
        if command == 'scale':
            s.add_argument('--workers', type=int)
            s.add_argument('--control-plane', type=int)
        if command == 'replace':
            s.add_argument('--pool', choices=['workers', 'control-plane', 'all'], required=True)
        if command == 'upgrade':
            s.add_argument('--kubernetes-version', required=True)
            s.add_argument('--image', required=True, help='absolute matching next-version image metadata JSON')
        if command == 'retire':
            s.add_argument('--confirm', help='reserved for future reviewed contract; retirement is blocked at this pin')
        if command == 'handoff':
            s.add_argument('--live', action='store_true', help='read current GovStackSpoke generation/spec/counts and probe two edge markers; partial evidence only')
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        require(1 <= args.timeout <= 7200, 'timeout must be 1..7200 seconds')
        if args.command == 'init':
            path = Path(args.case).expanduser().resolve()
            case = validate(json.loads(Path(args.inputs).read_text()), path)
            pinned(case)
            require(not path.exists(), 'case already exists; edit/review it explicitly')
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as f:
                json.dump(case, f, indent=2)
                f.write('\n')
            print(f'INITIALIZED {path}: platform-session/v1; no cloud access')
            return 0
        case = load_case(args.case)
        repo = pinned(case)
        if args.command == 'doctor':
            for key in ('environment_config', 'inventory'):
                require(Path(case[key]).is_file(), f'{key} is missing')
            for role in CLUSTERS:
                declaration(case, role)
            artifacts = {key: Path(case[key]).is_file() for key in ('infrastructure_outputs', 'image_metadata')}
            print(json.dumps({'source': PIN, 'inputs': 'valid', 'artifacts_present': artifacts, 'evidence': 'offline-only',
                              'child_bootstrap': 'credential-only integration blocked', 'retire': 'source-contract blocked'}, indent=2))
        elif args.command == 'bootstrap':
            bootstrap(case, repo, args)
        elif args.command == 'render':
            render(case, repo, args)
        elif args.command in ('scale', 'replace', 'upgrade'):
            lifecycle(case, repo, args)
        elif args.command == 'route':
            route(case, repo, args)
        elif args.command == 'status':
            status(case, args)
        elif args.command == 'probe':
            probe(case, args)
        elif args.command == 'retire':
            retirement_blocker(repo)
        elif args.command == 'handoff':
            handoff(case, repo, args)
        return 0
    except (Refused, OSError, ValueError, KeyError, yaml.YAMLError) as error:
        print(f'REFUSED: {error}', file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
