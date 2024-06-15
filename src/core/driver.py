from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from src.config import DB_ASYNC_DRIVER, DB_USER, DB_PASSWORD, DB_HOST, DB_NAME

DATABASE_URL = f'{DB_ASYNC_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
Base = declarative_base()

engine = create_async_engine(DATABASE_URL)
async_session_marker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_marker() as session:
        yield session

