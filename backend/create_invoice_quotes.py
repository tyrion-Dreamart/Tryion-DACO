import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('postgresql+asyncpg://daco:daco_secret@localhost:5432/daco')
    async with engine.connect() as conn:
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS invoice_quotes (
                invoice_id VARCHAR(36) NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
                quote_id VARCHAR(36) NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
                PRIMARY KEY (invoice_id, quote_id)
            )
        '''))
        await conn.commit()
        print('Tabla invoice_quotes creada exitosamente!')
    await engine.dispose()

asyncio.run(main())
