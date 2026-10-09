"""Bounded credential-pattern check of Git history and tracked working files.

Prints paths only, never matching credential text. This is not a universal
secret detector; provider-specific patterns and environment-file tracking are
checked before public source publication.
"""
import re
import subprocess
from pathlib import Path

PATTERNS = [
    rb"gh[pousr]_[A-Za-z0-9]{20,}", rb"github_pat_[A-Za-z0-9_]{40,}",
    rb"AKIA[A-Z0-9]{16}", rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    rb"rnd_[A-Za-z0-9]{20,}", rb"sk-(?:proj-)?[A-Za-z0-9_-]{40,}",
]


def main():
    failures = set()
    checked = 0
    objects = subprocess.check_output(['git', 'rev-list', '--objects', '--all']).decode().splitlines()
    for record in objects:
        parts = record.split(' ', 1)
        if len(parts) != 2:
            continue
        oid, path = parts
        if subprocess.check_output(['git', 'cat-file', '-t', oid]).strip() != b'blob':
            continue
        data = subprocess.check_output(['git', 'cat-file', 'blob', oid])
        checked += 1
        if any(re.search(pattern, data) for pattern in PATTERNS):
            failures.add(path)
    for path in subprocess.check_output(['git', 'ls-files']).decode().splitlines():
        target = Path(path)
        if target.name.startswith('.env') and target.name != '.env.example':
            failures.add(path)
        if target.is_file() and any(re.search(pattern, target.read_bytes()) for pattern in PATTERNS):
            failures.add(path)
    if failures:
        print('Credential checks failed for paths: ' + ', '.join(sorted(failures)))
        return 1
    print(f'Credential-pattern check passed ({checked} historical blobs plus tracked working files).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
