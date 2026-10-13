"""Punto de entrada principal de la aplicación Cafetería POS (backend con FastAPI).

Este archivo es el "arranque" del servidor web. Aquí se:
- Crea la instancia de ``FastAPI`` (la aplicación que atiende las peticiones HTTP).
- Registra los ``routers`` (grupos de endpoints) de cada módulo del negocio.
- Configura CORS (para que el frontend pueda consumir la API).
- Define manejadores globales de errores (traducen errores de negocio a códigos HTTP).
- Ejecuta tareas de arranque mediante ``lifespan``: crear/actualizar el esquema de la
  base de datos (``_ensure_schema``) y sembrar el usuario administrador inicial
  (``_seed_admin``).

Se relaciona con: ``config.py`` (configuración/entorno), ``database.py`` (conexión y
esquema), ``application/`` (lógica de aplicación) e ``infrastructure/api/routers``
endpoints de la API. El servidor se levanta típicamente con:
``uvicorn app:app``.
"""

import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import jwt
from sqlalchemy import inspect, text

from application.events import event_bus
from application.security.hashing import hash_password
from application.security.jwt import decode_token
from application.utils import new_id
from config import settings
from database import Base, engine, SessionLocal
from domain.exceptions import (
    ConflictError,
    DomainError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from infrastructure.api.routers import (
    auth,
    categorias,
    compras,
    configuracion,
    costeo,
    costos_fijos,
    eventos,
    insumos,
    notas,
    productos,
    proveedores,
    reportes,
    ventas,
)
import infrastructure.models  # noqa: F401  (registra los modelos en Base.metadata)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación (eventos de arranque y apagado).

    FastAPI ejecuta el código antes del ``yield`` cuando el servidor **arranca**,
    y el código después del ``yield`` cuando el servidor **se detiene**.

    Aquí, al arrancar:
    1. Se asegura de que el esquema de base de datos exista/esté actualizado.
    2. Se crea el usuario administrador por defecto si aún no existe.

    Parámetros:
        app (FastAPI): instancia de la aplicación que FastAPI inyecta.

    Yields:
        None: cede el control para que el servidor empiece a atender peticiones.
    """
    # --- Fase de arranque (antes del yield) ---
    _ensure_schema()  # Crea tablas y columnas faltantes.
    _seed_admin()  # Garantiza que exista un usuario admin.
    # --- A partir de aquí el servidor atiende peticiones ---
    yield
    # --- Fase de apagado (después del yield): aquí no hay limpieza pendiente ---


def _default_sql(column, dialect: str) -> str:
    """Construye el valor DEFAULT de una columna como texto SQL.

    Se usa al agregar columnas nuevas a tablas existentes: cuando una columna no
    admite ``NULL`` necesitamos un valor por defecto válido para rellenar las
    filas que ya existían.

    Parámetros:
        column: columna de SQLAlchemy (``Column``) de la que se lee ``default``.
        dialect (str): nombre del dialecto de base de datos (p. ej. "sqlite",
            "postgresql") para escribir los booleanos de forma compatible.

    Retorno:
        str: representación SQL del valor por defecto. Si no hay default
        reconocible, devuelve ``''`` (cadena vacía) con comillas.
    """
    default = getattr(column, "default", None)
    # ``default.arg`` contiene el valor real cuando el default es un objeto
    # tipo ``default=valor`` de SQLAlchemy.
    if default is not None and hasattr(default, "arg"):
        val = default.arg
        if isinstance(val, bool):
            # Postgres usa true/false; el resto (SQLite, MySQL) usa 1/0.
            if dialect.startswith("postgres"):
                return "true" if val else "false"
            return "1" if val else "0"
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, str):
            # Las cadenas van entre comillas simples en SQL.
            return f"'{val}'"
    # Fallback seguro: cadena vacía.
    return "''"


def _ensure_schema() -> None:
    """Crea las tablas y agrega las columnas que falten (esquema auto-sanable).

    Primero crea todas las tablas declaradas en los modelos (si no existen).
    Después, para cada tabla ya existente, detecta columnas nuevas en los
    modelos y las agrega con ``ALTER TABLE``. Esto permite evolucionar el
    esquema sin una migración manual en entornos sencillos.

    Retorno:
        None
    """
    # Crea las tablas definidas en los modelos (no hace nada si ya existen).
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    dialecto = engine.dialect.name  # "sqlite", "postgresql", etc.
    with engine.begin() as conn:  # transacción: todo o nada
        for table in Base.metadata.sorted_tables:
            # Si la tabla no existe físicamente, se omite (create_all ya la habría creado).
            if table.name not in inspector.get_table_names():
                continue
            # Columnas que ya existen en la base de datos real.
            existing_cols = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                # Si la columna ya existe o es llave primaria, no se toca.
                if column.name in existing_cols or column.primary_key:
                    continue
                # Compila el tipo de la columna al dialecto actual (INTEGER, VARCHAR, etc.).
                col_type = column.type.compile(engine.dialect)
                if column.nullable:
                    # Columna opcional: se puede agregar sin default.
                    ddl = f"ALTER TABLE {table.name} ADD COLUMN {column.name} {col_type}"
                else:
                    # Columna obligatoria: necesita NOT NULL + DEFAULT para las filas existentes.
                    ddl = (
                        f"ALTER TABLE {table.name} ADD COLUMN {column.name} "
                        f"{col_type} NOT NULL DEFAULT {_default_sql(column, dialecto)}"
                    )
                conn.execute(text(ddl))


def _seed_admin() -> None:
    """Crea el usuario administrador inicial si no existe ninguno.

    Busca cualquier usuario con rol ``admin``. Si no lo encuentra, inserta uno
    con las credenciales tomadas de ``settings`` (``admin_email`` /
    ``admin_password``). Sirve para poder entrar al sistema la primera vez.

    Retorno:
        None
    """
    # Import local para evitar importaciones circulares en el arranque.
    from infrastructure.models.usuario import UsuarioModel

    db = SessionLocal()  # sesión de base de datos
    try:
        admin = db.query(UsuarioModel).filter(UsuarioModel.rol == "admin").first()
        if admin is None:
            # No hay admin: se crea con contraseña hasheada (nunca en texto plano).
            db.add(
                UsuarioModel(
                    id=new_id(),
                    nombre="Administrador",
                    email=settings.admin_email,
                    contraseña_hash=hash_password(settings.admin_password),
                    rol="admin",
                    estado=True,
                )
            )
            db.commit()
    finally:
        # La sesión siempre se cierra, haya error o no.
        db.close()


# Instancia principal de FastAPI: metadatos que se ven en la documentación /docs.
app = FastAPI(
    title="Cafetería POS API",
    version="1.0.0",
    description="API para la gestión de productos y ventas de Cafetería POS.",
    lifespan=lifespan,  # enlaza las tareas de arranque/apagado definidas arriba
)

# CORS: permite que el frontend (desde otro origen) consuma la API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # orígenes permitidos (desde config)
    allow_credentials=False,
    allow_methods=["*"],  # permite todos los métodos HTTP (GET, POST, ...)
    allow_headers=["*"],  # permite todas las cabeceras
)

# Registro de routers: cada uno agrupa los endpoints de un módulo del negocio.
app.include_router(auth.router)
app.include_router(productos.router)
app.include_router(categorias.router)
app.include_router(proveedores.router)
app.include_router(ventas.router)
app.include_router(compras.router)
app.include_router(reportes.router)
app.include_router(eventos.router)
app.include_router(configuracion.router)
app.include_router(insumos.router)
app.include_router(costos_fijos.router)
app.include_router(costeo.router)
app.include_router(notas.router)


@app.exception_handler(DomainError)
async def domain_error_handler(request, exc: DomainError):
    """Traduce los errores de negocio (``DomainError``) a respuestas HTTP.

    Los errores del dominio no saben de HTTP; este manejador les asigna el
    código de estado adecuado según el tipo concreto de excepción.

    Parámetros:
        request: petición HTTP entrante (inyectada por FastAPI; no se usa).
        exc (DomainError): excepción de negocio lanzada por la capa de dominio.

    Retorno:
        JSONResponse: cuerpo ``{"detail": mensaje}`` con el código HTTP correcto.
    """
    codigo = 400  # valor por defecto: error genérico de petición
    if isinstance(exc, NotFoundError):
        codigo = 404  # recurso no encontrado
    elif isinstance(exc, ValidationError):
        codigo = 422  # datos no procesables / inválidos
    elif isinstance(exc, ConflictError):
        codigo = 409  # conflicto (p. ej. duplicado)
    elif isinstance(exc, ForbiddenError):
        codigo = 403  # sin permisos
    elif isinstance(exc, UnauthorizedError):
        codigo = 401  # no autenticado
    return JSONResponse(status_code=codigo, content={"detail": str(exc)})


@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    """Convierte cualquier ``ValueError`` no controlado en un HTTP 422.

    Evita que un error de validación termine como un error 500 del servidor.

    Parámetros:
        request: petición HTTP entrante (no se usa).
        exc (ValueError): excepción capturada.

    Retorno:
        JSONResponse: ``{"detail": mensaje}`` con estado 422.
    """
    return JSONResponse(status_code=422, content={"detail": str(exc)})
