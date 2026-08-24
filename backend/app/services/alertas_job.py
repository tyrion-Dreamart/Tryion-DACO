"""
Job programado de alertas: marca facturas vencidas y cotizaciones expiradas
de forma proactiva, sin depender de que alguien abra la pantalla de alertas,
y — si hay SMTP configurado — avisa por correo qué se marcó en esta corrida.

Antes esto solo pasaba como efecto secundario de GET /alertas (ver
app/api/v1/endpoints/alertas.py) — si nadie entraba a esa pantalla, una
factura vencida se quedaba con status PENDING indefinidamente.
"""
import asyncio
import logging
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import Invoice, InvoiceStatus, LegalEntity
from app.models.quote_models import Quote, QuoteStatus

logger = logging.getLogger("daco.alertas_job")


async def check_overdue(db: AsyncSession) -> dict:
    """Revisa facturas y cotizaciones activas, actualiza su estado si ya vencieron
    y (si hay SMTP configurado) manda un correo resumen de lo que se marcó."""
    now = datetime.now(timezone.utc)

    inv_result = await db.execute(
        select(Invoice).where(Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.PARTIALLY_PAID]))
    )
    newly_overdue = []
    for inv in inv_result.scalars().all():
        if inv.due_date and inv.due_date.replace(tzinfo=timezone.utc) < now:
            inv.status = InvoiceStatus.OVERDUE
            newly_overdue.append(inv)

    quote_result = await db.execute(
        select(Quote).where(Quote.status.in_([QuoteStatus.DRAFT, QuoteStatus.SENT]))
    )
    newly_expired = []
    for quote in quote_result.scalars().all():
        if quote.expiry_date and quote.expiry_date.replace(tzinfo=timezone.utc) < now:
            quote.status = QuoteStatus.EXPIRED
            newly_expired.append(quote)

    # nombres de cliente para el correo — hay que leerlos antes del commit
    client_ids = {x.client_id for x in (*newly_overdue, *newly_expired) if x.client_id}
    client_names: dict[str, str] = {}
    if client_ids:
        c_result = await db.execute(select(LegalEntity).where(LegalEntity.id.in_(client_ids)))
        client_names = {c.id: (c.trade_name or c.legal_name) for c in c_result.scalars().all()}

    await db.commit()

    result = {"invoices_overdue": len(newly_overdue), "quotes_expired": len(newly_expired)}
    logger.info("alertas_job: %s", result)

    if newly_overdue or newly_expired:
        await asyncio.to_thread(_send_alert_email, newly_overdue, newly_expired, client_names)

    return result


def _send_alert_email(invoices: list[Invoice], quotes: list[Quote], client_names: dict[str, str]) -> None:
    if not settings.smtp_configured:
        logger.info(
            "alertas_job: SMTP no configurado (ver SMTP_HOST/SMTP_USER/SMTP_PASSWORD/ALERTAS_EMAIL_TO en .env) — "
            "se omite el correo (%d facturas, %d cotizaciones)",
            len(invoices), len(quotes),
        )
        return

    lines = []
    if invoices:
        lines.append("Facturas recién marcadas como VENCIDAS:")
        for inv in invoices:
            client = client_names.get(inv.client_id, "Cliente desconocido")
            lines.append(f"  - {inv.folio} · {client} · ${float(inv.balance or 0):,.2f}")
    if quotes:
        if lines:
            lines.append("")
        lines.append("Cotizaciones recién marcadas como EXPIRADAS:")
        for quote in quotes:
            client = client_names.get(quote.client_id, "Cliente desconocido")
            lines.append(f"  - {quote.folio} · {client} · ${float(quote.total or 0):,.2f}")

    msg = MIMEText("\n".join(lines), "plain", "utf-8")
    msg["Subject"] = f"DACO — {len(invoices)} factura(s) vencida(s), {len(quotes)} cotización(es) expirada(s)"
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = settings.ALERTAS_EMAIL_TO

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(msg["From"], [settings.ALERTAS_EMAIL_TO], msg.as_string())
        logger.info("alertas_job: correo de alertas enviado a %s", settings.ALERTAS_EMAIL_TO)
    except Exception:
        logger.exception("alertas_job: falló el envío del correo de alertas")


async def run_alertas_job() -> None:
    """Wrapper sin dependencias de FastAPI — abre su propia sesión para correr fuera de un request."""
    from app.db.base import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            await check_overdue(db)
        except Exception:
            logger.exception("alertas_job falló")
