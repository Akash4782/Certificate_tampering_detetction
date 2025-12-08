#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit

echo "Installing wkhtmltopdf..."
apt-get update
apt-get install -y wkhtmltopdf

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Initializing database..."
python init_db.py

echo "Build complete!"
