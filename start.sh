#!/bin/bash
set -e

echo "Starting Django application on Railway..."

# Verify required database env vars are set
echo "Checking environment variables..."
for var in MYSQLHOST MYSQLPORT MYSQLDATABASE MYSQLUSER MYSQLPASSWORD; do
    if [ -z "${!var}" ]; then
        echo "ERROR: Environment variable $var is not set."
        exit 1
    fi
done
echo "All database environment variables are set."

# Wait for database to be reachable
echo "Waiting for database at $MYSQLHOST:$MYSQLPORT..."
MAX_RETRIES=60
COUNT=0

while true; do
    if python -c "
import os, socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
try:
    s.connect((os.environ['MYSQLHOST'], int(os.environ.get('MYSQLPORT', '3306'))))
    s.close()
    exit(0)
except:
    exit(1)
" > /dev/null 2>&1; then
        echo "Database port is reachable!"
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

# Verify Django can connect to the database
echo "Verifying Django database connection..."
MAX_DJANGO_RETRIES=30
DJANGO_COUNT=0

while true; do
    if python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()
from django.db import connection
connection.ensure_connection()
" > /dev/null 2>&1; then
        echo "Django database connection successful!"
        break
    fi

    DJANGO_COUNT=$((DJANGO_COUNT + 1))

    if [ $DJANGO_COUNT -ge $MAX_DJANGO_RETRIES ]; then
        echo "Django database connection failed after $MAX_DJANGO_RETRIES attempts"
        exit 1
    fi

    echo "Django DB check not ready ($DJANGO_COUNT/$MAX_DJANGO_RETRIES). Waiting 5 seconds..."
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
