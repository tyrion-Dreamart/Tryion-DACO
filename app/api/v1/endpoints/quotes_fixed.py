"""
Cotizaciones DACO
- CRUD completo
- Extracción de datos desde PDF con IA (Claude API)
"""
import base64
import json
import math
import os
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, status
from sqlalchemy import func, select

from app.core.deps import CurrentUser, DBDep
from app.models.quote_models import Quote, QuoteItem, QuoteStatus
from app.models.models import LegalEntity
from app.schemas.quote_schemas import (
    ExtractedQuote,
    QuoteCreate,
    QuoteListResponse,
    QuoteResponse,
    QuoteStats,
    QuoteUpdate,
)

router = APIRouter(prefix="/quotes", tags=["Cotizaciones"])


def _calc_totals(quote: Quote) -> None:
    subtotal = sum(float(item.total) for item in quote.items)
    iva = subtotal * (float(quote.iva_rate) / 100) if quote.has_iva else 0
    quote.subtotal = subtotal
    quote.iva_amount = round(iva, 2)
    quote.total = round(subtotal + iva, 2)


def _calc_item_total(item: QuoteItem) -> None:
    item.total = round(float(item.quantity) * float(item.unit_price), 2)


# ── List ──────────────────────────────────────────────────────────────────────
@router.get("", response_model=QuoteListResponse)
async def list_quotes(
    db: DBDep,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    client_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
):
    query = select(Quote)
    if search:
        query = query.where(Quote.folio.ilike(f"%{search}%"))
    if client_id:
        query = query.where(Quote.client_id == client_id)
    if status:
        query = query.where(Quote.status == status)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.offset(offset).limit(page_size).order_by(Quote.created_at.desc())
    )
    quotes = result.scalars().all()

    items = []
    for q in quotes:
        resp = QuoteResponse.model_validate(q)
        client = await db.execute(select(LegalEntity).where(LegalEntity.id == q.client_id))
        c = client.scalar_one_or_none()
        if c:
            resp.client_name = c.trade_name or c.legal_name
        items.append(resp)

    return QuoteListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


# ── Stats for dashboard ───────────────────────────────────────────────────────
@router.get("/stats", response_model=QuoteStats)
async def get_stats(db: DBDep, current_user: CurrentUser):
    stats = QuoteStats()
    for s in QuoteStatus:
        result = await db.execute(
            select(func.count(Quote.id)).where(Quote.status == s)
        )
        count = result.scalar_one()
        setattr(stats, s.value, count)

    pipeline_result = await db.execute(
        select(func.sum(Quote.total)).where(
            Quote.status.in_([QuoteStatus.DRAFT, QuoteStatus.SENT])
        )
    )
    stats.pipeline = float(pipeline_result.scalar_one() or 0)
    return stats


