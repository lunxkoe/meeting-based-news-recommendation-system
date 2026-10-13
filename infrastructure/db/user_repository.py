# app/infrastructure/db/user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, Dict, Any
from domain.interfaces.user_repository import IUserRepository

class MySQLUserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        query = text("SELECT id, name, email FROM user WHERE email = :email")
        result = await self.session.execute(query, {"email": email})
        row = result.fetchone()
        return row._asdict() if row else None

    async def get_by_email_with_password(self, email: str) -> Optional[Dict[str, Any]]:
        query = text("SELECT id, name, email, hashed_password FROM user WHERE email = :email")
        result = await self.session.execute(query, {"email": email})
        row = result.fetchone()
        return row._asdict() if row else None

    async def create(self, user_data: Dict[str, Any]) -> None:
        query = text("""
            INSERT INTO user(name, email, hashed_password)
            VALUES (:name, :email, :hashed_password)
        """)
        await self.session.execute(query, user_data)
        await self.session.commit()