#!/usr/bin/env bash
set -euo pipefail
echo "BUILD START"

# Find a usable python command (python3, python, or py)
PY_CMD=""
if command -v python3 >/dev/null 2>&1; then
	PY_CMD=python3
elif command -v python >/dev/null 2>&1; then
	PY_CMD=python
elif command -v py >/dev/null 2>&1; then
	PY_CMD="py -3"
else
	echo "No python interpreter found (python3, python or py)." >&2
	exit 1
fi

# Upgrade pip (avoid platform-specific flags for portability)
echo "Using $PY_CMD to upgrade pip"
eval "$PY_CMD -m pip install --upgrade pip"

# Install requirements. On some platforms binary-only installs fail; allow source builds.
echo "Installing requirements.txt"
eval "$PY_CMD -m pip install -r requirements.txt"

# If production-only requirements exist, install them
if [ -f requirements-prod.txt ]; then
	echo "Installing requirements-prod.txt"
	eval "$PY_CMD -m pip install -r requirements-prod.txt"
fi

echo "Running migrations"
eval "$PY_CMD manage.py migrate --noinput" || true

echo "Collecting static files"
eval "$PY_CMD manage.py collectstatic --noinput --clear"

echo "BUILD END"
