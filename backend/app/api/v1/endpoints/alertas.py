"""
Alertas DACO — generadas automáticamente desde facturas y cotizaciones
"""
from datetime import datetime, timezone
from fastapi import APIRouter
from sqlalchemy import select
from app.core.deps import CurrentUser, DBDep
from app.models.models import Invoice, InvoiceStatus
from app.models.quote_models import Quote, QuoteStatus
from app.models.models import LegalEntity

router = APIRouter(prefix="/alertas", tags=["Alertas"])


@router.get("")
async def get_alertas(db: DBDep, current_user: CurrentUser):
    now = datetime.now(timezone.utc)
    alertas = []

    # ── Facturas vencidas ─────────────────────────────────────────────────────
    inv_result = await db.execute(
        select(Invoice).where(
            Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.PARTIALLY_PAID])
        )
    )
    invoices = inv_result.scalars().all()

    for inv in invoices:
        if not inv.due_date:
            continue
        dias = (inv.due_date.replace(tzinfo=timezone.utc) - now).days

        client_name = None
        c = await db.execute(select(LegalEntity).where(LegalEntity.id == inv.client_id))
        cl = c.scalar_one_or_none()
        if cl:
            client_name = cl.trade_name or cl.legal_name

        if dias < 0:
            alertas.append({
                "id": f"inv-overdue-{inv.id}",
                "type": "overdue",
                "priority": "high",
                "title": f"Factura vencida — {inv.folio}",
                "subtitle": f"{client_name} · {format_currency(float(inv.balance))}",
                "label": f"{abs(dias)}d",
                "days": dias,
                "entity_id": inv.id,
                "entity_type": "invoice",
            })
            # Auto-mark as overdue
            inv.status = InvoiceStatus.OVERDUE
        elif dias <= 7:
            alertas.append({
                "id": f"inv-due-soon-{inv.id}",
                "type": "due_soon",
                "priority": "medium",
                "title": f"Factura por vencer — {inv.folio}",
                "subtitle": f"{client_name} · {format_currency(float(inv.balance))}",
                "label": f"{dias}d",
                "days": dias,
                "entity_id": inv.id,
                "entity_type": "invoice",
            })

    # ── Cotizaciones expiradas ────────────────────────────────────────────────
    quote_result = await db.execute(
        select(Quote).where(
            Quote.status.in_([QuoteStatus.DRAFT, QuoteStatus.SENT])
        )
    )
    quotes = quote_result.scalars().all()

    for quote in quotes:
        if not quote.expiry_date:
            continue
        dias = (quote.expiry_date.replace(tzinfo=timezone.utc) - now).days

        client_name = None
        c = await db.execute(select(LegalEntity).where(LegalEntity.id == quote.client_id))
        cl = c.scalar_one_or_none()
        if cl:
            client_name = cl.trade_name or cl.legal_name

        if dias < 0:
            alertas.append({
                "id": f"quote-expired-{quote.id}",
                "type": "expired",
                "priority": "medium",
                "title": f"Cotización expirada — {quote.folio}",
                "subtitle": f"{client_name} · {format_currency(float(quote.total))}",
                "label": "Exp",
                "days": dias,
                "entity_id": quote.id,
                "entity_type": "quote",
            })
        elif dias <= 3:
            alertas.append({
                "id": f"quote-expiring-{quote.id}",
                "type": "expiring",
                "priority": "low",
                "title": f"Cotización por expirar — {quote.folio}",
                "subtitle": f"{client_name} · {format_currency(float(quote.total))}",
                "label": f"{dias}d",
                "days": dias,
                "entity_id": quote.id,
                "entity_type": "quote",
            })

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    alertas.sort(key=lambda x: (priority_order.get(x["priority"], 3), x["days"]))

    await db.flush()

    return {
        "items": alertas,
        "total": len(alertas),
        "high": sum(1 for a in alertas if a["priority"] == "high"),
        "medium": sum(1 for a in alertas if a["priority"] == "medium"),
        "low": sum(1 for a in alertas if a["priority"] == "low"),
    }


def format_currency(amount: float) -> str:
    return f"${amount:,.2f}"
