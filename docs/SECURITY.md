# Security Hardening Guide

## OWASP Top 10 Compliance Matrix

| # | OWASP Risk | Implementation | Status |
|---|------------|----------------|--------|
| A01 | Broken Access Control | RBAC + Tenant Isolation | ✅ Implemented |
| A02 | Cryptographic Failures | bcrypt + AES-256 + TLS | ✅ Implemented |
| A03 | Injection | SQLAlchemy ORM + Sanitization | ✅ Implemented |
| A04 | Insecure Design | Security Reviews + Threat Modeling | ⚠️ In Progress |
| A05 | Security Misconfiguration | Hardened configs + Secrets management | ✅ Implemented |
| A06 | Vulnerable Components | Dependency scanning + Updates | ⚠️ Partial |
| A07 | Auth Failures | JWT + MFA Ready + Account lockout | ✅ Implemented |
| A08 | Software/Data Integrity | Signed tokens + Input validation | ✅ Implemented |
| A09 | Logging Failures | Comprehensive audit logs | ✅ Implemented |
| A10 | SSRF | URL validation + Allowlists | ✅ Implemented |

---

## 1. Authentication Security

### 1.1 JWT Token Security

```python
# Token configuration
ACCESS_TOKEN_EXPIRE_MINUTES = 30      # Short-lived access tokens
REFRESH_TOKEN_EXPIRE_DAYS = 30        # Long-lived refresh tokens
ALGORITHM = "HS256"                   # Use RS256 for production

# Token structure
{
    "sub": "user-uuid",
    "role": "admin",
    "store_id": "store-uuid",
    "type": "access|refresh",
    "iat": 1708300800,
    "exp": 1708302600,
    "jti": "unique-token-id"  # For revocation
}
```

### 1.2 Password Security

```python
# Password hashing with bcrypt
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Increased from default 10
)

# Password validation rules
def validate_password(password: str) -> bool:
    """
    Password must:
    - Be at least 12 characters
    - Contain uppercase and lowercase
    - Contain numbers
    - Contain special characters
    - Not be in common password list
    """
    if len(password) < 12:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    if password.lower() in COMMON_PASSWORDS:
        return False
    return True
```

### 1.3 Account Security

```python
# Account lockout after failed attempts
class LoginAttemptTracker:
    MAX_ATTEMPTS = 5
    LOCKOUT_DURATION = 900  # 15 minutes
    
    async def check_and_record(self, email: str, success: bool):
        key = f"login_attempts:{email}"
        
        if success:
            await redis.delete(key)
            return True
        
        attempts = await redis.incr(key)
        await redis.expire(key, self.LOCKOUT_DURATION)
        
        if attempts >= self.MAX_ATTEMPTS:
            raise HTTPException(
                status_code=429,
                detail=f"Account locked. Try again in {self.LOCKOUT_DURATION // 60} minutes."
            )
        
        return False
```

---

## 2. Input Validation & Sanitization

### 2.1 Request Validation

```python
# Pydantic schema validation
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=500)
    description: Optional[str] = Field(None, max_length=10000)
    price: float = Field(..., gt=0, le=10000000)
    quantity: int = Field(default=0, ge=0, le=1000000)
    
    @validator('name')
    def sanitize_name(cls, v):
        # Remove potential HTML/script
        return bleach.clean(v, tags=[], strip=True)
    
    @validator('description')
    def sanitize_description(cls, v):
        if v:
            # Allow basic formatting
            return bleach.clean(
                v, 
                tags=['p', 'br', 'b', 'i', 'ul', 'li'],
                strip=True
            )
        return v
```

### 2.2 SQL Injection Prevention

```python
# Always use parameterized queries (SQLAlchemy ORM)
# NEVER do this:
# db.execute(f"SELECT * FROM users WHERE id = '{user_id}'")

# Always do this:
user = db.query(User).filter(User.id == user_id).first()

# For raw SQL, use text() with parameters:
from sqlalchemy import text
result = db.execute(
    text("SELECT * FROM users WHERE email = :email"),
    {"email": email}
)
```

