FROM python:3.11-slim

# Install system dependencies including wkhtmltopdf
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint executable
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Environment variables
ENV PYTHONUNBUFFERED=1

# Run entrypoint
CMD ["./entrypoint.sh"]
