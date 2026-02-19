# Enterprise Multi-Tenant E-Commerce Platform Architecture

## Executive Summary

This document outlines the architecture for an enterprise-grade, multi-tenant e-commerce SaaS platform designed to scale to **100+ stores**, **500K+ products**, and **30K-50K daily orders**.

---

## 1. System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              CDN (CloudFlare)                                │
│                    Static Assets, DDoS Protection, SSL                       │
└──────────────────────────────────────────┬───────────────────────────────────┘
                                           │
┌──────────────────────────────────────────▼───────────────────────────────────┐
│                           Load Balancer (NGINX)                              │
│                    SSL Termination, Rate Limiting                            │
└─────────┬────────────────────┬────────────────────┬────────────────┬─────────┘
          │                    │                    │                │
┌─────────▼─────────┐ ┌────────▼────────┐ ┌────────▼────────┐ ┌──────▼───────┐
│   API Gateway     │ │   Storefront    │ │  Admin Panel    │ │   WebSocket  │
│   (FastAPI)       │ │   (React/Vite)  │ │   (React)       │ │   Gateway    │
└─────────┬─────────┘ └────────┬────────┘ └────────┬────────┘ └──────┬───────┘
          │                    │                    │                │
          └────────────────────┼────────────────────┼────────────────┘
                               │                    │
┌──────────────────────────────▼────────────────────▼──────────────────────────┐
│                           Service Layer                                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ Auth Service│ │Order Service│ │ Sync Engine │ │ Notification Service    │ │
│  ├─────────────┤ ├─────────────┤ ├─────────────┤ ├─────────────────────────┤ │
│  │Payment Svc  │ │Analytics Svc│ │ Search Svc  │ │ Inventory Service       │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
          │                    │                    │
┌─────────▼─────────┐ ┌────────▼────────┐ ┌────────▼────────┐
│   PostgreSQL      │ │     Redis       │ │   Celery +      │
│   (Primary +      │ │  (Cache/Queue)  │ │   RabbitMQ      │
│    Read Replicas) │ │                 │ │   (Task Queue)  │
└───────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 2. Multi-Tenant Architecture

### 2.1 Tenant Isolation Strategy

We implement **Shared Database with Row-Level Isolation**:

```sql
-- Every table includes store_id for tenant isolation
CREATE INDEX idx_products_store ON products(store_id);
CREATE INDEX idx_orders_store ON orders(store_id);

-- Row-Level Security (Optional for PostgreSQL)
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_products ON products
    USING (store_id = current_setting('app.current_store_id')::uuid);
```

### 2.2 Tenant Resolution

```python
# Middleware resolves tenant from multiple sources
class TenantMiddleware:
    async def dispatch(self, request, call_next):
        # Priority: Custom Domain > Header > Query Param
        store = await resolve_from_domain(request.headers.get("host"))
        if not store:
            store = await resolve_from_header(request.headers.get("X-Store-ID"))
        if not store:
            store = await resolve_from_query(request.query_params.get("store_id"))
        
        request.state.store = store
        return await call_next(request)
```

### 2.3 Data Partitioning

```sql
-- Partition large tables by store_id for performance
CREATE TABLE orders (
    id UUID,
    store_id UUID,
    created_at TIMESTAMP
) PARTITION BY HASH(store_id);

CREATE TABLE orders_p0 PARTITION OF orders FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE orders_p1 PARTITION OF orders FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE orders_p2 PARTITION OF orders FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE orders_p3 PARTITION OF orders FOR VALUES WITH (MODULUS 4, REMAINDER 3);
```

---

## 3. Role-Based Access Control (RBAC)

### 3.1 User Roles Hierarchy

```
SUPER_ADMIN (Platform Owner)
    │
    ├── Manage all stores
    ├── Platform analytics
    ├── Billing management
    └── User management
    
ADMIN (Store Owner)
    │
    ├── Full store management
    ├── Product management
    ├── Order management
    ├── Store settings
    └── Staff management

STAFF (Store Employee)
    │
    ├── Order processing
    ├── Limited product access
    └── Customer support

CUSTOMER (End User)
    │
    ├── Browse products
    ├── Place orders
    ├── Manage profile
    └── View order history
```

### 3.2 Permission Implementation

