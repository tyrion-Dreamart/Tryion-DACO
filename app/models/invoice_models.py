"""
Modelo de pagos de facturas DACO
Soporta pagos en moneda original (USD/MXN) y registro del monto MXN recibido en banco
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InvoicePayment(Base):
    __tablename__ = "invoice_payments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    invoice_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    payment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Monto en la moneda de la factura (USD si factura USD, MXN si factura MXN)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)

    # Pago cross-currency: factura en USD pero el banco acredita MXN
    paid_currency: Mapped[Optional[str]] = mapped_column(String(3))           # 'MXN' cuando aplica
    paid_amount_mxn: Mapped[Optional[float]] = mapped_column(Numeric(14, 2))  # Exacto lo que entró al banco
    exchange_rate_payment: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))  # TC implícito

    reference: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<InvoicePayment {self.invoice_id} {self.amount}>"