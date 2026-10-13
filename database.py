"""Capa de acceso a la base de datos (SQLAlchemy).

Este archivo configura la conexión a la base de datos y expone los objetos que
el resto de la aplicación usa:

- ``engine``: motor de conexión a la base de datos.
- ``SessionLocal``: fábrica de sesiones (una por petición, normalmente).
- ``Base``: clase base de la que heredan todos los modelos ORM.
- ``get_session()``: dependencia de FastAPI que entrega y cierra una sesión.

Se apoya en ``config.py`` para saber a qué base de datos conectarse. Los modelos
(de ``infrastructure/models``) heredan de ``Base``, y los servicios/repositorios
usan ``SessionLocal`` o ``get_session()`` para leer y escribir datos.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings


def _normalizar_url(url: str) -> str:
    """Normaliza la URL de conexión para SQLAlchemy.

    - ``postgres://`` (formato viejo de Render/Heroku) -> ``postgresql://``.
    - En Postgres remoto fuerza ``sslmode=require`` (Supabase lo exige) si no
      viene ya en la URL y no es un host local.
    """
    # SQLAlchemy moderno ya no acepta el esquema "postgres://".
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]

    es_postgres = url.startswith("postgresql")
    es_local = "localhost" in url or "127.0.0.1" in url
    # Solo forzamos SSL en Postgres remoto y si el usuario no lo indicó ya.
    if es_postgres and not es_local and "sslmode=" not in url:
        # El separador depende de si la URL ya trae parámetros ("?...").
        separador = "&" if "?" in url else "?"
        url = f"{url}{separador}sslmode=require"
    return url


# URL ya normalizada a partir de la configuración (settings).
database_url = _normalizar_url(settings.database_url)

# Argumentos y opciones que se pasan al motor según el tipo de base de datos.
connect_args: dict = {}
engine_kwargs: dict = {"future": True}  # "future" activa el estilo SQLAlchemy 2.0

if database_url.startswith("sqlite"):
    # SQLite no permite compartir una conexión entre hilos por defecto;
    # con FastAPI (async/multihilo) hay que desactivar esa comprobación.
    connect_args = {"check_same_thread": False}
else:
    # En bases de datos cliente-servidor conviene validar conexiones "viejas".
    # pool_pre_ping: prueba la conexión antes de usarla (evita errores por timeouts).
    # pool_recycle: recicla conexiones cada 300 s para que no las cierre el servidor.
    engine_kwargs.update(pool_pre_ping=True, pool_recycle=300)

# Motor de base de datos: gestiona el pool de conexiones.
engine = create_engine(database_url, connect_args=connect_args, **engine_kwargs)

# Fábrica de sesiones. autocommit/autoflush en False para controlar la
# transacción explícitamente y evitar envíos implícitos a la base de datos.
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

# Clase base declarativa: todos los modelos ORM heredan de ella.
Base = declarative_base()


def get_session():
    """Dependencia de FastAPI que abre una sesión de base de datos.

    FastAPI la inyecta en los endpoints que la declaran. El bloque ``finally``
    garantiza que la sesión se cierre siempre al terminar la petición, evitando
    fugas de conexiones.

    Yields:
        Session: sesión de SQLAlchemy lista para consultar la base de datos.
    """
    db = SessionLocal()
    try:
        yield db  # se entrega la sesión al endpoint
    finally:
        db.close()  # se cierra al finalizar (con o sin error)
