"""
Fixtures de integración: corren contra Postgres real, aisladas en su propio
esquema (`pytest`, ver TEST_SCHEMA) para no tocar los datos de `public`.

Requiere una URL de Postgres en TEST_DATABASE_URL (o DATABASE_URL como
fallback) — no usa SQLite ni mocks: los enums, NUMERIC, CASCADE, etc. de
Postgres son parte de lo que se está probando.

El esquema se crea/destruye con un engine SÍNCRONO (psycopg2) fuera de
cualquier event loop de asyncio — el engine async (asyncpg) se crea de
nuevo en cada test, dentro del loop de ESE test, para evitar compartir
conexiones asyncpg entre distintos event loops (pytest-asyncio crea uno
por test por default).
"""
import os
import uuid

os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

TEST_SCHEMA = "pytest"
_raw_url = os.environ.get("TEST_DATABASE_URL") or os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://daco:daco_secret@localhost:5432/daco"
)
os.environ.setdefault("DATABASE_URL", _raw_url)
_sync_url = _raw_url.replace("+asyncpg", "+psycopg2")


@pytest.fixture(scope="session", autouse=True)
def _setup_schema():
    """Crea un esquema `pytest` limpio con el shape actual de los modelos."""
    from app.models.models import Base  # importa también quote_models vía app/models/__init__

    engine = create_engine(_sync_url)
    with engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
        conn.execute(text(f"CREATE SCHEMA {TEST_SCHEMA}"))
        conn.execute(text(f"SET search_path TO {TEST_SCHEMA}"))
        Base.metadata.create_all(conn)
    engine.dispose()

    yield

    engine = create_engine(_sync_url)
    with engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
    engine.dispose()


@pytest_asyncio.fixture
async def _engine():
    engine = create_async_engine(
        _raw_url,
        connect_args={"server_settings": {"search_path": TEST_SCHEMA}},
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables(_engine):
    """Deja las tablas vacías antes de cada test (aislamiento entre tests)."""
    from app.models.models import Base

    async with _engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f'TRUNCATE TABLE "{TEST_SCHEMA}"."{table.name}" CASCADE'))
    yield


@pytest_asyncio.fixture
async def db_session(_engine):
    session_factory = async_sessionmaker(_engine, expire_on_commit=False, autoflush=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    from app.db.base import get_db
    from app.main import app

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_corporate_and_client(db_session):
    """Corporate + LegalEntity mínimos para usar como client_id en quotes/invoices/contacts."""
    from app.models.models import Corporate, LegalEntity

    corp = Corporate(name=f"Test Corp {uuid.uuid4().hex[:8]}")
    db_session.add(corp)
    await db_session.flush()

    entity = LegalEntity(corporate_id=corp.id, legal_name=f"Test Legal Entity {uuid.uuid4().hex[:8]}")
    db_session.add(entity)
    await db_session.commit()
    await db_session.refresh(entity)
    return entity


@pytest_asyncio.fixture
async def test_user(db_session):
    from app.core.security import hash_password
    from app.models.models import User, UserRole

    user = User(
        email=f"pytest-{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("testpass123"),
        full_name="Pytest User",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user):
    from app.core.security import create_access_token

    token = create_access_token(test_user.id, {"role": test_user.role, "name": test_user.full_name})
    return {"Authorization": f"Bearer {token}"}
