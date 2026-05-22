#!/bin/bash
set -e
echo "BUILD START"
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
# If production-only requirements exist, install them (Vercel will have requirements-prod.txt)
if [ -f requirements-prod.txt ]; then
	python3 -m pip install -r requirements-prod.txt
fi
echo "Running migrations"
python3 manage.py migrate --noinput || true
echo "Collecting static files"
python3 manage.py collectstatic --noinput --clear
echo "BUILD END"
