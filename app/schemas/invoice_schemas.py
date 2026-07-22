"""
DACO — Schemas de Facturas y Pagos
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class InvoiceBase(BaseModel):
    folio: str = Field(min_length=1, max_length=50)
    client_id: str
    issue_date: datetime
    due_date: Optional[datetime] = None
    status: str = "issued"
    currency: str = "MXN"
    exchange_rate: Optional[float] = None
    subtotal: float = 0
    iva_amount: float = 0
    total: float = 0
    notes: Optional[str] = None
    quote_id: Optional[str] = None
    quote_ids: Optional[List[str]] = []


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(BaseModel):
    folio: Optional[str] = None
    issue_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    subtotal: Optional[float] = None
    iva_amount: Optional[float] = None
    total: Optional[float] = None
    paid_amount: Optional[float] = None
    notes: Optional[str] = None
    currency: Optional[str] = None
    exchange_rate: Optional[float] = None
    quote_id: Optional[str] = None
    quote_ids: Optional[List[str]] = None


class InvoiceResponse(InvoiceBase):
    id: str
    paid_amount: float
    balance: float
    pdf_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    client_name: Optional[str] = None
    quote_folio: Optional[str] = None
    quotes_folios: Optional[List[str]] = []
    model_config = {"from_attributes": True}


class InvoiceListResponse(BaseModel):
    items: list[InvoiceResponse]
    total: int
    page: int
    page_size: int
    pages: int


class PaymentCreate(BaseModel):
    amount: float = Field(gt=0)
    reference: Optional[str] = None
    notes: Optional[str] = None
    payment_date: Optional[datetime] = None
    # Pago cross-currency: cuando factura es USD pero el banco acredita MXN
    paid_currency: Optional[str] = None          # 'MXN' si pagaron en pesos
    paid_amount_mxn: Optional[float] = None      # Monto exacto MXN acreditado en banco
    exchange_rate_payment: Optional[float] = None # TC implícito (paid_amount_mxn / amount)