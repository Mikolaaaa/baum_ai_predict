from typing import AsyncGenerator
from datetime import datetime
from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase, SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, String, Boolean, Integer, TIMESTAMP, ForeignKey, UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
import os
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from schemas.user_schema import BaseUser, UserDB
from config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER
import uuid


DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
Base: DeclarativeMeta = declarative_base()


class User(SQLAlchemyBaseUserTableUUID, Base):
    id = Column(UUID,
                default=uuid.uuid4,
                primary_key=True,
                index=True,
                nullable=False)
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)
    surname = Column(String)
    patronymic = Column(String)
    phone = Column(String)
    registered_at = Column(TIMESTAMP, default=datetime.utcnow)
    hashed_password: str = Column(String(length=1024), nullable=False)
    is_active: bool = Column(Boolean, default=True, nullable=False)
    is_superuser: bool = Column(Boolean, default=False, nullable=False)
    is_verified: bool = Column(Boolean, default=False, nullable=False)


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)
