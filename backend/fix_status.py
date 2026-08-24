import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('postgresql+asyncpg://daco:daco_secret@localhost:5432/daco')
    async with engine.connect() as conn:
        # Ver valores actuales de status
        result = await conn.execute(text('SELECT DISTINCT status FROM invoices'))
        print('Valores actuales de status:')
        for row in result:
            print(f'  - {row.status}')
        
        # Actualizar ISSUED a pending
        await conn.execute(text("UPDATE invoices SET status = 'pending' WHERE status = 'ISSUED'"))
        
        # Actualizar OVERDUE a overdue (en minusculas)
        await conn.execute(text("UPDATE invoices SET status = 'overdue' WHERE status = 'OVERDUE'"))
        
        await conn.commit()
        print('Status actualizados!')
    await engine.dispose()

asyncio.run(main())
