"""
Job de alertas (app/services/alertas_job.py) — el pedazo nuevo de la Fase 4.
GET /alertas ya marcaba facturas vencidas como efecto secundario, pero nunca
marcaba cotizaciones expiradas; este job sí lo hace, y corre solo (scheduler
en app/main.py), no depende de que alguien abra una pantalla.
"""
import email
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app.core.config import settings
from app.models.models import Invoice, InvoiceStatus
from app.models.quote_models import Quote, QuoteStatus
from app.services.alertas_job import check_overdue


def _configure_smtp(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.dreamhost.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USE_TLS", True)
    monkeypatch.setattr(settings, "SMTP_USER", "jlebrija@dacogpo.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "fake-password-for-test")
    monkeypatch.setattr(settings, "SMTP_FROM", "jlebrija@dacogpo.com")
    monkeypatch.setattr(settings, "ALERTAS_EMAIL_TO", "jlebrija@dacogpo.com")


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


async def test_no_email_sent_when_smtp_not_configured(db_session, test_corporate_and_client, monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    monkeypatch.setattr(settings, "ALERTAS_EMAIL_TO", "")

    inv = Invoice(
        client_id=test_corporate_and_client.id,
        folio="F-JOB-NOSMTP",
        issue_date=datetime.now(timezone.utc) - timedelta(days=40),
        due_date=datetime.now(timezone.utc) - timedelta(days=1),
        status=InvoiceStatus.PENDING,
        subtotal=100, iva_amount=16, total=116, paid_amount=0, balance=116,
    )
    db_session.add(inv)
    await db_session.commit()

    with patch("smtplib.SMTP") as mock_smtp:
        await check_overdue(db_session)
    mock_smtp.assert_not_called()


async def test_email_sent_with_overdue_details_when_smtp_configured(db_session, test_corporate_and_client, monkeypatch):
    _configure_smtp(monkeypatch)

    inv = Invoice(
        client_id=test_corporate_and_client.id,
        folio="F-JOB-EMAIL",
        issue_date=datetime.now(timezone.utc) - timedelta(days=40),
        due_date=datetime.now(timezone.utc) - timedelta(days=1),
        status=InvoiceStatus.PENDING,
        subtotal=100, iva_amount=16, total=116, paid_amount=0, balance=116,
    )
    db_session.add(inv)
    await db_session.commit()

    mock_server = MagicMock()
    mock_server.__enter__.return_value = mock_server
    with patch("smtplib.SMTP", return_value=mock_server) as mock_smtp:
        await check_overdue(db_session)

    mock_smtp.assert_called_once_with("smtp.dreamhost.com", 587, timeout=15)
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("jlebrija@dacogpo.com", "fake-password-for-test")

    assert mock_server.sendmail.call_count == 1
    from_addr, to_addrs, raw_message = mock_server.sendmail.call_args[0]
    assert from_addr == "jlebrija@dacogpo.com"
    assert to_addrs == ["jlebrija@dacogpo.com"]

    body = email.message_from_string(raw_message).get_payload(decode=True).decode("utf-8")
    assert "F-JOB-EMAIL" in body
    assert "VENCIDAS" in body
