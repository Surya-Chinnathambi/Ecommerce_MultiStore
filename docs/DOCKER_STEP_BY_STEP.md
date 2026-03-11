# Docker Run Guide (Step by Step)

This guide explains how to run the full ecommerce platform using Docker Compose.

## 1. Prerequisites

1. Install Docker Desktop (Windows/macOS) or Docker Engine + Compose (Linux).
2. Make sure Docker is running.
3. Verify versions:

```powershell
docker --version
docker compose version
```

## 2. Open the Project

1. Open a terminal in the project root:

```powershell
cd C:\ecommerce-platform
```

2. Confirm you are in the folder that contains `docker-compose.yml`.

## 3. Build and Start All Services

Run:

```powershell
docker compose up -d --build
```

This builds and starts all configured services (backend, frontend, nginx, db, redis, workers).

## 4. Check Service Health

Run:

```powershell
docker compose ps
```

Wait until key services are up and healthy:

- `ecommerce_storefront` -> `healthy`
- `ecommerce_backend` -> `Up`
- `ecommerce_nginx` -> `Up`
- `ecommerce_db` -> `healthy`
- `ecommerce_redis` -> `healthy`

## 5. Access the App

Open in browser:

- Storefront/Admin (through nginx): `http://localhost`

API is routed through nginx path prefix:

- `http://localhost/api/v1/...`

## 6. Useful Runtime Commands

### View logs

```powershell
docker compose logs --tail=100 backend
docker compose logs --tail=100 storefront
docker compose logs --tail=100 nginx
```

### Follow logs live

```powershell
docker compose logs -f backend
```

### Restart specific services

```powershell
docker compose restart nginx
docker compose restart backend
docker compose restart storefront
```

### Rebuild only frontend and proxy

```powershell
docker compose up -d --build storefront nginx
```

### Rebuild only backend

```powershell
docker compose up -d --build backend
```

## 7. Apply DB Migrations (If Needed Manually)

In most setups, migrations run from backend entrypoint automatically. If you need manual migration:

```powershell
docker compose exec backend alembic upgrade head
```

## 8. Stop Services

```powershell
docker compose down
```

To also remove volumes (warning: this deletes DB data):

```powershell
docker compose down -v
```

## 9. Common Troubleshooting

### A) "Service Unavailable" or 502 from nginx

If backend/storefront containers were rebuilt, nginx can hold stale upstream connections. Run:

```powershell
docker compose restart nginx
```

Then re-check:

```powershell
docker compose ps
```

### B) Frontend changes are not visible

1. Rebuild frontend:

```powershell
docker compose up -d --build storefront nginx
```

2. Hard refresh browser (`Ctrl + F5`).

### C) Backend errors after schema changes

1. Confirm migration files exist.
2. Run migrations:

```powershell
docker compose exec backend alembic upgrade head
```

### D) Check current container states quickly

```powershell
docker compose ps storefront backend nginx db redis
```

## 10. Quick Start (Copy/Paste)

```powershell
cd C:\ecommerce-platform
docker compose up -d --build
docker compose ps
```

Then open `http://localhost`.
