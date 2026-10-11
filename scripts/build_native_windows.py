"""Compile Tone Sentry without bundling its application Python source/bytecode."""
import os
import argparse
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from tonepage import __version__
parser = argparse.ArgumentParser()
parser.add_argument('--onefile', action='store_true', help='Build a single executable for portable testing')
args = parser.parse_args()
build_name = 'native-'+__version__+('-portable' if args.onefile else '')
if os.name != 'nt': raise SystemExit('Build this Windows artifact on Windows')
os.environ.setdefault('NUITKA_CACHE_DIR', str(Path.home()/'ToneSentryBuildCache'))
subprocess.run([
    sys.executable, '-m', 'nuitka', '--mode='+('onefile' if args.onefile else 'standalone'), '--mingw64', '--assume-yes-for-downloads',
    '--enable-plugin=tk-inter', '--windows-console-mode=disable', '--jobs=4',
    '--include-package=tonepage', '--include-package-data=tonepage', '--include-package-data=tzdata',
    '--include-package=imageio_ffmpeg', '--include-package-data=imageio_ffmpeg',
    '--include-package=_sounddevice_data',
    '--output-filename=Tone-Sentry.exe', '--output-dir='+str(root/'build'/build_name),
    '--report='+str(root/'build'/(build_name+'-report.xml')),
    '--windows-icon-from-ico='+str(root/'tonepage/resources/app-icon.ico'),
    '--product-name=Tone Sentry', '--file-description=Paging Monitor and Tone Discovery',
    '--file-version='+__version__, '--product-version='+__version__,
    str(root/'scripts/windows_entry.py'),
], cwd=root, check=True)