### 2.3 XSS Prevention

```python
# Content Security Policy header
CSP_HEADER = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://js.stripe.com; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "connect-src 'self' https://api.stripe.com; "
    "frame-src https://js.stripe.com; "
    "object-src 'none';"
)

# JSON response escaping (automatic in FastAPI)
# HTML escaping for any user-generated content
import html
safe_content = html.escape(user_content)
```

---

## 3. CSRF Protection

### 3.1 Token-Based CSRF Protection

```python
import secrets

class CSRFProtection:
    TOKEN_LENGTH = 32
    HEADER_NAME = "X-CSRF-Token"
    COOKIE_NAME = "csrf_token"
    
    def generate_token(self) -> str:
        return secrets.token_urlsafe(self.TOKEN_LENGTH)
    
    def set_csrf_cookie(self, response: Response, token: str):
        response.set_cookie(
            self.COOKIE_NAME,
            token,
            httponly=True,
            secure=True,  # HTTPS only
            samesite="strict",
            max_age=3600
        )
    
    def validate_csrf(self, request: Request) -> bool:
        cookie_token = request.cookies.get(self.COOKIE_NAME)
        header_token = request.headers.get(self.HEADER_NAME)
        
        if not cookie_token or not header_token:
            return False
        
        return secrets.compare_digest(cookie_token, header_token)
```

### 3.2 SameSite Cookie Configuration

```python
# Session cookie settings
SESSION_COOKIE_CONFIG = {
    "httponly": True,
    "secure": True,  # HTTPS only
    "samesite": "strict",  # Prevent CSRF
    "max_age": 86400,  # 24 hours
    "path": "/",
    "domain": None  # Set for specific domain
}
```

---

## 4. Secure File Uploads

### 4.1 File Validation

```python
import magic
from PIL import Image
import io

class SecureFileUpload:
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    ALLOWED_MIME_TYPES = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp'
    }
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_DIMENSIONS = (4096, 4096)
    
    async def validate_and_process(self, file: UploadFile) -> bytes:
        # Check file size
        content = await file.read()
        if len(content) > self.MAX_FILE_SIZE:
            raise ValueError("File too large")
        
        # Check extension
        ext = Path(file.filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError("Invalid file extension")
        
        # Check MIME type using magic bytes
        mime = magic.from_buffer(content, mime=True)
        if mime not in self.ALLOWED_MIME_TYPES:
            raise ValueError("Invalid file type")
        
        # Validate image content
        try:
            img = Image.open(io.BytesIO(content))
            img.verify()  # Verify it's a valid image
            
            # Check dimensions
            if img.size[0] > self.MAX_DIMENSIONS[0] or \
               img.size[1] > self.MAX_DIMENSIONS[1]:
                raise ValueError("Image dimensions too large")
            
            # Re-encode to strip metadata/malicious content
            img = Image.open(io.BytesIO(content))
            output = io.BytesIO()
            img.save(output, format=img.format, quality=85)
            return output.getvalue()
            
        except Exception as e:
            raise ValueError(f"Invalid image: {e}")
```

---

## 5. Payment Security (PCI DSS Compliance)

### 5.1 Secure Payment Handling

```python
class SecurePaymentHandler:
    """
    PCI DSS Compliance Guidelines:
    1. Never store CVV/CVC
    2. Never log card numbers
    3. Use tokenization
    4. Use TLS 1.2+
    5. Implement strong access controls
    """
    
    def mask_card_number(self, card_number: str) -> str:
        """Show only last 4 digits"""
        return f"****-****-****-{card_number[-4:]}"
    
    async def process_payment(self, payment_data: dict):
        # Never store raw card data
        # Use payment gateway tokenization
        
        # Log only safe data
        logger.info(f"Processing payment: amount={payment_data['amount']}, "
                   f"card_last4={payment_data.get('card_last4', 'N/A')}")
        
        # All communication over TLS
        async with httpx.AsyncClient(verify=True) as client:
            response = await client.post(
                "https://api.stripe.com/v1/payment_intents",
                headers={"Authorization": f"Bearer {settings.STRIPE_SECRET_KEY}"},
                data=payment_data
            )
        
        return response.json()
```

