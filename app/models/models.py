"""
DACO — Modelos de base de datos
Separación: Corporate (grupo) → LegalEntity (razón social) → Contact (personas)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text,
    UniqueConstraint, func, Enum as SAEnum, Numeric,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# ─── Enums ───────────────────────────────────────────────────────────────────
import enum


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"


class ContactType(str, enum.Enum):
    CLIENT = "client"
    SUPPLIER = "supplier"
    BOTH = "both"
    INTERNAL = "internal"


class EntityStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class InvoiceStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    TRANSFER = "transfer"
    CHECK = "check"
    CARD = "card"
    OTHER = "other"


# ─── Users ───────────────────────────────────────────────────────────────────
class User(Base):
    """Usuarios del sistema DACO."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"), default=UserRole.OPERATOR, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


# ─── Corporate ───────────────────────────────────────────────────────────────
class Corporate(Base):
    """
    Grupo corporativo (nivel más alto).
    Ej: TYRION Group — puede tener múltiples razones sociales.
    """
    __tablename__ = "corporates"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    trade_name: Mapped[Optional[str]] = mapped_column(String(255))
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    website: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[EntityStatus] = mapped_column(
        SAEnum(EntityStatus, name="entity_status"),
        default=EntityStatus.ACTIVE,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    legal_entities: Mapped[list["LegalEntity"]] = relationship(
        back_populates="corporate", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Corporate {self.name}>"


# ─── Legal Entity (Razón Social) ─────────────────────────────────────────────
class LegalEntity(Base):
    """
    Razón social / persona moral o física con actividad empresarial.
    Puede emitir facturas, cotizaciones y tener CxC propias.
    """
    __tablename__ = "legal_entities"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    corporate_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("corporates.id", ondelete="SET NULL"), nullable=True, index=True
    )
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    trade_name: Mapped[Optional[str]] = mapped_column(String(255))
    rfc: Mapped[Optional[str]] = mapped_column(String(13), unique=True, index=True)
    tax_regime: Mapped[Optional[str]] = mapped_column(String(100))
    address_street: Mapped[Optional[str]] = mapped_column(String(255))
    address_exterior: Mapped[Optional[str]] = mapped_column(String(20))
    address_interior: Mapped[Optional[str]] = mapped_column(String(20))
    address_colony: Mapped[Optional[str]] = mapped_column(String(100))
    address_city: Mapped[Optional[str]] = mapped_column(String(100))
    address_state: Mapped[Optional[str]] = mapped_column(String(100))
    address_postal_code: Mapped[Optional[str]] = mapped_column(String(10))
    address_country: Mapped[str] = mapped_column(String(3), default="MEX")
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    website: Mapped[Optional[str]] = mapped_column(String(255))
    is_issuer: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[EntityStatus] = mapped_column(
        SAEnum(EntityStatus, name="entity_status"),
        default=EntityStatus.ACTIVE,
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    corporate: Mapped["Corporate"] = relationship(back_populates="legal_entities")
    contacts: Mapped[list["Contact"]] = relationship(
        back_populates="legal_entity", cascade="all, delete-orphan"
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="legal_entity", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<LegalEntity {self.legal_name} ({self.rfc})>"


# ─── Contact ─────────────────────────────────────────────────────────────────
class Contact(Base):
    """
    Persona de contacto asociada a una razón social (cliente/proveedor).
    Separado de LegalEntity para manejar múltiples contactos por empresa.
    """
    __tablename__ = "contacts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    legal_entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("legal_entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    position: Mapped[Optional[str]] = mapped_column(String(150))
    department: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    phone_ext: Mapped[Optional[str]] = mapped_column(String(10))
    mobile: Mapped[Optional[str]] = mapped_column(String(20))
    contact_type: Mapped[ContactType] = mapped_column(
        SAEnum(ContactType, name="contact_type"), default=ContactType.CLIENT, nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_billing: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    legal_entity: Mapped["LegalEntity"] = relationship(back_populates="contacts")
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="contact")

    def __repr__(self) -> str:
        return f"<Contact {self.first_name} {self.last_name}>"


# ─── Invoice (Factura) ───────────────────────────────────────────────────────
class Invoice(Base):
    """
    Factura emitida por una razón social.
    """
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    legal_entity_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("legal_entities.id", ondelete="CASCADE"), nullable=True, index=True
    )
    contact_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    
    # Datos de la factura
    invoice_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    issue_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Montos
    subtotal: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), default=0.0)
    tax_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), default=0.0)
    total: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), default=0.0)
    
    # Moneda
    currency: Mapped[str] = mapped_column(String(3), default="MXN", nullable=False)
    
    # Estado
    status: Mapped[InvoiceStatus] = mapped_column(
        SAEnum(InvoiceStatus, name="invoice_status"),
        default=InvoiceStatus.PENDING,
        nullable=False,
    )
    
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relations
    legal_entity: Mapped["LegalEntity"] = relationship(back_populates="invoices")
    contact: Mapped[Optional["Contact"]] = relationship(back_populates="invoices")
    payments: Mapped[list["InvoicePayment"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number}>"


# ─── Invoice Payment (Pago de Factura) ───────────────────────────────────────
class InvoicePayment(Base):
    """
    Pago recibido contra una factura.
    Soporta moneda cruzada (pago en diferente moneda a la factura).
    """
    __tablename__ = "invoice_payments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    invoice_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # Datos del pago
    payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        SAEnum(PaymentMethod, name="payment_method"),
        default=PaymentMethod.TRANSFER,
        nullable=False,
    )
    reference: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Campos de moneda cruzada
    invoice_currency: Mapped[str] = mapped_column(String(3), default="MXN", nullable=False)
    payment_currency: Mapped[str] = mapped_column(String(3), default="MXN", nullable=False)
    exchange_rate: Mapped[Optional[float]] = mapped_column(Numeric(15, 6), default=1.0)
    amount_in_invoice_currency: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    
    # Quién registró el pago
    recorded_by_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relations
    invoice: Mapped["Invoice"] = relationship(back_populates="payments")
    recorded_by: Mapped[Optional["User"]] = relationship()

    def __repr__(self) -> str:
        return f"<InvoicePayment {self.amount} {self.payment_currency}>"