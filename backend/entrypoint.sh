#!/bin/bash
set -e

echo "========================================="
echo "  E-Commerce Platform Startup"
echo "========================================="

# Wait for Postgres to be ready (belt-and-suspenders over healthcheck)
echo "Waiting for database..."
until python -c "
import psycopg2, os, sys
try:
    psycopg2.connect(os.environ['DATABASE_URL'])
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
  echo "  Database not ready yet - retrying in 2s..."
  sleep 2
done
echo "  Database is ready."

# Wait for Redis
echo "Waiting for Redis..."
until python -c "
import redis, os, sys
try:
    r = redis.from_url(os.environ.get('REDIS_URL', 'redis://redis:6379/0'))
    r.ping()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
  echo "  Redis not ready yet - retrying in 2s..."
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
