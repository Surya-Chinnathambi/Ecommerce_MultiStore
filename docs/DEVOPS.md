# DevOps & Scalability Guide

## Overview

This guide covers deployment, scaling, monitoring, and disaster recovery strategies for the Multi-Tenant E-Commerce Platform.

---

## 1. Infrastructure Architecture

```
                                    ┌─────────────────────────────────────────┐
                                    │              CDN (CloudFront)            │
                                    └─────────────────────────────────────────┘
                                                        │
                                    ┌─────────────────────────────────────────┐
                                    │          Application Load Balancer       │
                                    │          (SSL Termination)               │
                                    └─────────────────────────────────────────┘
                                                        │
                    ┌───────────────────────────────────┼───────────────────────────────────┐
                    │                                   │                                   │
              ┌─────▼─────┐                       ┌─────▼─────┐                       ┌─────▼─────┐
              │  Frontend │                       │  API Pod  │                       │  API Pod  │
              │   Pods    │                       │    (1)    │                       │    (n)    │
              │   (NGINX) │                       └─────┬─────┘                       └─────┬─────┘
              └───────────┘                             │                                   │
                                                        └─────────────┬─────────────────────┘
                                                                      │
              ┌─────────────────────────────────────────┬─────────────┴─────────────┬───────────────────┐
              │                                         │                           │                   │
        ┌─────▼─────┐                           ┌───────▼───────┐           ┌───────▼───────┐   ┌───────▼───────┐
        │PostgreSQL │                           │  Redis Cluster │           │   RabbitMQ    │   │    Celery     │
        │  Primary  │◄──────Replication────────►│ (Cache+Queue)  │           │   Cluster     │   │   Workers     │
        └─────┬─────┘                           └───────────────┘           └───────────────┘   └───────────────┘
              │
        ┌─────▼─────┐
        │PostgreSQL │
        │  Replica  │ (Read-only queries)
        └───────────┘
```

---

## 2. Database Scaling Strategy

### 2.1 Connection Pooling

```python
# SQLAlchemy connection pool configuration
SQLALCHEMY_POOL_SIZE = 20        # Base connections per worker
SQLALCHEMY_MAX_OVERFLOW = 40    # Additional connections under load
SQLALCHEMY_POOL_TIMEOUT = 30    # Wait time for connection
SQLALCHEMY_POOL_RECYCLE = 3600  # Recycle connections hourly

# For production with multiple workers:
# Total connections = (pool_size + max_overflow) × num_workers
# Example: (20 + 40) × 8 workers = 480 max connections
```

### 2.2 Read Replica Configuration

```python
# database.py - Multi-database routing
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

class DatabaseRouter:
    def __init__(self):
        self.primary = create_engine(
            settings.DATABASE_URL,
            pool_size=20,
            max_overflow=40
        )
        self.replica = create_engine(
            settings.DATABASE_REPLICA_URL,
            pool_size=30,
            max_overflow=60
        )
    
    def get_session(self, read_only: bool = False) -> Session:
        engine = self.replica if read_only else self.primary
        return Session(engine)

# Usage
@router.get("/products")
async def list_products(db: Session = Depends(get_read_db)):
    # Uses replica for read operations
    return db.query(Product).all()

@router.post("/products")
async def create_product(db: Session = Depends(get_write_db)):
    # Uses primary for write operations
    pass
```

### 2.3 Table Partitioning

```sql
-- Partition orders by created_at (monthly)
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    store_id UUID NOT NULL,
    created_at TIMESTAMP NOT NULL,
    ...
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE orders_2024_01 PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE orders_2024_02 PARTITION OF orders
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Automated partition creation (run monthly via cron)
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS void AS $$
DECLARE
    start_date DATE := DATE_TRUNC('month', NOW() + INTERVAL '1 month');
    end_date DATE := start_date + INTERVAL '1 month';
    partition_name TEXT := 'orders_' || TO_CHAR(start_date, 'YYYY_MM');
BEGIN
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF orders FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );
END;
$$ LANGUAGE plpgsql;
```

### 2.4 Query Optimization

