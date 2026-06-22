#!/bin/bash
set -e

echo "Starting deployment..."

# Run migrations with retry (DB may take a moment to be ready)
MAX_RETRIES=30
RETRY_INTERVAL=2
RETRIES=0

echo "Running database migrations..."
while [ $RETRIES -lt $MAX_RETRIES ]; do
    if python manage.py migrate --noinput 2>/dev/null; then
        echo "Migrations completed successfully."
        break
    fi
    RETRIES=$((RETRIES + 1))
    echo "Database not ready (attempt $RETRIES/$MAX_RETRIES). Retrying in ${RETRIES}x${RETRY_INTERVAL}s..."
    sleep $((RETRY_INTERVAL * RETRIES))
done

if [ $RETRIES -eq $MAX_RETRIES ]; then
    echo "ERROR: Could not connect to database after $MAX_RETRIES attempts."
    exit 1
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start gunicorn
echo "Starting gunicorn..."
exec gunicorn config.wsgi:application -c gunicorn.conf.py
