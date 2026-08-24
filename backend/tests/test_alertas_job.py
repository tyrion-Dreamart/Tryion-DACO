"""
Job de alertas (app/services/alertas_job.py) — el pedazo nuevo de la Fase 4.
GET /alertas ya marcaba facturas vencidas como efecto secundario, pero nunca
marcaba cotizaciones expiradas; este job sí lo hace, y corre solo (scheduler
en app/main.py), no depende de que alguien abra una pantalla.
"""
from datetime import datetime, timedelta, timezone

from app.models.models import Invoice, InvoiceStatus
from app.models.quote_models import Quote, QuoteStatus
from app.services.alertas_job import check_overdue


async def test_check_overdue_marks_late_invoice(db_session, test_corporate_and_client):
    inv = Invoice(
        client_id=test_corporate_and_client.id,
        folio="F-JOB-1",
        issue_date=datetime.now(timezone.utc) - timedelta(days=40),
        due_date=datetime.now(timezone.utc) - timedelta(days=1),
        status=InvoiceStatus.PENDING,
        subtotal=100, iva_amount=16, total=116, paid_amount=0, balance=116,
    )
    db_session.add(inv)
    await db_session.commit()

    result = await check_overdue(db_session)
    assert result["invoices_overdue"] == 1

    await db_session.refresh(inv)
    assert inv.status == InvoiceStatus.OVERDUE


async def test_check_overdue_leaves_current_invoice_alone(db_session, test_corporate_and_client):
    inv = Invoice(
        client_id=test_corporate_and_client.id,
        folio="F-JOB-2",
        issue_date=datetime.now(timezone.utc),
        due_date=datetime.now(timezone.utc) + timedelta(days=10),
        status=InvoiceStatus.PENDING,
        subtotal=100, iva_amount=16, total=116, paid_amount=0, balance=116,
    )
    db_session.add(inv)
    await db_session.commit()

    result = await check_overdue(db_session)
    assert result["invoices_overdue"] == 0

    await db_session.refresh(inv)
    assert inv.status == InvoiceStatus.PENDING


async def test_check_overdue_marks_expired_quote(db_session, test_corporate_and_client):
    quote = Quote(
        client_id=test_corporate_and_client.id,
        folio="COT-JOB-1",
        issue_date=datetime.now(timezone.utc) - timedelta(days=20),
        expiry_date=datetime.now(timezone.utc) - timedelta(days=2),
        status=QuoteStatus.SENT,
        subtotal=0, iva_amount=0, total=0,
    )
    db_session.add(quote)
    await db_session.commit()

    result = await check_overdue(db_session)
    assert result["quotes_expired"] == 1

    await db_session.refresh(quote)
    assert quote.status == QuoteStatus.EXPIRED


async def test_check_overdue_ignores_already_paid_invoice(db_session, test_corporate_and_client):
    inv = Invoice(
        client_id=test_corporate_and_client.id,
        folio="F-JOB-3",
        issue_date=datetime.now(timezone.utc) - timedelta(days=40),
        due_date=datetime.now(timezone.utc) - timedelta(days=1),
        status=InvoiceStatus.PAID,
        subtotal=100, iva_amount=16, total=116, paid_amount=116, balance=0,
    )
    db_session.add(inv)
    await db_session.commit()

    result = await check_overdue(db_session)
    assert result["invoices_overdue"] == 0

    await db_session.refresh(inv)
    assert inv.status == InvoiceStatus.PAID