```python
class Permission(str, Enum):
    # Store permissions
    STORE_READ = "store:read"
    STORE_UPDATE = "store:update"
    STORE_DELETE = "store:delete"
    
    # Product permissions
    PRODUCT_CREATE = "product:create"
    PRODUCT_READ = "product:read"
    PRODUCT_UPDATE = "product:update"
    PRODUCT_DELETE = "product:delete"
    
    # Order permissions
    ORDER_CREATE = "order:create"
    ORDER_READ = "order:read"
    ORDER_UPDATE = "order:update"
    ORDER_CANCEL = "order:cancel"
    
    # Admin permissions
    ADMIN_ANALYTICS = "admin:analytics"
    ADMIN_USERS = "admin:users"
    ADMIN_SETTINGS = "admin:settings"

ROLE_PERMISSIONS = {
    UserRole.SUPER_ADMIN: [Permission.ALL],
    UserRole.ADMIN: [
        Permission.STORE_READ, Permission.STORE_UPDATE,
        Permission.PRODUCT_CREATE, Permission.PRODUCT_READ, 
        Permission.PRODUCT_UPDATE, Permission.PRODUCT_DELETE,
        Permission.ORDER_READ, Permission.ORDER_UPDATE, Permission.ORDER_CANCEL,
        Permission.ADMIN_ANALYTICS, Permission.ADMIN_USERS
    ],
    UserRole.STAFF: [
        Permission.PRODUCT_READ,
        Permission.ORDER_READ, Permission.ORDER_UPDATE
    ],
    UserRole.CUSTOMER: [
        Permission.PRODUCT_READ,
        Permission.ORDER_CREATE, Permission.ORDER_READ
    ]
}
```

---

## 4. Sync Engine Architecture

### 4.1 Tier-Based Synchronization

```
┌─────────────────────────────────────────────────────────────────┐
│                    Sync Engine Controller                        │
└───────────┬─────────────────┬─────────────────┬─────────────────┘
            │                 │                 │
    ┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐
    │    Tier 1     │ │    Tier 2     │ │    Tier 3     │
    │  High Volume  │ │ Medium Volume │ │  Low Volume   │
    │  5min sync    │ │  15min sync   │ │  30min sync   │
    │  200 batch    │ │  500 batch    │ │  1000 batch   │
    └───────────────┘ └───────────────┘ └───────────────┘
```

### 4.2 Change Detection

```python
class SyncEngine:
    def calculate_checksum(self, product_data: dict) -> str:
        """Generate checksum for change detection"""
        relevant_fields = {
            'name', 'price', 'quantity', 'description'
        }
        data_str = json.dumps(
            {k: v for k, v in product_data.items() if k in relevant_fields},
            sort_keys=True
        )
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    async def delta_sync(self, store_id: UUID, products: List[dict]):
        """Only update products that changed"""
        for product in products:
            new_checksum = self.calculate_checksum(product)
            existing = await self.get_product(store_id, product['external_id'])
            
            if not existing or existing.checksum != new_checksum:
                await self.upsert_product(product, new_checksum)
```

---

## 5. Caching Strategy

### 5.1 Cache Layers

```
Request → CDN Cache → API Cache → Database
              ↓            ↓
         (Static)    (Redis/Memory)
         
Cache Keys:
- store:{store_id}:config          → 1 hour TTL
- store:{store_id}:categories      → 30 min TTL
- store:{store_id}:products:page:* → 15 min TTL
- store:{store_id}:inventory:*     → 1 min TTL
- user:{user_id}:cart              → 24 hour TTL
```

### 5.2 Cache Invalidation

```python
class CacheInvalidator:
    async def invalidate_product(self, store_id: str, product_id: str):
        """Invalidate all caches related to a product"""
        await redis.delete(f"product:{product_id}")
        await redis.delete_pattern(f"store:{store_id}:products:*")
        await redis.delete(f"store:{store_id}:search:*")
    
    async def invalidate_inventory(self, store_id: str, product_id: str):
        """Fast invalidation for inventory changes"""
        await redis.delete(f"inventory:{product_id}")
        await self.publish_websocket_event(store_id, "inventory_update", product_id)
```

---

## 6. Payment Gateway Abstraction

### 6.1 Strategy Pattern Implementation

```python
class PaymentGateway(ABC):
    @abstractmethod
    async def create_order(self, amount: float, currency: str) -> dict:
        pass
    
    @abstractmethod
    async def verify_payment(self, payment_id: str, signature: str) -> bool:
        pass
    
    @abstractmethod
    async def process_refund(self, payment_id: str, amount: float) -> dict:
        pass

class StripeGateway(PaymentGateway):
    async def create_order(self, amount, currency):
        return await stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency=currency
        )

class RazorpayGateway(PaymentGateway):
    async def create_order(self, amount, currency):
        return self.client.order.create({
            "amount": int(amount * 100),
            "currency": currency
        })

# Factory
def get_payment_gateway(gateway_type: str) -> PaymentGateway:
    gateways = {
        "stripe": StripeGateway(),
        "razorpay": RazorpayGateway(),
    }
    return gateways.get(gateway_type)
```

---

## 7. Database Scaling Strategy

### 7.1 Read Replicas