### 5.2 Webhook Verification

```python
import hmac
import hashlib

class WebhookVerifier:
    def verify_stripe_signature(
        self, 
        payload: bytes, 
        signature: str, 
        secret: str
    ) -> bool:
        """Verify Stripe webhook signature"""
        parts = dict(p.split('=') for p in signature.split(','))
        timestamp = parts.get('t')
        expected_sig = parts.get('v1')
        
        signed_payload = f"{timestamp}.{payload.decode()}"
        computed_sig = hmac.new(
            secret.encode(),
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(computed_sig, expected_sig)
    
    def verify_razorpay_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
        secret: str
    ) -> bool:
        """Verify Razorpay webhook signature"""
        body = f"{order_id}|{payment_id}"
        computed_sig = hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(computed_sig, signature)
```

---

## 6. Secrets Management

### 6.1 Environment Variables

```python
# Never commit secrets to git
# Use .env files locally, environment variables in production

# .gitignore
.env
.env.local
.env.production
*.pem
*.key

# docker-compose.yml - reference from environment
services:
  backend:
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
```

### 6.2 Secrets Rotation

```python
class SecretsManager:
    """
    Best practices for secrets:
    1. Rotate secrets regularly
    2. Use different secrets per environment
    3. Never log secrets
    4. Use secret scanning in CI/CD
    """
    
    @staticmethod
    def generate_secret_key() -> str:
        """Generate a cryptographically secure secret key"""
        import secrets
        return secrets.token_hex(32)  # 256-bit key
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate an API key with prefix for identification"""
        import secrets
        key = secrets.token_urlsafe(32)
        return f"eck_{key}"  # ecommerce-key prefix
```

---

## 7. Audit Logging

### 7.1 Security Event Logging

```python
import logging
from datetime import datetime

class SecurityAuditLogger:
    def __init__(self):
        self.logger = logging.getLogger("security")
        handler = logging.FileHandler("security_audit.log")
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
    
    def log_auth_attempt(
        self,
        email: str,
        success: bool,
        ip_address: str,
        user_agent: str
    ):
        self.logger.info(
            f"AUTH_ATTEMPT | "
            f"email={email} | "
            f"success={success} | "
            f"ip={ip_address} | "
            f"ua={user_agent[:50]}"
        )
    
    def log_permission_denied(
        self,
        user_id: str,
        resource: str,
        action: str
    ):
        self.logger.warning(
            f"PERMISSION_DENIED | "
            f"user_id={user_id} | "
            f"resource={resource} | "
            f"action={action}"
        )
    
    def log_data_access(
        self,
        user_id: str,
        resource: str,
        record_ids: list
    ):
        self.logger.info(
            f"DATA_ACCESS | "
            f"user_id={user_id} | "
            f"resource={resource} | "
            f"records={len(record_ids)}"
        )
```

---

## 8. Security Checklist

### Pre-Deployment Security Checklist

- [ ] All secrets removed from codebase
- [ ] Environment variables properly configured
- [ ] HTTPS/TLS enforced
- [ ] CORS configured for production domains only
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified
- [ ] CSRF protection enabled
- [ ] File upload restrictions in place
- [ ] Payment handling PCI compliant
- [ ] Audit logging enabled
- [ ] Error messages don't leak sensitive info
- [ ] Dependencies scanned for vulnerabilities
- [ ] Penetration testing completed

### Regular Security Tasks

- [ ] Weekly: Review security logs
- [ ] Monthly: Update dependencies
- [ ] Quarterly: Rotate secrets
- [ ] Quarterly: Security audit
- [ ] Annually: Penetration testing
- [ ] Annually: Compliance review
