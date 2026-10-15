"""Build an allowlisted private Raspberry Pi ARM64 source test package."""
import hashlib
import json
import re
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
project = (root / 'pyproject.toml').read_text(encoding='utf-8')
version = re.search(r'^version = "([^"]+)"', project, re.M)[1]
dependencies = json.loads(re.search(r'^dependencies = (\[.*\])', project, re.M)[1])
name = f'Tone-Sentry-{version}-Pi4-ARM64-Test'
out = root / 'dist' / (name + '.zip')
out.parent.mkdir(exist_ok=True)
files = {}
for path in (root / 'tonepage').rglob('*'):
    if path.is_file() and '__pycache__' not in path.parts and path.suffix in {'.py', '.json', '.pdf', '.md', '.png', '.ico', '.html', '.css', '.js'}:
        files['app/' + path.relative_to(root).as_posix()] = path.read_bytes()
files['app/pyproject.toml'] = project.encode()
for filename in ('WEB-CONSOLE.md', 'GOOGLE-CHAT.md', f'RELEASE-{version}.md'):
    files['docs/' + filename] = (root / 'docs' / filename).read_bytes()
for path in (root / 'scripts/pi').iterdir():
    if path.is_file() and path.suffix in {'.sh', '.py', '.md'}:
        files[path.name] = path.read_bytes().replace(b'\r\n', b'\n')
files['requirements-pi.txt'] = ('\n'.join(dependencies) + '\n').encode()
files['PACKAGE-INFO.json'] = json.dumps({
    'version': version, 'target': 'Raspberry Pi 4, Raspberry Pi OS Desktop Linux ARM64',
    'distribution': 'Private Python source test package', 'hardware_tested': False,
    'files_sha256': {k: hashlib.sha256(v).hexdigest() for k, v in sorted(files.items())},
}, indent=2).encode()
with zipfile.ZipFile(out, 'x', zipfile.ZIP_DEFLATED) as archive:
    for relative, data in sorted(files.items()):
        info = zipfile.ZipInfo(name + '/' + relative)
        info.create_system = 3
        info.external_attr = (0o100755 if relative.endswith('.sh') else 0o100644) << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, data)
with zipfile.ZipFile(out) as archive:
    assert archive.testzip() is None
    for relative, data in files.items():
        assert archive.read(name + '/' + relative) == data
digest = hashlib.sha256(out.read_bytes()).hexdigest()
out.with_suffix('.zip.sha256').write_text(digest + '  ' + out.name + '\n', encoding='ascii')
print(json.dumps({'file': str(out), 'files': len(files), 'bytes': out.stat().st_size, 'sha256': digest}, indent=2))
