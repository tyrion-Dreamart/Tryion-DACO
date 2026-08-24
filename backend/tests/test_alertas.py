"""
GET /alertas y GET /reportes/antiguedad-saldos estaban rotos: filtraban por
InvoiceStatus.ISSUED / InvoiceStatus.PARTIAL, valores que ya no existen en el
enum (quedó PENDING / PARTIALLY_PAID) — cualquier llamada tiraba 500.
"""
from datetime import datetime, timedelta, timezone

from app.models.models import Invoice, InvoiceStatus


async def _make_invoice(db_session, client_id, *, due_in_days, folio):
    inv = Invoice(
        client_id=client_id,
        folio=folio,
        issue_date=datetime.now(timezone.utc) - timedelta(days=30),
        due_date=datetime.now(timezone.utc) + timedelta(days=due_in_days),
        status=InvoiceStatus.PENDING,
        subtotal=1000,
        iva_amount=160,
        total=1160,
        paid_amount=0,
        balance=1160,
    )
    db_session.add(inv)
    await db_session.commit()
    await db_session.refresh(inv)
    return inv


async def test_alertas_does_not_crash_and_flags_overdue_invoice(client, auth_headers, db_session, test_corporate_and_client):
    overdue = await _make_invoice(db_session, test_corporate_and_client.id, due_in_days=-5, folio="F-OVERDUE")
    await _make_invoice(db_session, test_corporate_and_client.id, due_in_days=30, folio="F-FINE")

    resp = await client.get("/api/v1/alertas", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    ids = {a["entity_id"] for a in body["items"]}
    assert overdue.id in ids
    assert body["high"] >= 1

    await db_session.refresh(overdue)
    assert overdue.status == InvoiceStatus.OVERDUE


async def test_antiguedad_saldos_does_not_crash(client, auth_headers, db_session, test_corporate_and_client):
    await _make_invoice(db_session, test_corporate_and_client.id, due_in_days=-10, folio="F-AGED")

    resp = await client.get("/api/v1/reportes/antiguedad-saldos", headers=auth_headers)
    assert resp.status_code == 200, resp.text