```sql
-- Essential indexes for multi-tenant queries
CREATE INDEX idx_products_store_id ON products(store_id);
CREATE INDEX idx_products_store_category ON products(store_id, category_id);
CREATE INDEX idx_orders_store_user ON orders(store_id, user_id);
CREATE INDEX idx_orders_store_created ON orders(store_id, created_at DESC);

-- Partial indexes for common filters
CREATE INDEX idx_products_active ON products(store_id, name) 
    WHERE is_active = true;

CREATE INDEX idx_orders_pending ON orders(store_id, created_at) 
    WHERE status = 'pending';

-- Full-text search index
CREATE INDEX idx_products_search ON products 
    USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));
```

---

## 3. Caching Strategy

### 3.1 Multi-Level Cache Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   L1: In-Memory │  →   │   L2: Redis     │  →   │   L3: Database  │
│   (per-process) │      │   (distributed) │      │                 │
│   TTL: 60s      │      │   TTL: 5min     │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

### 3.2 Cache Key Strategy

```python
# Cache key patterns
CACHE_KEYS = {
    # Store-specific data
    "store_config": "store:{store_id}:config",
    "store_products": "store:{store_id}:products:page:{page}",
    "store_categories": "store:{store_id}:categories",
    
    # User-specific data
    "user_cart": "user:{user_id}:cart",
    "user_session": "session:{session_id}",
    
    # Global data
    "product_detail": "product:{product_id}:detail",
    "category_tree": "global:category_tree",
}

# Cache invalidation patterns
async def invalidate_store_cache(store_id: str):
    pattern = f"store:{store_id}:*"
    keys = await redis.keys(pattern)
    if keys:
        await redis.delete(*keys)
```

### 3.3 Cache-Aside Implementation

```python
class CacheService:
    def __init__(self, redis_client, default_ttl=300):
        self.redis = redis_client
        self.default_ttl = default_ttl
    
    async def get_or_set(
        self, 
        key: str, 
        fetch_func: Callable,
        ttl: Optional[int] = None
    ):
        # Try cache first
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        
        # Cache miss - fetch from source
        data = await fetch_func()
        
        # Store in cache
        await self.redis.setex(
            key, 
            ttl or self.default_ttl, 
            json.dumps(data)
        )
        
        return data

# Usage
products = await cache.get_or_set(
    f"store:{store_id}:products",
    lambda: db.query(Product).filter_by(store_id=store_id).all(),
    ttl=600
)
```

---

## 4. Horizontal Scaling

### 4.1 API Pod Scaling

```yaml
# HorizontalPodAutoscaler configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Pods
        value: 4
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

### 4.2 Worker Scaling with KEDA

```yaml
# KEDA ScaledObject for Celery workers
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: celery-worker-scaledobject
spec:
  scaleTargetRef:
    name: celery-worker
  minReplicaCount: 2
  maxReplicaCount: 10
  triggers:
  - type: rabbitmq
    metadata:
      host: amqp://rabbitmq:5672
      queueName: celery
      mode: QueueLength
      value: "50"  # Scale when queue > 50 messages
```

---

## 5. Backup & Recovery

### 5.1 Backup Strategy

| Data Type | Frequency | Retention | Method |
|-----------|-----------|-----------|--------|
| PostgreSQL (full) | Daily | 30 days | pg_dump + S3 |
| PostgreSQL (WAL) | Continuous | 7 days | WAL archiving |
| Redis | Hourly | 24 hours | RDB snapshots |
| File uploads | Continuous | Permanent | S3 replication |

### 5.2 PostgreSQL Backup Script

```bash
#!/bin/bash
# backup-postgres.sh

set -e

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"
S3_BUCKET="s3://ecommerce-backups/postgres"
DATABASE="ecommerce"

# Create compressed backup
pg_dump -h $DB_HOST -U $DB_USER -Fc $DATABASE > \
    $BACKUP_DIR/backup_$DATE.dump

# Upload to S3
aws s3 cp $BACKUP_DIR/backup_$DATE.dump \
    $S3_BUCKET/backup_$DATE.dump \
    --storage-class STANDARD_IA

# Cleanup old local backups (keep 7 days)
find $BACKUP_DIR -name "*.dump" -mtime +7 -delete

echo "Backup completed: backup_$DATE.dump"
```

### 5.3 Disaster Recovery Plan

```
Recovery Point Objective (RPO): 1 hour
Recovery Time Objective (RTO): 4 hours

DISASTER RECOVERY PROCEDURE:

1. DETECTION (0-15 min)
   - Automated monitoring alerts
   - Verify incident is not false positive
   - Initiate incident response

2. ASSESSMENT (15-30 min)
   - Identify affected components
   - Determine data loss extent
   - Decide recovery strategy

