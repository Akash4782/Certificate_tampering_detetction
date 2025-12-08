#!/bin/bash
set -e

echo "Initializing database..."
python init_db.py

echo "Starting application..."
exec gunicorn --bind 0.0.0.0:$PORT app:app
