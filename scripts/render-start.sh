#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

export DJANGO_SETTINGS_MODULE=config.render_settings
test -s frontend/dist/index.html
python backend/manage.py migrate --noinput
python backend/manage.py seed_demo --render
exec python -m gunicorn --chdir backend config.wsgi:application \
  --bind "0.0.0.0:${PORT:-10000}" --workers 1 --threads 4 --access-logfile -
