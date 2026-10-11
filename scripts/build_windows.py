"""Private PyInstaller fallback; does not provide native source protection."""
import os
from pathlib import Path
import PyInstaller.__main__

root=Path(__file__).resolve().parents[1]
if os.name!='nt':
    raise SystemExit('Run this build on Windows using a matching Python architecture')
PyInstaller.__main__.run([
    str(root/'scripts/windows_entry.py'), '--name','Tone-Sentry',
    '--onefile','--windowed','--noconfirm','--noupx',
    '--icon',str(root/'tonepage/resources/app-icon.ico'),
    '--paths',str(root),
    '--distpath',str(root/'dist/windows-0.8.0-pyinstaller-development'),
    '--workpath',str(root/'build/windows'),
    '--specpath',str(root/'build'),
    '--collect-data','tonepage','--collect-all','imageio_ffmpeg',
    '--collect-all','_sounddevice_data','--collect-data','tzdata',
])
