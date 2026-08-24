"""
Facturas DACO — usando el modelo Invoice de models.py
Con historial de pagos, soporte USD/MXN y múltiples cotizaciones
"""
import math
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select, insert, delete

from app.core.deps import CurrentUser, DBDep
from app.models.models import Invoice, InvoiceStatus, InvoicePayment, LegalEntity, invoice_quotes
from app.models.quote_models import Quote
from app.schemas.invoice_schemas import (
    InvoiceCreate,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceUpdate,
    PaymentCreate,
)

router = APIRouter(prefix="/invoices", tags=["Facturas"])


# Mapeo de estados del frontend a los del modelo actual
STATUS_MAP = {
    "issued": InvoiceStatus.PENDING,
    "partial": InvoiceStatus.PARTIALLY_PAID,
    "paid": InvoiceStatus.PAID,
    "overdue": InvoiceStatus.OVERDUE,
    "cancelled": InvoiceStatus.CANCELLED,
}

STATUS_REVERSE_MAP = {
    InvoiceStatus.PENDING: "issued",
    InvoiceStatus.PARTIALLY_PAID: "partial",
    InvoiceStatus.PAID: "paid",
    InvoiceStatus.OVERDUE: "overdue",
    InvoiceStatus.CANCELLED: "cancelled",
}


async def _get_quotes_for_invoice(db, invoice_id: str) -> list:
    result = await db.execute(
        select(Quote).join(invoice_quotes, Quote.id == invoice_quotes.c.quote_id)
        .where(invoice_quotes.c.invoice_id == invoice_id)
    )
    return result.scalars().all()


async def _load_invoice_quotes(db, invoice_id: str):
    quotes = await _get_quotes_for_invoice(db, invoice_id)
    ids = [q.id for q in quotes]
    folios = [q.folio for q in quotes]
    first_folio = folios[0] if folios else None
    return ids, folios, first_folio


async def _sync_quote_ids(db, invoice_id: str, quote_ids: list):
    await db.execute(
        delete(invoice_quotes).where(invoice_quotes.c.invoice_id == invoice_id)
    )
    for qid in quote_ids:
        q = await db.execute(select(Quote).where(Quote.id == qid))
        if q.scalar_one_or_none():
            await db.execute(
                insert(invoice_quotes).values(invoice_id=invoice_id, quote_id=qid)
            )


def _build_response(inv: Invoice, client_name: str = None, quote_folio: str = None, quotes_folios: list = None, quote_ids: list = None) -> InvoiceResponse:
    status_str = STATUS_REVERSE_MAP.get(inv.status, str(inv.status).lower())
    return InvoiceResponse(
        id=inv.id,
        folio=inv.folio or inv.invoice_number or "",
        client_id=inv.client_id or "",
        quote_id=None,
        quote_ids=quote_ids or [],
        issue_date=inv.issue_date,
        due_date=inv.due_date,
        status=status_str,
        currency=inv.currency,
        exchange_rate=float(inv.exchange_rate) if inv.exchange_rate else None,
        subtotal=float(inv.subtotal or 0),
        iva_amount=float(inv.iva_amount or 0),
        total=float(inv.total or 0),
        paid_amount=float(inv.paid_amount or 0),
        balance=float(inv.balance or 0),
        notes=inv.notes,
        pdf_url=inv.pdf_url,
        created_at=inv.created_at,
        updated_at=inv.updated_at or datetime.now(timezone.utc),
        client_name=client_name,
        quote_folio=quote_folio,
        quotes_folios=quotes_folios or [],
    )


# ── List ──────────────────────────────────────────────────────────────────────
@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    db: DBDep,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    client_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
):
    query = select(Invoice)
    if search:
        query = query.where(
            Invoice.folio.ilike(f"%{search}%") | Invoice.invoice_number.ilike(f"%{search}%")
        )
    if client_id:
        query = query.where(Invoice.client_id == client_id)
    if status:
        mapped = STATUS_MAP.get(status)
        if mapped:
            query = query.where(Invoice.status == mapped)

    count_r = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_r.scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.offset(offset).limit(page_size).order_by(Invoice.issue_date.desc())
    )
    invoices = result.scalars().all()

    items = []
    for inv in invoices:
        client_name = None
        if inv.client_id:
            c = await db.execute(select(LegalEntity).where(LegalEntity.id == inv.client_id))
            cl = c.scalar_one_or_none()
            if cl:
                client_name = cl.legal_name
        ids, folios, first_folio = await _load_invoice_quotes(db, inv.id)
        items.append(_build_response(inv, client_name, first_folio, folios, ids))

    return InvoiceListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


