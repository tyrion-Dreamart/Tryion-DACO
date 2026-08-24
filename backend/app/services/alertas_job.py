"""
Job programado de alertas: marca facturas vencidas y cotizaciones expiradas
de forma proactiva, sin depender de que alguien abra la pantalla de alertas.

Antes esto solo pasaba como efecto secundario de GET /alertas (ver
app/api/v1/endpoints/alertas.py) — si nadie entraba a esa pantalla, una
factura vencida se quedaba con status PENDING indefinidamente, y no salía
correcta en el dashboard, reportes, etc.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Invoice, InvoiceStatus
from app.models.quote_models import Quote, QuoteStatus

logger = logging.getLogger("daco.alertas_job")


async def check_overdue(db: AsyncSession) -> dict:
    """Revisa facturas y cotizaciones activas y actualiza su estado si ya vencieron."""
    now = datetime.now(timezone.utc)

    inv_result = await db.execute(
        select(Invoice).where(Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.PARTIALLY_PAID]))
    )
    invoices_overdue = 0
    for inv in inv_result.scalars().all():
        if inv.due_date and inv.due_date.replace(tzinfo=timezone.utc) < now:
            inv.status = InvoiceStatus.OVERDUE
            invoices_overdue += 1

    quote_result = await db.execute(
        select(Quote).where(Quote.status.in_([QuoteStatus.DRAFT, QuoteStatus.SENT]))
    )
    quotes_expired = 0
    for quote in quote_result.scalars().all():
        if quote.expiry_date and quote.expiry_date.replace(tzinfo=timezone.utc) < now:
            quote.status = QuoteStatus.EXPIRED
            quotes_expired += 1

    await db.commit()

    result = {"invoices_overdue": invoices_overdue, "quotes_expired": quotes_expired}
    logger.info("alertas_job: %s", result)
    return result


async def run_alertas_job() -> None:
    """Wrapper sin dependencias de FastAPI — abre su propia sesión para correr fuera de un request."""
    from app.db.base import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            await check_overdue(db)
        except Exception:
            logger.exception("alertas_job falló")
