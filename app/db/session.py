import os
import ssl
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "")

# asyncpg requires postgresql+asyncpg:// scheme
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# asyncpg doesn't accept sslmode/channel_binding as URL params — strip them
# and pass SSL via connect_args instead
parsed = urlparse(DATABASE_URL)
params = parse_qs(parsed.query)
params.pop("sslmode", None)
params.pop("channel_binding", None)
clean_query = urlencode({k: v[0] for k, v in params.items()})
DATABASE_URL = urlunparse(parsed._replace(query=clean_query))

ssl_context = ssl.create_default_context()

engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    connect_args={"ssl": ssl_context},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
