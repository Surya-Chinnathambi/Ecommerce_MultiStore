from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List

from app.core.database import get_db
from app.core.config import settings
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_current_user,
    get_current_customer,
    get_current_admin,
    get_current_super_admin,
    generate_password_reset_token,
    blacklist_token,
    check_account_locked,
    clear_failed_logins,
    generate_api_key,
    hash_api_key,
    create_token_pair,
    rotate_refresh_token,
)
from app.models.auth_models import User, UserRole, Address, APIKey
from app.models.models import Store, Order
from app.schemas.schemas import APIResponse, OrderResponse
from app.schemas.auth_schemas import (
    UserRegister,
    UserLogin,
    Token,
    RefreshTokenRequest,
    UserResponse,
    ChangePassword,
    UpdateProfile,
    AddressCreate,
    AddressUpdate,
    AddressResponse,
    AdminRegister,
    PasswordResetRequest,
    PasswordResetConfirm,
    APIKeyCreate,
    APIKeyResponse,
    APIKeyCreatedResponse,
)

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_customer(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new customer"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.phone == user_data.phone)
    ).first()
    
    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
    
    # Create new user
    user = User(
        email=user_data.email,
        phone=user_data.phone,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    access_token, refresh_token = create_token_pair(
        db=db,
        user_id=str(user.id),
        role=user.role.value
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_expires_in": 30 * 24 * 60 * 60,
        "user": UserResponse.model_validate(user),
    }


@router.post("/login", response_model=Token)
async def login(credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login user — enforces account lockout after repeated failures.
    
    Accepts form-urlencoded body with username (= email) and password.
    """
    email = credentials.username  # OAuth2 form uses 'username'; we treat it as email
    # Check lockout BEFORE hitting the DB (prevents timing attacks)
    await check_account_locked(email)

    user = db.query(User).filter(User.email == email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        await record_failed_login(email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support.",
        )
    
    # Successful login — clear failure counter and update last_login
    await clear_failed_logins(email)
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    access_token, refresh_token = create_token_pair(
        db=db,
        user_id=str(user.id),
        role=user.role.value,
        user_agent=credentials.client_id, # Simplified usage
        ip_address=None # Would need request for this
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_expires_in": 30 * 24 * 60 * 60,
        "user": UserResponse.model_validate(user),
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    body: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout — revokes the refresh token and blacklists the access token.
    """
    from app.models.user_token_models import UserRefreshToken
    
    # Revoke the specific refresh token
    db.query(UserRefreshToken).filter(
        UserRefreshToken.jti == decode_token(body.refresh_token).get("jti"),
        UserRefreshToken.user_id == current_user.id
    ).update({"is_revoked": True, "revoked_at": datetime.utcnow()})
    
    # Blacklist access token
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.removeprefix("Bearer ").strip()
    if token:
        payload = decode_token(token)
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and exp:
            await blacklist_token(jti, datetime.utcfromtimestamp(exp))
    
    db.commit()
    return None


@router.post("/refresh", response_model=Token)
async def refresh_tokens(
    request: Request,
    body: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Refresh token rotation — invalidates old refresh token, issues a new pair.
    """
    # Verify and get DB record
    db_token = verify_refresh_token(db, body.refresh_token)
    
    # Rotate
    access_token, refresh_token = await rotate_refresh_token(
        db=db,
        old_token_record=db_token,
        user_agent=request.headers.get("User-Agent")
    )
    
    db.commit()
    
    user = db_token.user
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_expires_in": 30 * 24 * 60 * 60,
        "user": UserResponse.model_validate(user),
    }


@router.get("/profile", response_model=UserResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile (alias for /me)"""
    return current_user


@router.put("/me", response_model=UserResponse)
def update_profile(
    profile_data: UpdateProfile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    if profile_data.full_name:
        current_user.full_name = profile_data.full_name
    
    if profile_data.phone:
        # Check if phone is already taken by another user
        existing = db.query(User).filter(
            User.phone == profile_data.phone,
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already in use"
            )
        current_user.phone = profile_data.phone
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.post("/change-password")
def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    # Verify old password
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.password_hash = get_password_hash(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Password changed successfully"}


# Address Management
@router.post("/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address(
    address_data: AddressCreate,
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Create a new address for customer"""
    # If this is set as default, unset other defaults
    if address_data.is_default:
        db.query(Address).filter(
            Address.user_id == current_user.id,
            Address.is_default == True
        ).update({"is_default": False})
    
    address = Address(
        user_id=current_user.id,
        **address_data.model_dump()
    )
    
    db.add(address)
    db.commit()
    db.refresh(address)
    
    return address


@router.get("/addresses", response_model=List[AddressResponse])
def list_addresses(
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get all addresses for current customer"""
    addresses = db.query(Address).filter(Address.user_id == current_user.id).all()
    return addresses


@router.put("/addresses/{address_id}", response_model=AddressResponse)
def update_address(
    address_id: str,
    address_data: AddressUpdate,
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Update an address"""
    address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == current_user.id
    ).first()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    # If setting as default, unset other defaults
    if address_data.is_default:
        db.query(Address).filter(
            Address.user_id == current_user.id,
            Address.id != address_id,
            Address.is_default == True
        ).update({"is_default": False})
    
    # Update fields
    update_data = address_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(address, field, value)
    
    address.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(address)
    
    return address


@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(
    address_id: str,
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Delete an address"""
    address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == current_user.id
    ).first()
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    db.delete(address)
    db.commit()
    
    return None


# Admin Registration
@router.post("/admin/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_admin(
    admin_data: AdminRegister,
    db: Session = Depends(get_db)
):
    """Register a new admin for a store"""
    # Verify store exists
    store = db.query(Store).filter(Store.id == admin_data.store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == admin_data.email) | (User.phone == admin_data.phone)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or phone already registered"
        )
    
    # Create admin user
    user = User(
        email=admin_data.email,
        phone=admin_data.phone,
        password_hash=get_password_hash(admin_data.password),
        full_name=admin_data.full_name,
        role=UserRole.ADMIN,
        store_id=admin_data.store_id,
        is_active=True,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value, "store_id": str(user.store_id)}
    )
    refresh_token, _ = create_refresh_token(
        data={"sub": str(user.id), "role": user.role.value, "store_id": str(user.store_id)}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_expires_in": 30 * 24 * 60 * 60,
        "user": user,
    }


# Password Reset
@router.post("/password-reset/request")
def request_password_reset(
    request_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset (sends email in production)"""
    user = db.query(User).filter(User.email == request_data.email).first()
    
    if user:
        # Generate reset token
        reset_token = generate_password_reset_token()
        user.password_reset_token = reset_token
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        
        # In production, send email with reset link
        # For now, return token (development only)
        return {
            "message": "Password reset email sent",
            "reset_token": reset_token  # Remove this in production
        }
    
    # Don't reveal if email exists
    return {"message": "If that email exists, a password reset link has been sent"}


@router.post("/password-reset/confirm")
def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token"""
    user = db.query(User).filter(
        User.password_reset_token == reset_data.token
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    if user.password_reset_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
    
    # Update password
    user.password_hash = get_password_hash(reset_data.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Password reset successful"}


# Order history endpoint
@router.get("/my-orders", response_model=APIResponse)
async def get_my_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all orders for the current logged-in user
    """
    from app.models.models import Order
    from sqlalchemy import desc
    
    orders = db.query(Order).filter(
        Order.user_id == current_user.id
    ).order_by(desc(Order.created_at)).all()

    orders_data = []
    for order in orders:
        order_dict = OrderResponse.model_validate(order).model_dump(mode='json')
        orders_data.append(order_dict)

    return APIResponse(
        success=True,
        data=orders_data,
        meta={"total": len(orders_data)}
    )


# ──────────────────────────────────────────────────────────────────────────────
# API Key Management
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/api-keys", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Create a new API key (admin/super-admin only).
    The raw key is returned **once** — store it securely; it cannot be retrieved again.
    """
    from datetime import timezone

    # Super-admins can create keys for any store; admins only for their own.
    if key_data.store_id and current_user.role != UserRole.SUPER_ADMIN:
        if str(current_user.store_id) != str(key_data.store_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create key for another store")

    raw_key, key_hash = generate_api_key(is_test=key_data.is_test)

    expires_at = None
    if key_data.expires_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_days)

    api_key = APIKey(
        name=key_data.name,
        key_hash=key_hash,
        key_prefix=raw_key[:12],
        is_test=key_data.is_test,
        scopes=key_data.scopes,
        store_id=key_data.store_id or current_user.store_id,
        user_id=current_user.id,
        expires_at=expires_at,
    )

    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return {**APIKeyResponse.model_validate(api_key).model_dump(mode='json'), "raw_key": raw_key}


@router.get("/api-keys", response_model=List[APIKeyResponse])
def list_api_keys(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all API keys for the current admin's store (or all stores for super-admin)."""
    query = db.query(APIKey)
    if current_user.role != UserRole.SUPER_ADMIN:
        query = query.filter(APIKey.store_id == current_user.store_id)
    return query.order_by(APIKey.created_at.desc()).all()


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Revoke (soft-delete) an API key."""
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    if current_user.role != UserRole.SUPER_ADMIN and str(api_key.store_id) != str(current_user.store_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to revoke this key")

    api_key.is_active = False
    api_key.revoked_at = datetime.utcnow()
    db.commit()
    return None


@router.patch("/api-keys/{key_id}/rotate", response_model=APIKeyCreatedResponse)
def rotate_api_key(
    key_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Rotate an API key — revoke the existing key and issue a new one with the same settings.
    Returns the new raw key (shown once).
    """
    old_key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.is_active == True).first()
    if not old_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active API key not found")
    if current_user.role != UserRole.SUPER_ADMIN and str(old_key.store_id) != str(current_user.store_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    # Revoke old key
    old_key.is_active   = False
    old_key.revoked_at  = datetime.utcnow()

    # Create replacement
    raw_key, key_hash = generate_api_key(is_test=old_key.is_test)
    new_key = APIKey(
        name=old_key.name + " (rotated)",
        key_hash=key_hash,
        key_prefix=raw_key[:12],
        is_test=old_key.is_test,
        scopes=old_key.scopes,
        store_id=old_key.store_id,
        user_id=current_user.id,
        expires_at=old_key.expires_at,
    )
    db.add(new_key)
    db.commit()
    db.refresh(new_key)

    return {**APIKeyResponse.model_validate(new_key).model_dump(mode='json'), "raw_key": raw_key}
