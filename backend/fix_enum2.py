import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('postgresql+asyncpg://daco:daco_secret@localhost:5432/daco')
    async with engine.connect() as conn:
        # Cambiar el tipo de la columna a texto temporalmente
        await conn.execute(text('ALTER TABLE invoices ALTER COLUMN status TYPE VARCHAR(50)'))
        
        # Actualizar los valores ANTES de crear el enum nuevo
        await conn.execute(text("UPDATE invoices SET status = 'PENDING' WHERE status = 'ISSUED'"))
        await conn.execute(text("UPDATE invoices SET status = 'PARTIALLY_PAID' WHERE status = 'PARTIAL'"))
        
        # Eliminar el enum viejo
        await conn.execute(text('DROP TYPE IF EXISTS invoice_status'))
        
        # Crear el enum nuevo con los valores correctos
        await conn.execute(text("CREATE TYPE invoice_status AS ENUM ('PENDING', 'PAID', 'PARTIALLY_PAID', 'OVERDUE', 'CANCELLED')"))
        
        # Cambiar la columna de nuevo al enum nuevo
        await conn.execute(text('ALTER TABLE invoices ALTER COLUMN status TYPE invoice_status USING status::invoice_status'))
        
        await conn.commit()
        print('Enum actualizado correctamente!')
    await engine.dispose()

asyncio.run(main())
