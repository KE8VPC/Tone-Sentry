#!/bin/sh
set -eu
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/python -m tonepage init
printf '%s\n' 'Install FFmpeg, PortAudio, and Tk using your OS package manager, then run sh launch.sh.'

