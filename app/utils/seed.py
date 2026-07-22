"""
Seed script: Creates default super_admin user.
Run: docker compose exec api python -m app.utils.seed
"""
import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.db.base import AsyncSessionLocal
from app.models.models import User, UserRole


async def seed():
    async with AsyncSessionLocal() as db:
        # Check if superadmin exists
        result = await db.execute(
            select(User).where(User.email == "admin@daco.local")
        )
        if result.scalar_one_or_none():
            print("✓ Super admin already exists")
            return

        user = User(
            email="admin@daco.local",
            hashed_password=hash_password("Admin123!"),
            full_name="DACO Administrator",
            role=UserRole.SUPER_ADMIN,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        print("✓ Super admin created: admin@daco.local / Admin123!")
        print("  ⚠  Change password immediately in production!")


if __name__ == "__main__":
    asyncio.run(seed())
