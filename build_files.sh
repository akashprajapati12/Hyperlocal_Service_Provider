#!/bin/bash
set -e
echo "BUILD START"
python3 -m pip install --upgrade pip --break-system-packages
python3 -m pip install -r requirements.txt --break-system-packages --only-binary :all:
# If production-only requirements exist, install them (Vercel will have requirements-prod.txt)
if [ -f requirements-prod.txt ]; then
	python3 -m pip install -r requirements-prod.txt --break-system-packages --only-binary :all:
fi
echo "Running migrations"
python3 manage.py migrate --noinput || true
echo "Collecting static files"
python3 manage.py collectstatic --noinput --clear
echo "BUILD END"
