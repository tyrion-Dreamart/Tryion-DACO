from datetime import datetime, timezone
from fastapi import APIRouter
from sqlalchemy import select, func, desc
from app.core.deps import CurrentUser, DBDep
from app.models.models import LegalEntity, Corporate
from app.models.quote_models import Quote, QuoteItem, QuoteStatus
from app.models.invoice_models import Invoice, InvoiceStatus

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def to_mxn(amount, inv):
    """Convierte monto a MXN usando TC de la factura si es USD"""
    if inv.currency == 'USD' and inv.exchange_rate:
        return float(amount) * float(inv.exchange_rate)
    return float(amount)


@router.get("/summary")
async def get_summary(db: DBDep, current_user: CurrentUser):
    now = datetime.now(timezone.utc)
    mes_inicio = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # ── Clientes ──────────────────────────────────────────────────────────────
    total_clientes_r = await db.execute(select(func.count(LegalEntity.id)))
    total_clientes = total_clientes_r.scalar_one()

    # ── Cotizaciones stats ────────────────────────────────────────────────────
    stats = {}
    for s in QuoteStatus:
        r = await db.execute(select(func.count(Quote.id)).where(Quote.status == s))
        stats[s.value] = r.scalar_one()

    pipeline_r = await db.execute(
        select(func.sum(Quote.total)).where(
            Quote.status.in_([QuoteStatus.DRAFT, QuoteStatus.SENT])
        )
    )
    pipeline = float(pipeline_r.scalar_one() or 0)

    # ── Facturas — todas para calcular MXN equivalente ───────────────────────
    all_inv_r = await db.execute(
        select(Invoice).where(
            Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIAL, InvoiceStatus.PAID, InvoiceStatus.OVERDUE])
        )
    )
    all_inv = all_inv_r.scalars().all()

    facturado = sum(
        to_mxn(i.total, i) for i in all_inv
        if i.status in [InvoiceStatus.ISSUED, InvoiceStatus.PARTIAL, InvoiceStatus.PAID]
    )
    cobrado = sum(
        to_mxn(i.paid_amount, i) for i in all_inv
        if i.status in [InvoiceStatus.ISSUED, InvoiceStatus.PARTIAL, InvoiceStatus.PAID]
    )
    por_cobrar = sum(
        to_mxn(i.balance, i) for i in all_inv
        if i.status in [InvoiceStatus.ISSUED, InvoiceStatus.PARTIAL]
    )
    vencido = sum(
        to_mxn(i.balance, i) for i in all_inv
        if i.status == InvoiceStatus.OVERDUE
    )

    facturas_vigentes = sum(
        1 for i in all_inv
        if i.status in [InvoiceStatus.ISSUED, InvoiceStatus.PARTIAL]
    )
    facturas_vencidas = sum(
        1 for i in all_inv
        if i.status == InvoiceStatus.OVERDUE
    )

    pct_cobrado = round(cobrado / facturado * 100) if facturado else 0

    # ── Mix de servicios ──────────────────────────────────────────────────────
    items_r = await db.execute(
        select(QuoteItem.concept, func.sum(QuoteItem.total).label("amount"))
        .group_by(QuoteItem.concept)
        .order_by(desc("amount"))
        .limit(5)
    )
    items = items_r.all()
    total_items = sum(float(i.amount) for i in items)
    mix = [
        {
            "name": i.concept[:40] + ("..." if len(i.concept) > 40 else ""),
            "clients": 1,
            "amount": float(i.amount),
            "pct": round(float(i.amount) / total_items * 100) if total_items else 0,
        }
        for i in items
    ]

    # ── CxC agrupado por corporativo con conversión MXN ───────────────────────
    corp_r = await db.execute(select(Corporate).order_by(Corporate.name))
    corporates = corp_r.scalars().all()

    cxc_grupos = []
    for corp in corporates:
        les_r = await db.execute(
            select(LegalEntity).where(LegalEntity.corporate_id == corp.id)
        )
        les = les_r.scalars().all()
        sub_cuentas = []
        for le in les:
            inv_r = await db.execute(
                select(Invoice).where(
                    Invoice.client_id == le.id,
                    Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE])
                ).order_by(Invoice.due_date.asc())
            )
            invs = inv_r.scalars().all()
            saldo = sum(to_mxn(i.balance or 0, i) for i in invs)
            cobrado_le = sum(to_mxn(i.paid_amount or 0, i) for i in invs)
            if invs:
                sub_cuentas.append({
                    "id": le.id,
                    "legal_name": le.legal_name,
                    "rfc": le.rfc,
                    "saldo": saldo,
                    "cobrado": cobrado_le,
                    "facturas": len(invs),
                    "detalle": [
                        {
                            "folio": i.folio,
                            "total": to_mxn(i.total, i),
                            "paid_amount": to_mxn(i.paid_amount, i),
                            "balance": to_mxn(i.balance, i),
                            "due_date": i.due_date.isoformat() if i.due_date else None,
                            "status": str(i.status).replace("InvoiceStatus.", "").lower(),
                            "currency": i.currency,
                            "exchange_rate": float(i.exchange_rate) if i.exchange_rate else None,
                        }
                        for i in invs
                    ],
                })
        if sub_cuentas:
            cxc_grupos.append({
                "corporativo": corp.name,
                "corporativo_id": corp.id,
                "sub_cuentas": sub_cuentas,
                "total_saldo": sum(s["saldo"] for s in sub_cuentas),
                "total_cobrado": sum(s["cobrado"] for s in sub_cuentas),
            })

    # Clientes sin corporativo
    sin_corp_r = await db.execute(
        select(LegalEntity).where(LegalEntity.corporate_id == None)
    )
    sin_corp = sin_corp_r.scalars().all()
    for le in sin_corp:
        inv_r = await db.execute(
            select(Invoice).where(
                Invoice.client_id == le.id,
                Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE])
            )
        )
        invs = inv_r.scalars().all()
        saldo = sum(to_mxn(i.balance or 0, i) for i in invs)
        if invs:
            cxc_grupos.append({
                "corporativo": le.trade_name or le.legal_name,
                "corporativo_id": None,
                "sub_cuentas": [{
                    "id": le.id,
                    "legal_name": le.legal_name,
                    "rfc": le.rfc,
                    "saldo": saldo,
                    "cobrado": sum(to_mxn(i.paid_amount or 0, i) for i in invs),
                    "facturas": len(invs),
                    "detalle": [],
                }],
                "total_saldo": saldo,
                "total_cobrado": sum(to_mxn(i.paid_amount or 0, i) for i in invs),
            })

    return {
        "periodo": mes_inicio.strftime("%B %Y").capitalize(),
        "facturado": facturado,
        "cobrado": cobrado,
        "por_cobrar": por_cobrar,
        "vencido": vencido,
        "pct_cobrado": pct_cobrado,
        "facturas_vigentes": facturas_vigentes,
        "facturas_vencidas": facturas_vencidas,
        "clientes_total": total_clientes,
        "clientes_activos": stats.get("approved", 0),
        "clientes_inactivos": 0,
        "mix_servicios": mix,
        "cxc_grupos": cxc_grupos,
        "cotizaciones": {
            "draft": stats.get("draft", 0),
            "sent": stats.get("sent", 0),
            "approved": stats.get("approved", 0),
            "rejected": stats.get("rejected", 0),
            "pipeline": pipeline,
        }
    }
