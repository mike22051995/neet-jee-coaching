FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for asyncpg, Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create uploads directory (mounted as volume in production)
RUN mkdir -p /app/uploads

EXPOSE 8000
