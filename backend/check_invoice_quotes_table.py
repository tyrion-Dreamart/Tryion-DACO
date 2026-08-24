import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('postgresql+asyncpg://daco:daco_secret@localhost:5432/daco')
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = 'invoice_quotes')"))
        exists = result.scalar_one()
        print(f'Tabla invoice_quotes existe: {exists}')
    await engine.dispose()

asyncio.run(main())
