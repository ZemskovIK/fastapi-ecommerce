from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from decouple import config

# Строка подключения для SQLite
DATABASE_URL = "sqlite:///ecommerce.db"

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(bind=engine)


# --------------- Асинхронное подключение к PostgreSQL -------------------------

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# Строка подключения для PostgreSQl
DATABASE_URL = config("DATABASE_URL")

async_engine = create_async_engine(DATABASE_URL, echo=True)

async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass