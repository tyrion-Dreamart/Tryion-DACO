"""
Restablece la contraseña de un usuario existente.

Uso:
    python reset_password.py usuario@ejemplo.com "nueva-contraseña-segura"
"""
import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.security import hash_password


async def main(email: str, new_password: str) -> None:
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.connect() as conn:
        result = await conn.execute(
            text("UPDATE users SET hashed_password = :hash WHERE email = :email"),
            {"hash": hash_password(new_password), "email": email},
        )
        await conn.commit()
        if result.rowcount == 0:
            print(f"No existe ningún usuario con email {email}")
        else:
            print(f"Contraseña actualizada para {email}")
    await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
