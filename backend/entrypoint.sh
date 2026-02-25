#!/bin/bash
set -e

echo "========================================="
echo "  E-Commerce Platform Startup"
echo "========================================="

# Wait for Postgres to be ready (max 60s)
echo "Waiting for database..."
DB_RETRIES=30
until python -c "
import psycopg2, os, sys
try:
    psycopg2.connect(os.environ['DATABASE_URL'])
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
  DB_RETRIES=$((DB_RETRIES - 1))
  if [ $DB_RETRIES -le 0 ]; then
    echo "ERROR: Database not available after 60s. Exiting."
    exit 1
  fi
  echo "  Database not ready yet - retrying in 2s... ($DB_RETRIES attempts left)"
  sleep 2
done
echo "  Database is ready."

# Wait for Redis (max 30s)
echo "Waiting for Redis..."
REDIS_RETRIES=15
until python -c "
import redis, os, sys
try:
    r = redis.from_url(os.environ.get('REDIS_URL', 'redis://redis:6379/0'))
    r.ping()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
  REDIS_RETRIES=$((REDIS_RETRIES - 1))
  if [ $REDIS_RETRIES -le 0 ]; then
    echo "ERROR: Redis not available after 30s. Exiting."
    exit 1
  fi
  echo "  Redis not ready yet - retrying in 2s... ($REDIS_RETRIES attempts left)"
  sleep 2
done
echo "  Redis is ready."

# Run Alembic migrations
echo "Running database migrations..."
alembic upgrade head
echo "  Migrations complete."

echo "========================================="
echo "  Starting application server..."
echo "========================================="

exec "$@"
