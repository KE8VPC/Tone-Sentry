"""Package the single-file test executable with its notices and guide."""
import hashlib
import json
import shutil
import struct
import sys
import zipfile
from pathlib import Path

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from tonepage import __version__
name=f'Tone-Sentry-{__version__}-Portable-Windows-x64'
source=root/'build'/f'native-{__version__}-portable'/'Tone-Sentry.exe'
notices=root/'dist'/f'Tone-Sentry-{__version__}-Windows-x64'/'third-party-notices'
target=root/'dist'/name
if target.exists():raise SystemExit('Portable release folder already exists; inspect before replacing')
if not source.is_file() or not notices.is_dir():raise SystemExit('Build the onefile executable and stage the matching standalone notices first')
binary=source.read_bytes()
pe_offset=struct.unpack_from('<I',binary,0x3c)[0]
assert binary[:2]==b'MZ' and binary[pe_offset:pe_offset+4]==b'PE\0\0'
assert struct.unpack_from('<H',binary,pe_offset+4)[0]==0x8664
target.mkdir()
exe=target/(name+'.exe')
shutil.copy2(source,exe)
shutil.copytree(notices,target/'third-party-notices')
shutil.copy2(root/'docs/PORTABLE-TESTING.md',target/'START-HERE.md')
shutil.copy2(root/'docs/RELEASE-0.8.18.md',target/'RELEASE-NOTES.md')
shutil.copy2(root/'tonepage/resources/usage-guide.md',target/'HELP.md')
(target/'docs').mkdir()
shutil.copy2(root/'docs/COORDINATION.md',target/'docs/COORDINATION.md')
shutil.copy2(root/'docs/WEB-CONSOLE.md',target/'docs/WEB-CONSOLE.md')
shutil.copy2(root/'docs/GOOGLE-CHAT.md',target/'docs/GOOGLE-CHAT.md')
archive=root/'dist'/(name+'.zip')
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as out:
    for path in sorted(target.rglob('*')):
        if path.is_file():out.write(path,Path(name)/path.relative_to(target))
with zipfile.ZipFile(archive) as out:assert out.testzip() is None
result={}
for path in (exe,archive):
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    path.with_suffix(path.suffix+'.sha256').write_text(digest+'  '+path.name+'\n',encoding='ascii')
    result[path.name]=dict(path=str(path),bytes=path.stat().st_size,sha256=digest)
print(json.dumps(result,indent=2))