# ── Create ────────────────────────────────────────────────────────────────────
@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(payload: InvoiceCreate, db: DBDep, current_user: CurrentUser):
    c = await db.execute(select(LegalEntity).where(LegalEntity.id == payload.client_id))
    if not c.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Verificar folio duplicado
    existing = await db.execute(select(Invoice).where(Invoice.folio == payload.folio))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Folio {payload.folio} ya existe")

    mapped_status = STATUS_MAP.get(payload.status, InvoiceStatus.PENDING)

    inv = Invoice(
        folio=payload.folio,
        invoice_number=payload.folio,
        client_id=payload.client_id,
        issue_date=payload.issue_date,
        due_date=payload.due_date,
        status=mapped_status,
        currency=payload.currency,
        exchange_rate=payload.exchange_rate,
        subtotal=payload.subtotal,
        iva_amount=payload.iva_amount,
        tax_amount=payload.iva_amount,
        total=payload.total,
        paid_amount=0,
        balance=payload.total,
        notes=payload.notes,
    )
    db.add(inv)
    await db.flush()

    all_quote_ids = list(set((payload.quote_ids or []) + ([payload.quote_id] if payload.quote_id else [])))
    if all_quote_ids:
        await _sync_quote_ids(db, inv.id, all_quote_ids)

    await db.flush()

    cl = await db.execute(select(LegalEntity).where(LegalEntity.id == inv.client_id))
    client = cl.scalar_one_or_none()
    ids, folios, first_folio = await _load_invoice_quotes(db, inv.id)
    return _build_response(inv, client.trade_name or client.legal_name if client else None, first_folio, folios, ids)


# ── Get ───────────────────────────────────────────────────────────────────────
@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str, db: DBDep, current_user: CurrentUser):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    client_name = None
    if inv.client_id:
        c = await db.execute(select(LegalEntity).where(LegalEntity.id == inv.client_id))
        cl = c.scalar_one_or_none()
        if cl:
            client_name = cl.legal_name
    ids, folios, first_folio = await _load_invoice_quotes(db, inv.id)
    return _build_response(inv, client_name, first_folio, folios, ids)


# ── Update ────────────────────────────────────────────────────────────────────
@router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(invoice_id: str, payload: InvoiceUpdate, db: DBDep, current_user: CurrentUser):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    update_data = payload.model_dump(exclude_unset=True)
    quote_ids = update_data.pop("quote_ids", None)

    # Mapear campos del payload al modelo
    field_map = {
        "folio": "folio",
        "client_id": "client_id",
        "issue_date": "issue_date",
        "due_date": "due_date",
        "subtotal": "subtotal",
        "iva_amount": "iva_amount",
        "total": "total",
        "paid_amount": "paid_amount",
        "notes": "notes",
        "currency": "currency",
        "exchange_rate": "exchange_rate",
    }

    for field, value in update_data.items():
        if field == "status":
            setattr(inv, "status", STATUS_MAP.get(value, InvoiceStatus.PENDING))
        elif field in field_map:
            setattr(inv, field_map[field], value)

    # Actualizar cotizaciones vinculadas
    if quote_ids is not None:
        await _sync_quote_ids(db, invoice_id, quote_ids)
        if quote_ids:
            inv.invoice_number = inv.folio

    # Recalcular balance y estado
    inv.balance = float(inv.total or 0) - float(inv.paid_amount or 0)
    if inv.balance <= 0:
        inv.status = InvoiceStatus.PAID
    elif float(inv.paid_amount or 0) > 0:
        inv.status = InvoiceStatus.PARTIALLY_PAID

    await db.flush()

    # Recargar el objeto de la BD para evitar lazy loading
    await db.refresh(inv)

    client_name = None
    if inv.client_id:
        c = await db.execute(select(LegalEntity).where(LegalEntity.id == inv.client_id))
        cl = c.scalar_one_or_none()
        if cl:
            client_name = cl.legal_name
    ids, folios, first_folio = await _load_invoice_quotes(db, inv.id)
    return _build_response(inv, client_name, first_folio, folios, ids)


