import asyncio
from app.db.base import AsyncSessionLocal
from app.core.security import verify_password
from app.models.models import User
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        for u in users:
            print(f"Email: {u.email}")
            print(f"Active: {u.is_active}")
            print(f"Password OK: {verify_password('Admin123!', u.hashed_password)}")

asyncio.run(check())