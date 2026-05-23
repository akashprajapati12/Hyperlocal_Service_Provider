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

# Helper: install requirements and retry with --break-system-packages on failure
install_requirements() {
	REQ_FILE="$1"
	if [ ! -f "$REQ_FILE" ]; then
		return 0
	fi
	echo "Installing $REQ_FILE"
	set +e
	eval "$PY_CMD -m pip install -r \"$REQ_FILE\""
	RC=$?
	set -e
	if [ $RC -ne 0 ]; then
		echo "pip install failed for $REQ_FILE; retrying with --break-system-packages"
		eval "$PY_CMD -m pip install --break-system-packages -r \"$REQ_FILE\""
	fi
}

# Install requirements (with fallback to break-system-packages)
install_requirements requirements.txt

# If production-only requirements exist, install them
if [ -f requirements-prod.txt ]; then
	install_requirements requirements-prod.txt
fi

echo "Running migrations"
eval "$PY_CMD manage.py migrate --noinput" || true

echo "Collecting static files"
eval "$PY_CMD manage.py collectstatic --noinput --clear"

echo "BUILD END"
