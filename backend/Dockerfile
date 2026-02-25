FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    libmagic1 \
    libmagic-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security (used in production only)
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Create directories for uploads and logs with open permissions
# (dev: volumes may be mounted as root; prod: runs as appuser)
RUN mkdir -p /app/uploads /app/logs && chmod -R 777 /app/uploads /app/logs

# Copy and configure entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

# NOTE: USER appuser is set via docker-compose in production.
# Dev mode runs as root to allow live-reload volume writes.

# Expose port
EXPOSE 8000

# Entrypoint runs migrations then starts the app
ENTRYPOINT ["/entrypoint.sh"]

# Production: Gunicorn with Uvicorn workers (4 workers for 2-core container)
# Override with `command` in docker-compose for dev mode (uvicorn --reload)
CMD ["gunicorn", "app.main:app", \
    "--worker-class", "uvicorn.workers.UvicornWorker", \
    "--workers", "4", \
    "--bind", "0.0.0.0:8000", \
    "--timeout", "120", \
    "--keepalive", "5", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--log-level", "info"]
