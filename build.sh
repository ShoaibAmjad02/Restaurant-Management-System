#!/bin/bash
set -e

echo "Building Django application for Render..."

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

echo "Build complete!"
