"""Stage a private development binary bundle and inspect its contents."""
import hashlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root/'build/native-0.8.17/windows_entry.dist'
target = root/'dist/Tone-Sentry-0.8.17-Windows-x64'
if not (source/'Tone-Sentry.exe').is_file(): raise SystemExit('Compile the native build first')
if target.exists(): raise SystemExit('Release folder exists; choose a new version or inspect it before replacing')
shutil.copytree(source, target)
notices = target/'third-party-notices'
notices.mkdir(exist_ok=True)
deps = ['numpy','sounddevice','requests','urllib3','certifi','charset-normalizer','idna','cffi','pycparser','cryptography','typing_extensions','tzdata','imageio-ffmpeg','Flask','Werkzeug','Jinja2','MarkupSafe','click','blinker','itsdangerous','cheroot','jaraco.functools','more-itertools','psutil']
manifest = {}
for name in deps:
    dist = metadata.distribution(name)
    manifest[name] = dist.version
    for f in dist.files or []:
        if f.name.lower().startswith(('license','copying','notice')) and '.dist-info' in str(f) and dist.locate_file(f).is_file():
            directory = notices/name
            directory.mkdir(exist_ok=True)
            shutil.copy2(dist.locate_file(f), directory/f.name)
python_license = Path(sys.base_prefix)/'LICENSE.txt'
if python_license.exists(): shutil.copy2(python_license, notices/'Python-LICENSE.txt')
for f in (Path(sys.base_prefix)/'tcl').rglob('license.terms'):
    shutil.copy2(f, notices/(f.parent.name+'-license.terms'))
import imageio_ffmpeg
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
for option, name in [('-version','FFmpeg-build.txt'),('-L','FFmpeg-license.txt')]:
    result = subprocess.run([ffmpeg,option],capture_output=True,text=True,check=True)
    (notices/name).write_text(result.stdout+result.stderr,encoding='utf-8')
shutil.copy2(root/'docs/NATIVE-BUILD.md', target/'BUILD-AND-LIMITS.md')
shutil.copy2(root/'docs/WINDOWS-EXE.md', target/'START-HERE.md')
shutil.copy2(root/'docs/RELEASE-0.8.17.md', target/'RELEASE-NOTES.md')
shutil.copy2(root/'tonepage/resources/usage-guide.md', target/'HELP.md')
(target/'docs').mkdir()
shutil.copy2(root/'docs/COORDINATION.md',target/'docs/COORDINATION.md')
shutil.copy2(root/'docs/WEB-CONSOLE.md',target/'docs/WEB-CONSOLE.md')
shutil.copy2(root/'docs/GOOGLE-CHAT.md',target/'docs/GOOGLE-CHAT.md')
(notices/'dependencies.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
files = sorted(p for p in target.rglob('*') if p.is_file())
for p in files:
    relative = p.relative_to(target)
    private_material = p.suffix.lower() == '.pem' and relative.as_posix() != 'certifi/cacert.pem'
    if p.suffix.lower() in ('.py','.pyc','.pyo','.pdb','.key','.sqlite3') or private_material or any(x in relative.parts for x in ('tests','scripts','runtime')):
        raise SystemExit('Unexpected release content: '+str(relative))
    if ':' in relative.as_posix() or any(part.endswith((' ','.')) for part in relative.parts):
        raise SystemExit('Invalid Windows archive path: '+str(relative))
archive = target.parent/(target.name+'.zip')
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
    for p in files: out.write(p,Path(target.name)/p.relative_to(target))
with zipfile.ZipFile(archive) as out:
    assert out.testzip() is None
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n',encoding='ascii')
print(json.dumps(dict(executable=str(target/'Tone-Sentry.exe'),archive=str(archive),files=len(files),bytes=archive.stat().st_size,sha256=digest),indent=2))
