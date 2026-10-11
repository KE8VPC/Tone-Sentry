#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ! -x .venv/bin/python ]]; then
    echo 'Run bash install.sh first.' >&2
    exit 1
fi
# Diagnostics use a fresh isolated folder, never the live receiver data.
task_check=$(mktemp -d "${TMPDIR:-/tmp}/tonesentry-check.XXXXXXXX")
echo "Diagnostic folder: $task_check"
.venv/bin/python -m pip check
.venv/bin/python -m tonepage --home "$task_check" doctor
.venv/bin/python -m tonepage --home "$task_check" demo
echo 'Synthetic check finished. This does not verify live radio input or external deliveries.'
echo 'List audio inputs with: bash launch.sh devices'
