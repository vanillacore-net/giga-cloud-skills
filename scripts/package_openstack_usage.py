#!/usr/bin/env python3
"""Build standalone OpenStack usage kits from reviewed repository sources."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
DOMAINS = ('environment', 'compute', 'networking', 'storage', 'troubleshooting')
VERIFY = '''#!/usr/bin/env python3
"""Verify sealed operator files before adding local context, plans or evidence."""
import hashlib
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
try:
    for line in (root / 'MANIFEST.sha256').read_text().splitlines():
        digest, relative = line.split('  ', 1)
        if Path(relative).is_absolute() or '..' in Path(relative).parts:
            raise ValueError('unsafe manifest path')
        path = root / relative
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('unsafe artifact path')
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('checksum mismatch')
except (OSError, ValueError):
    print('operator kit verification failed; use the complete reviewed installation', file=sys.stderr)
    raise SystemExit(2)
print('operator kit checksums passed')
'''


def manifest(kit: Path):
    entries = []
    for path in sorted(kit.rglob('*')):
        if path.is_file() and path.name != 'MANIFEST.sha256' and '__pycache__' not in path.parts:
            if path.is_symlink() or not path.resolve().is_relative_to(kit.resolve()):
                raise ValueError('unsafe packaged file')
            entries.append(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(kit)}')
    (kit / 'MANIFEST.sha256').write_text('\n'.join(entries) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-commit', help='Reviewed commit containing the unchanged runtime and API contract')
    args = parser.parse_args()
    if args.source_commit and not re.fullmatch(r'[0-9a-f]{40}', args.source_commit):
        raise ValueError('source commit must be a full Git SHA')
    runtime = ROOT / 'runtime/openstack_ops.py'
    api = ROOT / 'docs/openstack-operations-api.md'
    if not runtime.is_file() or not api.is_file():
        raise SystemExit('runtime or operations API missing')
    digest = hashlib.sha256(runtime.read_bytes()).hexdigest()
    for domain in DOMAINS:
        skill = ROOT / 'skills' / f'openstack-{domain}'
        kit = skill / 'assets/operator-kit'
        (kit / 'scripts').mkdir(parents=True, exist_ok=True)
        shutil.copyfile(runtime, kit / 'scripts/openstack_ops.py')
        (kit / 'scripts/verify_kit.py').write_text(VERIFY)
        (skill / 'references').mkdir(exist_ok=True)
        shutil.copyfile(api, skill / 'references/operations-api.md')
        source = '# OpenStack usage operator-kit source\n\n'
        source += '- Source repository: https://git.vanillacore.net/giga/cloud-skills\n'
        source += '- Release: 0.5.0\n'
        source += '- Runtime source path: `runtime/openstack_ops.py`\n'
        source += f'- Runtime SHA-256: `{digest}`\n'
        if args.source_commit:
            source += f'- Reviewed runtime/API source commit: `{args.source_commit}`\n'
        else:
            source += '- Draft source state: source commit is recorded after reviewed source commit.\n'
        source += '\nThis kit contains newly authored tenant-operation tooling, not a mutable link to the chapter lab. Local input, plans, approvals, credentials and evidence belong only to a protected working copy. The OpenStack client is an external dependency; its command syntax is checked against version 8.2.0. Offline fixture tests do not establish live cloud acceptance.\n'
        (kit / 'SOURCE.md').write_text(source)
        (kit / 'THIRD_PARTY_NOTICES.md').write_text('# Dependency notices\n\nThe Python runtime and kit verifier are authored for this package. No OpenStack client, SDK, upstream deployment manifest or credential material is redistributed in this kit. OpenStackClient is installed separately and governed by its upstream Apache-2.0 license and dependency notices: https://opendev.org/openstack/python-openstackclient\n')
        manifest(kit)
    manifest(ROOT / 'skills/kubernetes-cluster-lifecycle-practitioner/assets/operator-kit')
    print('Packaged five standalone usage kits and regenerated repaired Chapter 4 kit manifest.')


if __name__ == '__main__':
    main()
