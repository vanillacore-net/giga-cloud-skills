#!/usr/bin/env python3
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
