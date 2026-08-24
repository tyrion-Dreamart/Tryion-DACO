import asyncio
from app.db.base import AsyncSessionLocal as async_session
from app.models.models import User, UserRole
from app.core.security import hash_password

async def create_admin():
    async with async_session() as db:
        # Verificar si ya existe admin
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == "admin@daco.com"))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("Admin ya existe!")
            return
        
        admin = User(
            email="admin@daco.com",
            hashed_password=hash_password("Admin123!"),
            full_name="Administrador DACO",
            role=UserRole.SUPER_ADMIN,
            is_active=True
        )
        db.add(admin)
        await db.commit()
        print("✅ Usuario admin creado: admin@daco.com / Admin123!")

if __name__ == "__main__":
    asyncio.run(create_admin())