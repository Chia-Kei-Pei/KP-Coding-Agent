#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Activate conda environment.
# conda activate does not work in non-interactive shells by default,
# so we source conda.sh first to make the activate command available.
CONDA_BASE="$(conda info --base 2>/dev/null)"
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate AI-Engg-HTX
echo "==> Activated conda environment: $CONDA_DEFAULT_ENV"

INSTALL_CMD=(pip install -r requirements.txt)
VERIFY_CMD=(true)  # no tests yet — replace with e.g. (python -m pytest) when ready
START_CMD=(python coding_agent.py)

echo "==> Working directory: $PWD"
echo "==> Syncing dependencies"
"${INSTALL_CMD[@]}"

echo "==> Running baseline verification"
"${VERIFY_CMD[@]}"

echo "==> Startup command"
printf '    %q' "${START_CMD[@]}"
printf '\n'

if [ "${RUN_START_COMMAND:-0}" = "1" ]; then
  echo "==> Starting the app"
  exec "${START_CMD[@]}"
fi

echo "Set RUN_START_COMMAND=1 if you want init.sh to launch the app directly."