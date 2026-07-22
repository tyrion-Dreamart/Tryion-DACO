"""
Módulo de Cotizaciones DACO
Quote → QuoteItem (líneas)
"""
from __future__ import annotations
import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, Numeric,
    String, Text, func, Enum as SAEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class QuoteStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    INVOICED = "invoiced"


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    folio: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    client_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("legal_entities.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    attention_name: Mapped[Optional[str]] = mapped_column(String(255))   # At'n.
    attention_area: Mapped[Optional[str]] = mapped_column(String(100))   # Dirección, Compras
    issue_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[QuoteStatus] = mapped_column(
        SAEnum(QuoteStatus, name="quote_status"),
        default=QuoteStatus.DRAFT,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(3), default="MXN")
    has_iva: Mapped[bool] = mapped_column(Boolean, default=True)
    iva_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=16.0)
    subtotal: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    iva_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    advance_pct: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))  # % anticipo
    exchange_rate: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500))          # PDF subido
    extracted_by_ai: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    items: Mapped[list["QuoteItem"]] = relationship(
        back_populates="quote", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Quote {self.folio}>"


class QuoteItem(Base):
    __tablename__ = "quote_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    quote_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    concept: Mapped[str] = mapped_column(Text, nullable=False)
    dimensions: Mapped[Optional[str]] = mapped_column(Text)   # Medidas (texto libre)
    quantity: Mapped[float] = mapped_column(Numeric(10, 2), default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(14, 2), default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    quote: Mapped["Quote"] = relationship(back_populates="items")