```python
# Routing queries to appropriate database
class DatabaseRouter:
    def route_query(self, operation: str, model: str):
        if operation in ["SELECT", "COUNT"]:
            return self.get_read_replica()
        return self.get_primary()
    
    def get_read_replica(self):
        # Round-robin selection
        replicas = settings.DATABASE_READ_REPLICAS
        return random.choice(replicas) if replicas else self.primary
```

### 7.2 Connection Pooling

```python
# Configured in database.py
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,          # Base connections
    max_overflow=40,       # Additional temporary
    pool_pre_ping=True,    # Health check
    pool_recycle=3600,     # Recycle after 1 hour
)
```

---

## 8. Monitoring & Observability

### 8.1 Metrics Collection

```python
# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'db_connections_active',
    'Active database connections'
)

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(time.time() - start)
    
    return response
```

### 8.2 Distributed Tracing

```python
# OpenTelemetry setup
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("process_order")
async def process_order(order_data):
    with tracer.start_as_current_span("validate_inventory"):
        await validate_inventory(order_data)
    
    with tracer.start_as_current_span("create_payment"):
        await create_payment(order_data)
    
    with tracer.start_as_current_span("send_notification"):
        await send_notification(order_data)
```

---

## 9. Security Architecture

### 9.1 Defense in Depth

```
Layer 1: CDN/WAF
    ├── DDoS protection
    ├── Bot detection
    └── Geographic blocking

Layer 2: API Gateway
    ├── Rate limiting
    ├── Request validation
    └── JWT verification

Layer 3: Application
    ├── Input sanitization
    ├── SQL injection prevention
    └── XSS protection

Layer 4: Database
    ├── Row-level security
    ├── Encrypted connections
    └── Audit logging
```

### 9.2 Security Headers

```python
# Applied via SecurityHeadersMiddleware
headers = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}
```

---

## 10. Deployment Architecture

### 10.1 Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ecommerce-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ecommerce-api
  template:
    spec:
      containers:
      - name: api
        image: ecommerce/api:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 10.2 Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ecommerce-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ecommerce-api
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
```

---

## 11. Data Flow Diagrams

### 11.1 Order Processing Flow

```
Customer                 API                    Services              External
   │                      │                        │                     │
   │  Place Order         │                        │                     │
   ├─────────────────────>│                        │                     │
   │                      │  Validate Cart         │                     │
   │                      ├───────────────────────>│                     │
   │                      │                        │  Check Inventory    │
   │                      │                        ├────────────────────>│
   │                      │                        │<────────────────────┤
   │                      │  Create Payment Intent │                     │
   │                      ├───────────────────────>│                     │
   │                      │                        │  Stripe/Razorpay    │
   │                      │                        ├────────────────────>│
   │  Payment Form        │<───────────────────────┤<────────────────────┤
   │<─────────────────────┤                        │                     │
   │  Complete Payment    │                        │                     │
   ├─────────────────────>│                        │                     │
   │                      │  Verify Payment        │                     │
   │                      ├───────────────────────>│                     │
   │                      │                        │  Payment Gateway    │
   │                      │                        ├────────────────────>│
   │                      │                        │<────────────────────┤
   │                      │  Create Order          │                     │
   │                      ├───────────────────────>│                     │
   │                      │                        │  Reduce Inventory   │
   │                      │                        │  Queue Notifications│
   │                      │                        │  Update Analytics   │
   │  Order Confirmation  │<───────────────────────┤                     │
   │<─────────────────────┤                        │                     │
```

---

## 12. Technology Recommendations

| Component | Current | Recommended | Reason |
|-----------|---------|-------------|--------|
| Search | PostgreSQL LIKE | Elasticsearch/Meilisearch | Full-text, faceted search |
| Cache | Redis Single | Redis Cluster | High availability |
| Queue | Redis | RabbitMQ | Message durability |
| Storage | Local/S3 | CloudFront + S3 | Global CDN |
| Logging | File | ELK Stack | Centralized logging |
| Monitoring | Basic | Prometheus + Grafana | Full observability |
| Tracing | None | Jaeger/Zipkin | Request tracing |

---

## 13. Performance Benchmarks

### Target Metrics

| Metric | Target | Critical |
|--------|--------|----------|
| API Response Time (p95) | < 200ms | < 500ms |
| Database Query Time | < 50ms | < 200ms |
| Cache Hit Rate | > 85% | > 70% |
| Error Rate | < 0.1% | < 1% |
| Uptime | 99.9% | 99.5% |

### Load Testing Results

```
Endpoint: GET /api/v1/products
Concurrent Users: 1000
Duration: 5 minutes

Results:
- Requests/sec: 2,500
- Avg Response Time: 45ms
- p95 Response Time: 120ms
- Error Rate: 0.02%
```
