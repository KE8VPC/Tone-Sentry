"""Verify supplied source/resources before installing; does not access receiver data."""
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
manifest = json.loads((base / 'PACKAGE-INFO.json').read_text(encoding='utf-8'))
for relative, expected in manifest['files_sha256'].items():
    path = (base / relative).resolve()
    if not path.is_relative_to(base) or not path.is_file():
        raise SystemExit('Missing or invalid package file: ' + relative)
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise SystemExit('Package checksum mismatch: ' + relative)
print('Package files verified: Tone Sentry ' + manifest['version'])