3. RECOVERY (30 min - 3 hours)
   a. Database Recovery:
      - Restore latest backup from S3
      - Apply WAL logs for point-in-time recovery
      - Verify data integrity
   
   b. Application Recovery:
      - Deploy to DR region (if regional failure)
      - Update DNS to failover endpoint
      - Scale up resources
   
   c. Cache Recovery:
      - Redis will warm up from database
      - Pre-warm critical cache keys

4. VERIFICATION (3-4 hours)
   - Run integration tests
   - Verify all services operational
   - Monitor for issues

5. POST-INCIDENT
   - Document timeline and actions
   - Root cause analysis
   - Update runbooks if needed
```

---

## 6. Monitoring Setup

### 6.1 Key Metrics to Track

```yaml
# Business Metrics
- orders_per_minute
- revenue_per_hour
- cart_abandonment_rate
- payment_success_rate
- sync_success_rate

# Application Metrics
- api_request_rate
- api_error_rate (5xx)
- api_latency_p95
- active_websocket_connections
- celery_queue_depth

# Infrastructure Metrics
- cpu_utilization
- memory_utilization
- disk_iops
- network_throughput
- container_restarts

# Database Metrics
- connection_pool_usage
- query_latency_p95
- replication_lag
- deadlocks_per_minute
- cache_hit_ratio
```

### 6.2 Alerting Rules

```yaml
# Critical (page on-call)
- api_up == 0
- error_rate > 5%
- database_down
- payment_failure_rate > 10%

# Warning (notify team)
- error_rate > 1%
- latency_p95 > 2s
- disk_usage > 80%
- queue_depth > 1000
- memory_usage > 85%

# Info (log only)
- pod_restarts > 3/hour
- cache_miss_rate > 20%
- slow_queries > 10/min
```

---

## 7. Deployment Pipeline

### 7.1 Release Strategy

```
Blue-Green Deployment:

┌─────────────────┐     ┌─────────────────┐
│   Blue (v1.0)   │     │  Green (v1.1)   │
│   (Active)      │     │   (Standby)     │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │    ←── Switch ──►     │
         │                       │
┌────────▼────────────────────────────────┐
│            Load Balancer                 │
└──────────────────────────────────────────┘

Steps:
1. Deploy new version to Green
2. Run smoke tests on Green
3. Gradually shift traffic (10% → 50% → 100%)
4. Monitor for errors
5. If issues, rollback to Blue immediately
6. Blue becomes new standby
```

### 7.2 Rollback Procedure

```bash
#!/bin/bash
# rollback.sh

set -e

PREVIOUS_IMAGE=$1
DEPLOYMENT=$2

if [ -z "$PREVIOUS_IMAGE" ] || [ -z "$DEPLOYMENT" ]; then
    echo "Usage: rollback.sh <previous-image> <deployment>"
    exit 1
fi

echo "Rolling back $DEPLOYMENT to $PREVIOUS_IMAGE..."

# Update deployment image
kubectl set image deployment/$DEPLOYMENT \
    $DEPLOYMENT=$PREVIOUS_IMAGE \
    -n ecommerce

# Wait for rollout
kubectl rollout status deployment/$DEPLOYMENT -n ecommerce

# Verify pods are healthy
kubectl get pods -n ecommerce -l app=$DEPLOYMENT

echo "Rollback complete!"
```

---

## 8. Performance Benchmarks

### Target Performance (per API pod)

| Metric | Target | Critical |
|--------|--------|----------|
| Requests/second | 1000+ | < 500 |
| P50 latency | < 100ms | > 500ms |
| P95 latency | < 500ms | > 2s |
| P99 latency | < 1s | > 5s |
| Error rate | < 0.1% | > 1% |
| Memory usage | < 1GB | > 2GB |
| CPU usage | < 70% | > 90% |

### Load Testing Script

```python
# locustfile.py
from locust import HttpUser, task, between

class EcommerceUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(10)
    def browse_products(self):
        self.client.get("/api/v1/products")
    
    @task(5)
    def view_product(self):
        self.client.get("/api/v1/products/1")
    
    @task(3)
    def add_to_cart(self):
        self.client.post("/api/v1/cart/items", json={
            "product_id": 1,
            "quantity": 1
        })
    
    @task(1)
    def checkout(self):
        self.client.post("/api/v1/orders")

# Run: locust -f locustfile.py --host=https://api.example.com
```
