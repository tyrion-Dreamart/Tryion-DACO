from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Quote Item ────────────────────────────────────────────────────────────────
class QuoteItemBase(BaseModel):
    concept: str = Field(min_length=1)
    dimensions: Optional[str] = None
    quantity: float = Field(default=1, gt=0)
    unit_price: float = Field(default=0, ge=0)
    sort_order: int = 0

class QuoteItemCreate(QuoteItemBase):
    pass

class QuoteItemUpdate(BaseModel):
    concept: Optional[str] = None
    dimensions: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    sort_order: Optional[int] = None

class QuoteItemResponse(QuoteItemBase):
    id: str
    quote_id: str
    total: float
    model_config = {"from_attributes": True}


# ── Quote ─────────────────────────────────────────────────────────────────────
class QuoteBase(BaseModel):
    folio: str = Field(min_length=1, max_length=50)
    client_id: str
    attention_name: Optional[str] = None
    attention_area: Optional[str] = None
    issue_date: datetime
    expiry_date: Optional[datetime] = None
    status: str = "draft"
    currency: str = "MXN"
    has_iva: bool = True
    iva_rate: float = 16.0
    advance_pct: Optional[float] = None
    notes: Optional[str] = None

class QuoteCreate(QuoteBase):
    items: list[QuoteItemCreate] = []

class QuoteUpdate(BaseModel):
    folio: Optional[str] = None
    attention_name: Optional[str] = None
    attention_area: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    status: Optional[str] = None
    currency: Optional[str] = None
    has_iva: Optional[bool] = None
    iva_rate: Optional[float] = None
    advance_pct: Optional[float] = None
    notes: Optional[str] = None
    items: Optional[list[QuoteItemCreate]] = None

class QuoteResponse(QuoteBase):
    id: str
    subtotal: float
    iva_amount: float
    total: float
    pdf_url: Optional[str] = None
    extracted_by_ai: bool
    exchange_rate: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    items: list[QuoteItemResponse] = []
    client_name: Optional[str] = None
    model_config = {"from_attributes": True}

class QuoteListResponse(BaseModel):
    items: list[QuoteResponse]
    total: int
    page: int
    page_size: int
    pages: int

class QuoteStats(BaseModel):
    draft: int = 0
    sent: int = 0
    approved: int = 0
    rejected: int = 0
    expired: int = 0
    pipeline: float = 0

# ── AI Extraction ─────────────────────────────────────────────────────────────
class ExtractedQuoteItem(BaseModel):
    concept: str = ""
    dimensions: Optional[str] = None
    quantity: Optional[float] = 1
    unit_price: Optional[float] = 0
    total: Optional[float] = 0

class ExtractedQuote(BaseModel):
    folio: Optional[str] = None
    attention_name: Optional[str] = None
    attention_area: Optional[str] = None
    issue_date: Optional[str] = None
    client_name: Optional[str] = None
    items: list[ExtractedQuoteItem] = []
    subtotal: Optional[float] = 0
    notes: Optional[str] = None
    advance_pct: Optional[float] = None
    exchange_rate: Optional[float] = None
    currency: Optional[str] = "MXN"