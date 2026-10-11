"""Explicit private development source export; never a protected customer package."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--private-source', action='store_true')
if not parser.parse_args().private_source:
    parser.error('Source export requires --private-source. Use package_native_windows.py for a binary package.')
destination = root / "dist"
destination.mkdir(exist_ok=True)
archive = destination / "Tone-Sentry-0.8.0-private-development-source.zip"
files = []
for folder in ("assets", "tonepage", "tests", "docs", "examples", "scripts", ".github"):
    base = root / folder
    if base.exists():
        files.extend(p for p in base.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix not in (".pyc", ".pem", ".key"))
files.extend(root / name for name in ("README.md", "REQUIREMENTS.md", "pyproject.toml", "MANIFEST.in", "setup_windows.cmd", "launch_windows.cmd", "setup.sh", "launch.sh", ".gitignore"))
with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as z:
    for path in sorted(files):
        z.write(path, Path("Tone-Sentry-private-source") / path.relative_to(root))
manifest = {"file": archive.name, "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(), "files": len(files), "bytes": archive.stat().st_size}
(destination / "private-source-manifest-0.8.0.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps(manifest, indent=2))
