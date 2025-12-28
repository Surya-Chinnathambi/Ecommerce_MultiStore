from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from uuid import UUID
import re


# User Registration
class UserRegister(BaseModel):
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)

    @validator('phone')
    def validate_phone(cls, v):
        pattern = r'^\+?[1-9]\d{9,14}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid phone number format')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


# User Login
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# User Response
class UserResponse(BaseModel):
    id: UUID
    email: str
    phone: Optional[str]
    full_name: str
    role: str
    store_id: Optional[UUID]
    is_active: bool
    is_email_verified: bool
    is_phone_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


# Token Response
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


# Change Password
class ChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


# Update Profile
class UpdateProfile(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)

    @validator('phone')
    def validate_phone(cls, v):
        if v is not None:
            pattern = r'^\+?[1-9]\d{9,14}$'
            if not re.match(pattern, v):
                raise ValueError('Invalid phone number format')
        return v


# Address Schemas
class AddressCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: str = Field(..., min_length=10, max_length=20)
    address_line1: str = Field(..., min_length=10, max_length=500)
    address_line2: Optional[str] = Field(None, max_length=500)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    pincode: str = Field(..., pattern=r'^\d{6}$')
    landmark: Optional[str] = Field(None, max_length=255)
    is_default: bool = False
    address_type: str = Field(default="home", pattern=r'^(home|work|other)$')


class AddressUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    address_line1: Optional[str] = Field(None, min_length=10, max_length=500)
    address_line2: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    pincode: Optional[str] = Field(None, pattern=r'^\d{6}$')
    landmark: Optional[str] = Field(None, max_length=255)
    is_default: Optional[bool] = None
    address_type: Optional[str] = Field(None, pattern=r'^(home|work|other)$')


class AddressResponse(BaseModel):
    id: UUID
    full_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str]
    city: str
    state: str
    pincode: str
    landmark: Optional[str]
    is_default: bool
    address_type: str
    created_at: datetime

    class Config:
        from_attributes = True


# Admin Registration
class AdminRegister(BaseModel):
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)
    store_id: UUID

    @validator('phone')
    def validate_phone(cls, v):
        pattern = r'^\+?[1-9]\d{9,14}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid phone number format')
        return v


# Password Reset Request
class PasswordResetRequest(BaseModel):
    email: EmailStr


# Password Reset Confirm
class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
