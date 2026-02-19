"""
Security Headers Middleware
Implements OWASP security headers and additional protections
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import secrets
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    Based on OWASP Security Headers recommendations
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID for tracing
        request_id = secrets.token_hex(16)
        request.state.request_id = request_id
        
        response = await call_next(request)
        
        # Security Headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy (adjust as needed)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://checkout.razorpay.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' https://api.stripe.com https://api.razorpay.com wss:; "
            "frame-src https://js.stripe.com https://api.razorpay.com; "
            "object-src 'none'; "
            "base-uri 'self';"
        )
        
        # HSTS (only in production)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Remove Server header
        if "server" in response.headers:
            del response.headers["server"]
        
        return response


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """
    Sanitize and validate inputs to prevent injection attacks
    """
    
    # Common SQL injection patterns
    SQL_PATTERNS = [
        "' OR '1'='1",
        "'; DROP TABLE",
        "UNION SELECT",
        "1=1--",
        "' OR ''='",
    ]
    
    # Common XSS patterns
    XSS_PATTERNS = [
        "<script>",
        "javascript:",
        "onerror=",
        "onclick=",
        "onload=",
    ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check query parameters
        query_string = str(request.query_params)
        
        for pattern in self.SQL_PATTERNS + self.XSS_PATTERNS:
            if pattern.lower() in query_string.lower():
                logger.warning(
                    f"Potential injection attempt blocked. "
                    f"IP: {request.client.host}, Path: {request.url.path}, "
                    f"Pattern: {pattern}"
                )
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": {
                            "code": "INVALID_INPUT",
                            "message": "Request contains invalid characters"
                        }
                    }
                )
        
        return await call_next(request)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Log all requests for audit trail
    """
    
    # Sensitive paths that should be logged with extra detail
    SENSITIVE_PATHS = [
        "/api/v1/auth/",
        "/api/v1/admin/",
        "/api/v1/payments/",
        "/api/v1/sync/",
    ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get request details
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        method = request.method
        path = request.url.path
        
        # Check if this is a sensitive path
        is_sensitive = any(path.startswith(sp) for sp in self.SENSITIVE_PATHS)
        
        response = await call_next(request)
        
        # Log the request
        log_data = {
            "request_id": getattr(request.state, "request_id", "unknown"),
            "client_ip": client_ip,
            "method": method,
            "path": path,
            "status_code": response.status_code,
            "user_agent": user_agent[:100],  # Truncate user agent
        }
        
        # Add user info if available
        if hasattr(request.state, "user_id"):
            log_data["user_id"] = request.state.user_id
        
        if hasattr(request.state, "store_id"):
            log_data["store_id"] = request.state.store_id
        
        # Log at appropriate level
        if is_sensitive or response.status_code >= 400:
            logger.info(f"Audit: {log_data}")
        else:
            logger.debug(f"Request: {log_data}")
        
        return response
