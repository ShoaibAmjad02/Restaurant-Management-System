#!/bin/bash
set -e

echo "Starting Django application on Railway..."

echo "Waiting for database..."
MAX_RETRIES=60
COUNT=0

while true; do
    if python manage.py check --database default > /dev/null 2>&1; then
        echo "Database is ready!"
        break
    fi

    COUNT=$((COUNT + 1))

    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "Database connection failed after $MAX_RETRIES attempts"
        exit 1
    fi

    echo "Database not ready ($COUNT/$MAX_RETRIES). Waiting 5 seconds..."
    sleep 5
done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 3 \
    --timeout 120
