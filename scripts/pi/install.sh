#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ $(uname -s) != Linux || $(uname -m) != aarch64 ]]; then
    echo 'Requires 64-bit Linux ARM64 (aarch64). Install Raspberry Pi OS 64-bit Desktop.' >&2
    exit 1
fi
if [[ $EUID == 0 ]]; then
    echo 'Run as your desktop user: bash install.sh (do not use sudo for this script).' >&2
    exit 1
fi
python3 verify-package.py
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-tk libportaudio2 ffmpeg
python3 -c 'import sys; assert sys.version_info >= (3,10), "Python 3.10 or newer is required"'
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
# Require prebuilt dependency wheels, avoiding lengthy native builds on the Pi.
.venv/bin/python -m pip install --only-binary=:all: -r requirements-pi.txt
.venv/bin/python -m pip install --no-deps ./app
.venv/bin/python -m pip check
chmod +x launch.sh check.sh
.venv/bin/python make-shortcut.py
printf '\nInstallation complete. Run: bash check.sh\nThen: bash launch.sh\n'
