import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
new_password = 'admin123'
hashed = pwd_context.hash(new_password)

async def main():
    engine = create_async_engine('postgresql+asyncpg://daco:daco_secret@localhost:5432/daco')
    async with engine.connect() as conn:
        result = await conn.execute(text("UPDATE users SET hashed_password = :hash WHERE email = 'admin@gmail.com'"), {"hash": hashed})
        await conn.commit()
        print('Contraseña actualizada para admin@gmail.com')
        print('Nueva contraseña: admin123')
    await engine.dispose()

asyncio.run(main())
