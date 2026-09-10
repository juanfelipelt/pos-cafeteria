from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings


def _normalizar_url(url: str) -> str:
    """Normaliza la URL de conexión para SQLAlchemy.

    - ``postgres://`` (formato viejo de Render/Heroku) -> ``postgresql://``.
    - En Postgres remoto fuerza ``sslmode=require`` (Supabase lo exige) si no
      viene ya en la URL y no es un host local.
    """
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]

    es_postgres = url.startswith("postgresql")
    es_local = "localhost" in url or "127.0.0.1" in url
    if es_postgres and not es_local and "sslmode=" not in url:
        separador = "&" if "?" in url else "?"
        url = f"{url}{separador}sslmode=require"
    return url


database_url = _normalizar_url(settings.database_url)

connect_args: dict = {}
engine_kwargs: dict = {"future": True}

if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    engine_kwargs.update(pool_pre_ping=True, pool_recycle=300)

engine = create_engine(database_url, connect_args=connect_args, **engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

Base = declarative_base()


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
