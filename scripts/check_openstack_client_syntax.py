#!/usr/bin/env python3
"""Check every emitted CLI option against real client help. No cloud calls."""
import argparse
import importlib.util
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PREFIXES = {
    'server-create': 'server create', 'server-start': 'server start',
    'server-stop': 'server stop', 'server-reboot': 'server reboot',
    'server-resize': 'server resize', 'server-resize-confirm': 'server resize confirm',
    'server-resize-revert': 'server resize revert', 'server-delete': 'server delete',
    'network-create': 'network create', 'subnet-create': 'subnet create',
    'router-create': 'router create', 'router-add-subnet': 'router add subnet',
    'router-set-external': 'router set', 'security-group-create': 'security group create',
    'security-rule-create': 'security group rule create',
    'security-rule-delete': 'security group rule delete',
    'floating-ip-create': 'floating ip create', 'floating-ip-associate': 'floating ip set',
    'floating-ip-disassociate': 'floating ip unset', 'floating-ip-delete': 'floating ip delete',
    'volume-create': 'volume create', 'volume-attach': 'server add volume',
    'volume-detach': 'server remove volume', 'volume-extend': 'volume set',
    'volume-snapshot': 'volume snapshot create', 'volume-from-snapshot': 'volume create',
    'volume-delete': 'volume delete',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', default='openstack')
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('usage_ops', ROOT / 'runtime/openstack_ops.py')
    assert spec is not None and spec.loader is not None
    ops = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ops)
    if set(PREFIXES) != set(ops.FIELDS):
        raise SystemExit('Syntax check action inventory does not match the executable catalogue')
    version = subprocess.run([args.client, '--version'], capture_output=True, text=True, timeout=15, check=True)
    checked = 0
    for action, (required, optional) in ops.FIELDS.items():
        parameters = {}
        for field in (required + ' ' + optional).split():
            if field in ops.TYPES:
                value = '33333333-3333-4333-8333-333333333333'
            elif field in {'confirm_delete', 'allow_external', 'allow_world'}:
                value = True
            elif field in {'size_gib', 'port_min', 'port_max'}:
                value = 22
            elif field in {'cidr', 'remote_cidr'}:
                value = '192.0.2.0/24'
            elif field in {'fixed_ip', 'gateway'}:
                value = '192.0.2.10'
            elif field == 'protocol':
                value = 'tcp'
            elif field == 'data_policy':
                value = 'delete' if action.endswith('-delete') else 'retain'
            else:
                value = 'syntax-fixture'
            parameters[field] = value
        request = ops.request({'action': action, 'parameters': parameters})
        emitted = ops.build(request)[1]
        prefix = PREFIXES[action].split()
        if emitted[:len(prefix)] != prefix:
            raise SystemExit(f'Command prefix differs for {action}')
        result = subprocess.run([args.client, *prefix, '--help'], capture_output=True, text=True, timeout=20)
        if result.returncode:
            raise SystemExit(f'Client help failed for {action}')
        advertised = set(re.findall(r'(?<![\w-])--[\w-]+', result.stdout))
        emitted_options = {word for word in emitted if word.startswith('--')}
        missing = emitted_options - advertised
        if missing:
            raise SystemExit(f'Unadvertised options for {action}: {sorted(missing)}')
        checked += 1
    print(f'CLIENT SYNTAX PASSED: {checked} supported actions; {version.stdout.strip()}; help-only, no API calls')


if __name__ == '__main__':
    main()
