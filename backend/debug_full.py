import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func

async def test():
    engine = create_async_engine('postgresql+asyncpg://daco:daco_secret@localhost:5432/daco')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            from app.models.models import Invoice, LegalEntity
            from app.models.quote_models import Quote
            from app.models.models import invoice_quotes
            
            # Simular exactamente lo que hace el endpoint
            query = select(Invoice)
            count_r = await db.execute(select(func.count()).select_from(query.subquery()))
            total = count_r.scalar_one()
            print(f'Total facturas: {total}')
            
            result = await db.execute(
                query.offset(0).limit(20).order_by(Invoice.issue_date.desc())
            )
            invoices = result.scalars().all()
            print(f'Facturas obtenidas: {len(invoices)}')
            
            for inv in invoices:
                print(f'Procesando factura: {inv.id}, folio: {inv.folio}, status: {inv.status}')
                
                # Verificar client_id
                print(f'  client_id: {inv.client_id}')
                
                # Buscar LegalEntity
                c = await db.execute(select(LegalEntity).where(LegalEntity.id == inv.client_id))
                cl = c.scalar_one_or_none()
                client_name = (cl.trade_name or cl.legal_name) if cl else None
                print(f'  Cliente: {client_name}')
                
                # Verificar invoice_quotes
                try:
                    result_q = await db.execute(
                        select(Quote).join(invoice_quotes, Quote.id == invoice_quotes.c.quote_id)
                        .where(invoice_quotes.c.invoice_id == inv.id)
                    )
                    quotes = result_q.scalars().all()
                    print(f'  Quotes: {len(quotes)}')
                except Exception as e:
                    print(f'  Error en quotes: {e}')
                    
                # Verificar quote_id directo
                if inv.quote_id:
                    q = await db.execute(select(Quote).where(Quote.id == inv.quote_id))
                    qt = q.scalar_one_or_none()
                    print(f'  Quote directo: {qt.folio if qt else None}')
                
                # Construir response
                from app.schemas.invoice_schemas import InvoiceResponse
                try:
                    resp = InvoiceResponse(
                        id=inv.id,
                        folio=inv.folio,
                        client_id=inv.client_id,
                        quote_id=inv.quote_id,
                        quote_ids=[],
                        issue_date=inv.issue_date,
                        due_date=inv.due_date,
                        status=inv.status,
                        currency=inv.currency,
                        exchange_rate=float(inv.exchange_rate) if inv.exchange_rate else None,
                        subtotal=float(inv.subtotal),
                        iva_amount=float(inv.iva_amount),
                        total=float(inv.total),
                        paid_amount=float(inv.paid_amount),
                        balance=float(inv.balance),
                        notes=inv.notes,
                        pdf_url=inv.pdf_url,
                        created_at=inv.created_at,
                        updated_at=inv.updated_at,
                        client_name=client_name,
                        quote_folio=None,
                        quotes_folios=[],
                    )
                    print(f'  Response OK: {resp.folio}')
                except Exception as e:
                    print(f'  Error en response: {e}')
                    import traceback
                    traceback.print_exc()
                    
        except Exception as e:
            import traceback
            traceback.print_exc()

asyncio.run(test())
