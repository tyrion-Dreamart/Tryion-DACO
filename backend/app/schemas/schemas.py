"""
DACO — Schemas Pydantic v2
Separación clara: Base → Create → Update → Response
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.models.models import ContactType, EntityStatus, UserRole


# ─── Shared ───────────────────────────────────────────────────────────────────
class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime


# ─── Auth ────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


# ─── User ────────────────────────────────────────────────────────────────────
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    role: UserRole = UserRole.OPERATOR


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase, TimestampMixin):
    id: str
    is_active: bool
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Corporate ───────────────────────────────────────────────────────────────
class CorporateBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    trade_name: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    status: EntityStatus = EntityStatus.ACTIVE


class CorporateCreate(CorporateBase):
    pass


class CorporateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    trade_name: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[EntityStatus] = None


class CorporateResponse(CorporateBase, TimestampMixin):
    id: str
    legal_entities_count: Optional[int] = 0

    model_config = {"from_attributes": True}


class CorporateListResponse(BaseModel):
    items: list[CorporateResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ─── Legal Entity ─────────────────────────────────────────────────────────────
class LegalEntityBase(BaseModel):
    legal_name: str = Field(min_length=2, max_length=255)
    trade_name: Optional[str] = Field(None, max_length=255)
    rfc: Optional[str] = Field(None, min_length=12, max_length=13, pattern=r"^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$")
    tax_regime: Optional[str] = Field(None, max_length=100)
    address_street: Optional[str] = None
    address_exterior: Optional[str] = None
    address_interior: Optional[str] = None
    address_colony: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_postal_code: Optional[str] = Field(None, pattern=r"^\d{5}$")
    address_country: str = Field(default="MEX", max_length=3)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    is_issuer: bool = True
    status: EntityStatus = EntityStatus.ACTIVE
    notes: Optional[str] = None


class LegalEntityCreate(LegalEntityBase):
    corporate_id: Optional[str] = None



class LegalEntityUpdate(BaseModel):
    legal_name: Optional[str] = Field(None, min_length=2, max_length=255)
    trade_name: Optional[str] = None
    rfc: Optional[str] = Field(None, min_length=12, max_length=13)
    tax_regime: Optional[str] = None
    address_street: Optional[str] = None
    address_exterior: Optional[str] = None
    address_interior: Optional[str] = None
    address_colony: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    is_issuer: Optional[bool] = None
    status: Optional[EntityStatus] = None
    notes: Optional[str] = None


class LegalEntityResponse(LegalEntityBase, TimestampMixin):
    id: str
    corporate_id: Optional[str] = None
    contacts_count: Optional[int] = 0

    model_config = {"from_attributes": True}


class LegalEntityListResponse(BaseModel):
    items: list[LegalEntityResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ─── Contact ─────────────────────────────────────────────────────────────────
class ContactBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=150)
    department: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    phone_ext: Optional[str] = Field(None, max_length=10)
    mobile: Optional[str] = Field(None, max_length=20)
    contact_type: ContactType = ContactType.CLIENT
    is_primary: bool = False
    is_billing: bool = False
    is_active: bool = True
    notes: Optional[str] = None


class ContactCreate(ContactBase):
    legal_entity_id: str


class ContactUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    phone_ext: Optional[str] = None
    mobile: Optional[str] = None
    contact_type: Optional[ContactType] = None
    is_primary: Optional[bool] = None
    is_billing: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class ContactResponse(ContactBase, TimestampMixin):
    id: str
    legal_entity_id: str

    model_config = {"from_attributes": True}


class ContactListResponse(BaseModel):
    items: list[ContactResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ─── Pagination ───────────────────────────────────────────────────────────────
class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    search: Optional[str] = None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
