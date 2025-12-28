from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List

from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_customer,
    get_current_admin,
    generate_password_reset_token,
)
from app.models.auth_models import User, UserRole, Address
from app.models.models import Store, Order
from app.schemas.schemas import APIResponse, OrderResponse
from app.schemas.auth_schemas import (
    UserRegister,
    UserLogin,
    Token,
    UserResponse,
    ChangePassword,
    UpdateProfile,
    AddressCreate,
    AddressUpdate,
    AddressResponse,
    AdminRegister,
    PasswordResetRequest,
    PasswordResetConfirm,
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
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 604800,  # 7 days in seconds
        "user": user
    }


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support.",
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 604800,  # 7 days
        "user": user
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


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
        **address_data.dict()
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
    update_data = address_data.dict(exclude_unset=True)
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
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value, "store_id": str(user.store_id)}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 604800,
        "user": user
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
        order_dict = OrderResponse.from_orm(order).dict()
        orders_data.append(order_dict)

    return APIResponse(
        success=True,
        data=orders_data,
        meta={"total": len(orders_data)}
    )