# ── Register payment ──────────────────────────────────────────────────────────
@router.post("/{invoice_id}/payment", response_model=InvoiceResponse)
async def register_payment(invoice_id: str, payload: PaymentCreate, db: DBDep, current_user: CurrentUser):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    from app.models.models import PaymentMethod
    payment = InvoicePayment(
        invoice_id=invoice_id,
        payment_date=payload.payment_date or datetime.now(timezone.utc),
        amount=payload.amount,
        payment_method=PaymentMethod.TRANSFER,
        reference=payload.reference,
        notes=payload.notes,
        invoice_currency=inv.currency,
        payment_currency=inv.currency,
        exchange_rate=inv.exchange_rate or 1,
        amount_in_invoice_currency=payload.amount,
    )
    db.add(payment)

    inv.paid_amount = float(inv.paid_amount or 0) + payload.amount
    inv.balance = float(inv.total or 0) - float(inv.paid_amount)

    if inv.balance <= 0:
        inv.balance = 0
        inv.status = InvoiceStatus.PAID
    else:
        inv.status = InvoiceStatus.PARTIALLY_PAID

    await db.flush()
    await db.refresh(inv)

    client_name = None
    if inv.client_id:
        c = await db.execute(select(LegalEntity).where(LegalEntity.id == inv.client_id))
        cl = c.scalar_one_or_none()
        if cl:
            client_name = cl.legal_name
    ids, folios, first_folio = await _load_invoice_quotes(db, inv.id)
    return _build_response(inv, client_name, first_folio, folios, ids)


# ── Get payment history ───────────────────────────────────────────────────────
@router.get("/{invoice_id}/payments")
async def get_payments(invoice_id: str, db: DBDep, current_user: CurrentUser):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    payments_r = await db.execute(
        select(InvoicePayment)
        .where(InvoicePayment.invoice_id == invoice_id)
        .order_by(InvoicePayment.payment_date.asc())
    )
    payments = payments_r.scalars().all()

    return {
        "items": [
            {
                "id": p.id,
                "payment_date": p.payment_date.isoformat(),
                "amount": float(p.amount),
                "reference": p.reference,
                "notes": p.notes,
                "created_at": p.created_at.isoformat(),
            }
            for p in payments
        ],
        "total": len(payments),
    }


# ── Delete ────────────────────────────────────────────────────────────────────
@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(invoice_id: str, db: DBDep, current_user: CurrentUser):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    await db.delete(inv)


# ── Delete payment ────────────────────────────────────────────────────────────
@router.delete("/{invoice_id}/payments/{payment_id}", response_model=InvoiceResponse)
async def delete_payment(invoice_id: str, payment_id: str, db: DBDep, current_user: CurrentUser):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    pay_r = await db.execute(
        select(InvoicePayment).where(
            InvoicePayment.id == payment_id,
            InvoicePayment.invoice_id == invoice_id
        )
    )
    payment = pay_r.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    inv.paid_amount = float(inv.paid_amount or 0) - float(payment.amount)
    inv.balance = float(inv.total or 0) - float(inv.paid_amount)

    if inv.paid_amount <= 0:
        inv.paid_amount = 0
        inv.balance = float(inv.total or 0)
        inv.status = InvoiceStatus.PENDING
    elif inv.balance <= 0:
        inv.status = InvoiceStatus.PAID
    else:
        inv.status = InvoiceStatus.PARTIALLY_PAID

    await db.delete(payment)
    await db.flush()

    client_name = None
    if inv.client_id:
        c = await db.execute(select(LegalEntity).where(LegalEntity.id == inv.client_id))
        cl = c.scalar_one_or_none()
        if cl:
            client_name = cl.legal_name
    ids, folios, first_folio = await _load_invoice_quotes(db, inv.id)
    return _build_response(inv, client_name, first_folio, folios, ids)