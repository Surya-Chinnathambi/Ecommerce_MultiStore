"""
Correlation ID Middleware
Attaches a unique request correlation ID to every inbound request and echoes
it back on every response.  Propagated as ``request.state.correlation_id`` so
any handler or service can include it in log records, Sentry breadcrumbs, or
outbound HTTP calls to downstream services.

Accepts:
  X-Correlation-ID  (canonical name, used by AWS ALB / GCP)
  X-Request-ID      (common alternative used by nginx / Heroku)

If neither is present a new UUID4 is generated.
"""
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Attach / propagate a correlation ID for every HTTP request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Request-ID")
            or str(uuid.uuid4())
        )

        # Make available to all downstream code via request.state
        request.state.correlation_id = correlation_id

        # Inject into Python logging context for the duration of this request
        # (works when using structlog or python-json-logger)
        logger_adapter = logging.LoggerAdapter(
            logger, {"correlation_id": correlation_id}
        )
        logger_adapter.debug(
            "Request started",
            extra={"method": request.method, "path": request.url.path},
        )

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
