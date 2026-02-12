#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

echo "Running migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Starting Daphne Server..."
daphne -b 0.0.0.0 -p 8000 config.asgi:application