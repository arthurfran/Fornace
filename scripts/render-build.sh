#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

python -m pip install -r backend/requirements-render.txt
npm --prefix frontend ci --include=dev
npm --prefix frontend run build
DJANGO_SETTINGS_MODULE=config.render_settings python backend/manage.py collectstatic --noinput
