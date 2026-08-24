import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('postgresql+asyncpg://daco:daco_secret@localhost:5432/daco')
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'invoices' ORDER BY column_name"))
        columns = [row.column_name for row in result]
        print('Columnas existentes en invoices:')
        for c in columns:
            print(f'  - {c}')
            
        required = ['id', 'folio', 'client_id', 'issue_date', 'due_date', 'status', 'currency', 
                   'exchange_rate', 'subtotal', 'iva_amount', 'total', 'paid_amount', 'balance',
                   'notes', 'pdf_url', 'created_at', 'updated_at']
        
        print('\nCampos requeridos por InvoiceResponse:')
        for r in required:
            status = 'OK' if r in columns else 'FALTA'
            print(f'  {status} {r}')
    await engine.dispose()

asyncio.run(main())
