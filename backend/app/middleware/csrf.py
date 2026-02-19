"""
CSRF Protection Middleware
Token-based CSRF protection for state-changing operations.
"""
import secrets
from typing import Optional
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import MutableHeaders
import logging

logger = logging.getLogger(__name__)


class CSRFProtection:
    """
    CSRF Token Manager
    
    Provides double-submit cookie pattern for CSRF protection.
    """
    
    TOKEN_LENGTH = 32
    HEADER_NAME = "X-CSRF-Token"
    COOKIE_NAME = "csrf_token"
    COOKIE_MAX_AGE = 3600  # 1 hour
    
    # Methods that require CSRF protection
    PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    
    # Paths exempt from CSRF (e.g., webhooks, API tokens)
    EXEMPT_PATHS = {
        "/api/v1/webhooks/stripe",
        "/api/v1/webhooks/razorpay",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
    }
    
    def generate_token(self) -> str:
        """Generate a cryptographically secure CSRF token."""
        return secrets.token_urlsafe(self.TOKEN_LENGTH)
    
    def set_csrf_cookie(
        self, 
        response: Response, 
        token: str,
        domain: Optional[str] = None
    ):
        """Set CSRF token cookie on response."""
        response.set_cookie(
            key=self.COOKIE_NAME,
            value=token,
            max_age=self.COOKIE_MAX_AGE,
            httponly=False,  # Must be readable by JavaScript
            secure=True,     # HTTPS only
            samesite="strict",
            domain=domain,
            path="/"
        )
    
    def validate_csrf(
        self, 
        request: Request
    ) -> bool:
        """
        Validate CSRF token using double-submit cookie pattern.
        
        Compares token from cookie with token from header.
        Uses constant-time comparison to prevent timing attacks.
        """
        cookie_token = request.cookies.get(self.COOKIE_NAME)
        header_token = request.headers.get(self.HEADER_NAME)
        
        if not cookie_token or not header_token:
            return False
        
        # Constant-time comparison
        return secrets.compare_digest(cookie_token, header_token)
    
    def is_exempt(self, request: Request) -> bool:
        """Check if request path is exempt from CSRF protection."""
        return request.url.path in self.EXEMPT_PATHS
    
    def requires_protection(self, request: Request) -> bool:
        """Check if request method requires CSRF protection."""
        return request.method in self.PROTECTED_METHODS


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection Middleware
    
    Implements double-submit cookie pattern:
    1. Server sets a CSRF token cookie
    2. Client includes token in X-CSRF-Token header
    3. Server validates cookie token matches header token
    """
    
    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.csrf = CSRFProtection()
        self.enabled = enabled
    
    async def dispatch(self, request: Request, call_next):
        # Skip if disabled
        if not self.enabled:
            return await call_next(request)
        
        # Generate token for GET requests (to set cookie)
        if request.method == "GET":
            response = await call_next(request)
            
            # Only set cookie if not already present
            if self.csrf.COOKIE_NAME not in request.cookies:
                token = self.csrf.generate_token()
                self.csrf.set_csrf_cookie(response, token)
            
            return response
        
        # Check if protection needed
        if self.csrf.requires_protection(request):
            # Skip exempt paths
            if not self.csrf.is_exempt(request):
                if not self.csrf.validate_csrf(request):
                    logger.warning(
                        f"CSRF validation failed: "
                        f"path={request.url.path}, "
                        f"method={request.method}, "
                        f"ip={request.client.host if request.client else 'unknown'}"
                    )
                    raise HTTPException(
                        status_code=403,
                        detail="CSRF token validation failed"
                    )
        
        response = await call_next(request)
        return response


# Token endpoint for SPA clients
from fastapi import APIRouter

csrf_router = APIRouter(prefix="/csrf", tags=["csrf"])
csrf_protection = CSRFProtection()


@csrf_router.get("/token")
async def get_csrf_token(response: Response):
    """
    Get a new CSRF token.
    
    SPA clients should call this endpoint on page load
    and include the returned token in the X-CSRF-Token header
    for all state-changing requests.
    """
    token = csrf_protection.generate_token()
    csrf_protection.set_csrf_cookie(response, token)
    
    return {"csrf_token": token}
