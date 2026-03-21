#!/bin/sh
set -e

uv run python manage.py migrate --noinput

exec uv run gunicorn personal_bot.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 2 \
    --timeout 60 \
    --keep-alive 5
