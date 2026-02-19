"""
Prometheus Metrics Middleware
Exposes standard RED metrics (Rate, Error, Duration) for every HTTP request.
Prometheus scrapes /metrics; Grafana reads from Prometheus.
"""
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    REGISTRY,
    CollectorRegistry,
)

logger = logging.getLogger(__name__)

# ── Metric Definitions ────────────────────────────────────────────────────────
# Normalise endpoint labels: strip dynamic path segments like /items/123 → /items/{id}
# This keeps cardinality low (prevents a unique label per UUID).

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
)

HTTP_RESPONSE_SIZE_BYTES = Histogram(
    "http_response_size_bytes",
    "HTTP response body size in bytes",
    ["method", "endpoint"],
    buckets=[100, 1_000, 10_000, 100_000, 1_000_000],
)

# App info gauge (static labels) — shows in Grafana dashboards as metadata
APP_INFO = Info("app_info", "Application version and environment information")


# ── Path normalisation ────────────────────────────────────────────────────────
import re

# Patterns that look like dynamic IDs — replace with a placeholder
_ID_PATTERNS = [
    re.compile(r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"),  # UUID
    re.compile(r"/\d{4,}"),   # Long numeric IDs
]

# Paths to skip entirely (no metrics recorded — avoids noise)
_SKIP_PATHS = frozenset(["/metrics", "/health", "/favicon.ico"])


def _normalise_path(path: str) -> str:
    """Replace dynamic segments in URL paths to keep label cardinality sane."""
    for pattern in _ID_PATTERNS:
        path = pattern.sub("/{id}", path)
    return path


# ── Middleware ─────────────────────────────────────────────────────────────────
class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Starlette/FastAPI middleware that records Prometheus metrics for every
    HTTP request.  Attach AFTER all other middleware so it wraps everything.
    """

    def __init__(self, app, app_name: str = "ecommerce_platform", app_version: str = "1.0.0", environment: str = "development"):
        super().__init__(app)
        APP_INFO.info({
            "app_name": app_name,
            "version": app_version,
            "environment": environment,
        })

    async def dispatch(self, request: Request, call_next) -> Response:
        path = _normalise_path(request.url.path)

        # Skip internal / low-value paths
        if path in _SKIP_PATHS:
            return await call_next(request)

        method = request.method

        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=path).inc()
        start = time.perf_counter()

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            HTTP_REQUESTS_TOTAL.labels(
                method=method, endpoint=path, status_code=500
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method, endpoint=path
            ).observe(time.perf_counter() - start)
            raise exc
        finally:
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=path).dec()

        duration = time.perf_counter() - start
        status = str(response.status_code)

        HTTP_REQUESTS_TOTAL.labels(
            method=method, endpoint=path, status_code=status
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=method, endpoint=path
        ).observe(duration)

        content_length = response.headers.get("content-length")
        if content_length and content_length.isdigit():
            HTTP_RESPONSE_SIZE_BYTES.labels(
                method=method, endpoint=path
            ).observe(int(content_length))

        return response
