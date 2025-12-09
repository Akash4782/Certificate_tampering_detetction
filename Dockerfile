# Use Bullseye (Debian 11) because wkhtmltopdf is removed in Bookworm (Debian 12)
FROM python:3.11-slim-bullseye

# Install system dependencies (wkhtmltopdf + fonts + utils)
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    libxrender1 \
    libfontconfig1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirement files
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Railway automatically provides a PORT env var.
CMD gunicorn -w 4 -b 0.0.0.0:$PORT app:app
