import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('postgresql+asyncpg://daco:daco_secret@localhost:5432/daco')
    async with engine.connect() as conn:
        # Agregar columnas faltantes
        await conn.execute(text('''
            ALTER TABLE invoices
            ADD COLUMN IF NOT EXISTS folio VARCHAR(50),
            ADD COLUMN IF NOT EXISTS client_id VARCHAR(36),
            ADD COLUMN IF NOT EXISTS exchange_rate NUMERIC(10,4),
            ADD COLUMN IF NOT EXISTS iva_amount NUMERIC(12,2) DEFAULT 0,
            ADD COLUMN IF NOT EXISTS paid_amount NUMERIC(12,2) DEFAULT 0,
            ADD COLUMN IF NOT EXISTS balance NUMERIC(12,2),
            ADD COLUMN IF NOT EXISTS pdf_url VARCHAR(500)
        '''))
        
        # Copiar invoice_number a folio
        await conn.execute(text("UPDATE invoices SET folio = invoice_number WHERE folio IS NULL"))
        
        # Copiar legal_entity_id a client_id
        await conn.execute(text("UPDATE invoices SET client_id = legal_entity_id WHERE client_id IS NULL"))
        
        # Calcular iva_amount desde tax_amount
        await conn.execute(text("UPDATE invoices SET iva_amount = COALESCE(tax_amount, 0) WHERE iva_amount = 0"))
        
        # Calcular balance
        await conn.execute(text("UPDATE invoices SET balance = total - paid_amount WHERE balance IS NULL"))
        
        await conn.commit()
        print('Migracion completada!')
    await engine.dispose()

asyncio.run(main())
