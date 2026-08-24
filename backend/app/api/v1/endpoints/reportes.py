"""
Reportes DACO
1. Estado de cuenta por cliente
2. Resumen ejecutivo por período
3. Antigüedad de saldos
4. Pipeline de cotizaciones
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Query
from sqlalchemy import select, func
from app.core.deps import CurrentUser, DBDep
from app.models.models import Invoice, InvoiceStatus
from app.models.quote_models import Quote, QuoteStatus
from app.models.models import LegalEntity

router = APIRouter(prefix="/reportes", tags=["Reportes"])


def fmt(amount) -> float:
    return round(float(amount or 0), 2)


# ── 1. Estado de cuenta por cliente ──────────────────────────────────────────
@router.get("/estado-cuenta")
async def estado_cuenta(
    db: DBDep,
    current_user: CurrentUser,
    client_id: Optional[str] = Query(default=None),
):
    # Get clients
    if client_id:
        clients_r = await db.execute(select(LegalEntity).where(LegalEntity.id == client_id))
        clients = clients_r.scalars().all()
    else:
        clients_r = await db.execute(select(LegalEntity).order_by(LegalEntity.legal_name))
        clients = clients_r.scalars().all()

    result = []
    for client in clients:
        # Invoices
        inv_r = await db.execute(
            select(Invoice).where(Invoice.client_id == client.id).order_by(Invoice.issue_date.desc())
        )
        invoices = inv_r.scalars().all()

        # Quotes
        quote_r = await db.execute(
            select(Quote).where(Quote.client_id == client.id).order_by(Quote.issue_date.desc())
        )
        quotes = quote_r.scalars().all()

        total_facturado = sum(fmt(i.total) for i in invoices)
        total_cobrado = sum(fmt(i.paid_amount) for i in invoices)
        total_saldo = sum(fmt(i.balance) for i in invoices if i.status not in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED])

        result.append({
            "client": {
                "id": client.id,
                "legal_name": client.legal_name,
                "trade_name": client.trade_name,
                "rfc": client.rfc,
                "email": client.email,
                "phone": client.phone,
            },
            "resumen": {
                "total_facturado": total_facturado,
                "total_cobrado": total_cobrado,
                "saldo_pendiente": total_saldo,
                "facturas": len(invoices),
                "cotizaciones": len(quotes),
            },
            "facturas": [
                {
                    "folio": i.folio,
                    "issue_date": i.issue_date.isoformat() if i.issue_date else None,
                    "due_date": i.due_date.isoformat() if i.due_date else None,
                    "total": fmt(i.total),
                    "paid_amount": fmt(i.paid_amount),
                    "balance": fmt(i.balance),
                    "status": i.status,
                }
                for i in invoices
            ],
            "cotizaciones": [
                {
                    "folio": q.folio,
                    "issue_date": q.issue_date.isoformat() if q.issue_date else None,
                    "total": fmt(q.total),
                    "status": q.status,
                }
                for q in quotes
            ],
        })

    return {"clientes": result, "total_clientes": len(result)}


# ── 2. Resumen ejecutivo ──────────────────────────────────────────────────────
@router.get("/resumen-ejecutivo")
async def resumen_ejecutivo(
    db: DBDep,
    current_user: CurrentUser,
    year: int = Query(default=datetime.now().year),
):
    meses = []
    for mes in range(1, 13):
        inicio = datetime(year, mes, 1, tzinfo=timezone.utc)
        if mes == 12:
            fin = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            fin = datetime(year, mes + 1, 1, tzinfo=timezone.utc)

        # Cotizado
        cot_r = await db.execute(
            select(func.sum(Quote.total)).where(
                Quote.issue_date >= inicio,
                Quote.issue_date < fin,
            )
        )
        cotizado = fmt(cot_r.scalar_one())

        # Facturado
        fac_r = await db.execute(
            select(func.sum(Invoice.total)).where(
                Invoice.issue_date >= inicio,
                Invoice.issue_date < fin,
            )
        )
        facturado = fmt(fac_r.scalar_one())

        # Cobrado
        cob_r = await db.execute(
            select(func.sum(Invoice.paid_amount)).where(
                Invoice.issue_date >= inicio,
                Invoice.issue_date < fin,
            )
        )
        cobrado = fmt(cob_r.scalar_one())

        meses.append({
            "mes": mes,
            "nombre": inicio.strftime("%b %Y"),
            "cotizado": cotizado,
            "facturado": facturado,
            "cobrado": cobrado,
            "pendiente": facturado - cobrado,
        })

    totales = {
        "cotizado": sum(m["cotizado"] for m in meses),
        "facturado": sum(m["facturado"] for m in meses),
        "cobrado": sum(m["cobrado"] for m in meses),
        "pendiente": sum(m["pendiente"] for m in meses),
    }

    return {"year": year, "meses": meses, "totales": totales}


# ── 3. Antigüedad de saldos ───────────────────────────────────────────────────
@router.get("/antiguedad-saldos")
async def antiguedad_saldos(db: DBDep, current_user: CurrentUser):
    now = datetime.now(timezone.utc)

    inv_r = await db.execute(
        select(Invoice).where(
            Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE])
        )
    )
    invoices = inv_r.scalars().all()

    rangos = {
        "corriente": [],    # Sin vencer
        "1_30": [],         # 1-30 días vencida
        "31_60": [],        # 31-60 días vencida
        "61_90": [],        # 61-90 días vencida
        "mas_90": [],       # +90 días vencida
    }

    for inv in invoices:
        client_name = None
        c = await db.execute(select(LegalEntity).where(LegalEntity.id == inv.client_id))
        cl = c.scalar_one_or_none()
        if cl:
            client_name = cl.trade_name or cl.legal_name

        item = {
            "folio": inv.folio,
            "client_name": client_name,
            "total": fmt(inv.total),
            "balance": fmt(inv.balance),
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "status": inv.status,
        }

        if not inv.due_date:
            rangos["corriente"].append(item)
            continue

        dias_vencida = (now - inv.due_date.replace(tzinfo=timezone.utc)).days

        if dias_vencida <= 0:
            rangos["corriente"].append(item)
        elif dias_vencida <= 30:
            rangos["1_30"].append(item)
        elif dias_vencida <= 60:
            rangos["31_60"].append(item)
        elif dias_vencida <= 90:
            rangos["61_90"].append(item)
        else:
            rangos["mas_90"].append(item)

    resumen = {
        rango: {
            "items": items,
            "total": sum(i["balance"] for i in items),
            "count": len(items),
        }
        for rango, items in rangos.items()
    }

    return {
        "rangos": resumen,
        "total_general": sum(r["total"] for r in resumen.values()),
    }


# ── 4. Pipeline de cotizaciones ───────────────────────────────────────────────
@router.get("/pipeline")
async def pipeline_cotizaciones(db: DBDep, current_user: CurrentUser):
    estados = {}
    for s in QuoteStatus:
        r = await db.execute(
            select(func.count(Quote.id), func.sum(Quote.total)).where(Quote.status == s)
        )
        row = r.one()
        estados[s.value] = {
            "count": row[0],
            "total": fmt(row[1]),
        }

    # Top cotizaciones activas
    top_r = await db.execute(
        select(Quote).where(
            Quote.status.in_([QuoteStatus.DRAFT, QuoteStatus.SENT])
        ).order_by(Quote.total.desc()).limit(10)
    )
    top_quotes = top_r.scalars().all()

    top = []
    for q in top_quotes:
        client_name = None
        c = await db.execute(select(LegalEntity).where(LegalEntity.id == q.client_id))
        cl = c.scalar_one_or_none()
        if cl:
            client_name = cl.trade_name or cl.legal_name
        top.append({
            "folio": q.folio,
            "client_name": client_name,
            "total": fmt(q.total),
            "status": q.status,
            "issue_date": q.issue_date.isoformat() if q.issue_date else None,
            "expiry_date": q.expiry_date.isoformat() if q.expiry_date else None,
        })

    pipeline_total = estados.get("draft", {}).get("total", 0) + estados.get("sent", {}).get("total", 0)
    aprobadas_total = estados.get("approved", {}).get("total", 0)
    total_cotizado = sum(v["total"] for v in estados.values())
    tasa_conversion = round(aprobadas_total / total_cotizado * 100, 1) if total_cotizado else 0

    return {
        "estados": estados,
        "pipeline_total": pipeline_total,
        "tasa_conversion": tasa_conversion,
        "top_cotizaciones": top,
    }