# ── AI Extract from PDF ───────────────────────────────────────────────────────
@router.post("/extract", response_model=ExtractedQuote)
async def extract_from_pdf(
    current_user: CurrentUser,
    file: UploadFile = File(...),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El archivo no debe superar 10MB")

    b64 = base64.standard_b64encode(content).decode("utf-8")

    prompt = """Eres un experto extrayendo datos de cotizaciones comerciales mexicanas. Analiza CUIDADOSAMENTE esta cotización y extrae TODOS los datos.

INSTRUCCIONES IMPORTANTES:
1. El folio aparece como "No de Cotización" o "No. de Cotización" — extráelo EXACTAMENTE como aparece (ej: DK-001, NNNM-005)
2. La persona en "At'n." es el contacto — extrae solo el nombre sin títulos (Lic., Ing., etc.)
3. El área/departamento aparece debajo del nombre (Dirección, Compras, etc.)
4. Para los items/conceptos: busca la TABLA de productos. Cada fila es un item separado.
   - "Concepto" o descripción del producto: cópiala COMPLETA tal como aparece
   - "Medidas" o dimensiones: extráelas como texto (ej: "Diámetro Interior 0.25 cms, Diámetro total 0.36 cms")
   - "Cantidad": el número de piezas/unidades
   - "P.U" o precio unitario: el precio POR UNIDAD (NO el total)
   - "Total": cantidad × precio unitario
5. En "notes" incluye TODAS las condiciones: tiempo de entrega, anticipo requerido, condiciones de pago, notas especiales
6. "advance_pct": si dice "70% de anticipo" pon 70, si no hay anticipo pon null
7. La fecha puede aparecer como "Martes 12 de Mayo 2026" — conviértela a YYYY-MM-DD

Devuelve SOLO un JSON válido sin texto adicional, sin markdown, sin explicaciones:
{
  "folio": "número exacto de cotización",
  "attention_name": "nombre sin títulos",
  "attention_area": "área o departamento",
  "issue_date": "YYYY-MM-DD",
  "client_name": "nombre del cliente",
  "items": [
    {
      "concept": "descripción COMPLETA del producto",
      "dimensions": "medidas como texto o null",
      "quantity": 66,
      "unit_price": 5000.00,
      "total": 330000.00
    }
  ],
  "subtotal": 330000.00,
  "notes": "todas las notas y condiciones comerciales",
  "advance_pct": 70,
  "currency": "MXN"
}"""

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key no configurada")

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 2000,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "document",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "application/pdf",
                                        "data": b64,
                                    },
                                },
                                {"type": "text", "text": prompt},
                            ],
                        }
                    ],
                },
            )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Error IA: {response.text}")

        data = response.json()
        text = data["content"][0]["text"].strip()

        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        extracted = json.loads(text)
        return ExtractedQuote(**extracted)

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="No se pudo parsear la respuesta de IA")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ── Create ────────────────────────────────────────────────────────────────────
@router.post("", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(payload: QuoteCreate, db: DBDep, current_user: CurrentUser):
    client = await db.execute(select(LegalEntity).where(LegalEntity.id == payload.client_id))
    if not client.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    existing = await db.execute(select(Quote).where(Quote.folio == payload.folio))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"El folio {payload.folio} ya existe")

    quote = Quote(
        folio=payload.folio,
        client_id=payload.client_id,
        attention_name=payload.attention_name,
        attention_area=payload.attention_area,
        issue_date=payload.issue_date,
        expiry_date=payload.expiry_date,
        status=payload.status,
        currency=payload.currency,
        has_iva=payload.has_iva,
        iva_rate=payload.iva_rate,
        advance_pct=payload.advance_pct,
        notes=payload.notes,
        extracted_by_ai=False,
    )
    db.add(quote)
    await db.flush()

    for i, item_data in enumerate(payload.items):
        item = QuoteItem(
            quote_id=quote.id,
            concept=item_data.concept,
            dimensions=item_data.dimensions,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            sort_order=i,
        )
        _calc_item_total(item)
        db.add(item)

    await db.flush()

    result = await db.execute(select(QuoteItem).where(QuoteItem.quote_id == quote.id))
    quote.items = list(result.scalars().all())
    _calc_totals(quote)
    await db.flush()
    await db.refresh(quote)

    resp = QuoteResponse.model_validate(quote)
    c = await db.execute(select(LegalEntity).where(LegalEntity.id == quote.client_id))
    cl = c.scalar_one_or_none()
    if cl:
        resp.client_name = cl.trade_name or cl.legal_name
    return resp


# ── Get ───────────────────────────────────────────────────────────────────────
@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote(quote_id: str, db: DBDep, current_user: CurrentUser):
    result = await db.execute(select(Quote).where(Quote.id == quote_id))
    quote = result.scalar_one_or_none()
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    items_result = await db.execute(
        select(QuoteItem).where(QuoteItem.quote_id == quote_id).order_by(QuoteItem.sort_order)
    )
    quote.items = list(items_result.scalars().all())

    resp = QuoteResponse.model_validate(quote)
    c = await db.execute(select(LegalEntity).where(LegalEntity.id == quote.client_id))
    cl = c.scalar_one_or_none()
    if cl:
        resp.client_name = cl.trade_name or cl.legal_name
    return resp


# ── Update ────────────────────────────────────────────────────────────────────
@router.patch("/{quote_id}", response_model=QuoteResponse)
async def update_quote(
    quote_id: str, payload: QuoteUpdate, db: DBDep, current_user: CurrentUser
):
    result = await db.execute(select(Quote).where(Quote.id == quote_id))
    quote = result.scalar_one_or_none()
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    for field, value in payload.model_dump(exclude_unset=True, exclude={"items"}).items():
        setattr(quote, field, value)

    if payload.items is not None:
        existing = await db.execute(select(QuoteItem).where(QuoteItem.quote_id == quote_id))
        for item in existing.scalars().all():
            await db.delete(item)
        await db.flush()

        for i, item_data in enumerate(payload.items):
            item = QuoteItem(
                quote_id=quote.id,
                concept=item_data.concept,
                dimensions=item_data.dimensions,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                sort_order=i,
            )
            _calc_item_total(item)
            db.add(item)
        await db.flush()

    items_result = await db.execute(
        select(QuoteItem).where(QuoteItem.quote_id == quote_id)
    )
    quote.items = list(items_result.scalars().all())
    _calc_totals(quote)
    await db.flush()
    await db.refresh(quote)

    resp = QuoteResponse.model_validate(quote)
    c = await db.execute(select(LegalEntity).where(LegalEntity.id == quote.client_id))
    cl = c.scalar_one_or_none()
    if cl:
        resp.client_name = cl.trade_name or cl.legal_name
    return resp


# ── Delete ────────────────────────────────────────────────────────────────────
@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote(quote_id: str, db: DBDep, current_user: CurrentUser):
    result = await db.execute(select(Quote).where(Quote.id == quote_id))
    quote = result.scalar_one_or_none()
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    await db.delete(quote)
