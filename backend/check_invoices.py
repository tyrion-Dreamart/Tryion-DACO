import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('postgresql+asyncpg://daco:daco_secret@localhost:5432/daco')
    async with engine.connect() as conn:
        # Verificar columnas de invoices
        result = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'invoices'"))
        columns = [row.column_name for row in result]
        print('Columnas de invoices:')
        for c in sorted(columns):
            print(f'  - {c}')
            
        # Contar facturas
        result = await conn.execute(text('SELECT COUNT(*) FROM invoices'))
        count = result.scalar_one()
        print(f'\nTotal de facturas: {count}')
        
        # Ver una factura
        if count > 0:
            result = await conn.execute(text('SELECT * FROM invoices LIMIT 1'))
            row = result.fetchone()
            print(f'\nPrimera factura:')
            for col, val in zip(result.keys(), row):
                print(f'  {col}: {val}')
    await engine.dispose()

asyncio.run(main())
