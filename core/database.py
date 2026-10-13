# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    _instance = None

    def __init__(self):
        self._engine = None
        self._session_factory = None
        self.db_url = os.getenv("DB_CONN")
        if not self.db_url:
            raise ValueError("DB_CONN 환경 변수가 설정되지 않았습니다.")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def connect(self):
        if self._engine is None:
            self._engine = create_async_engine(
                self.db_url,
                pool_size=10,
                max_overflow=0,
                pool_recycle=300,
                echo=False
            )
            self._session_factory = sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            print("Database Engine Created.")

    async def close(self):
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            print("Database Engine Disposed.")

    async def get_db_session(self) -> AsyncGenerator[AsyncSession, None]:
        if self._session_factory is None:
            self.connect()
        
        async with self._session_factory() as session:
            yield session

# 의존성 주입(DI)을 위한 헬퍼 함수
async def get_db_conn():
    db = Database.get_instance()
    async for session in db.get_db_session():
        yield session