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
    eventos,
    productos,
    proveedores,
    reportes,
    ventas,
)
import infrastructure.models  # noqa: F401  (registra los modelos en Base.metadata)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ensure_schema()
    _seed_admin()
    yield


def _default_sql(column, dialect: str) -> str:
    default = getattr(column, "default", None)
    if default is not None and hasattr(default, "arg"):
        val = default.arg
        if isinstance(val, bool):
            if dialect.startswith("postgres"):
                return "true" if val else "false"
            return "1" if val else "0"
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, str):
            return f"'{val}'"
    return "''"


def _ensure_schema() -> None:
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    dialecto = engine.dialect.name
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in inspector.get_table_names():
                continue
            existing_cols = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing_cols or column.primary_key:
                    continue
                col_type = column.type.compile(engine.dialect)
                if column.nullable:
                    ddl = f"ALTER TABLE {table.name} ADD COLUMN {column.name} {col_type}"
                else:
                    ddl = (
                        f"ALTER TABLE {table.name} ADD COLUMN {column.name} "
                        f"{col_type} NOT NULL DEFAULT {_default_sql(column, dialecto)}"
                    )
                conn.execute(text(ddl))


def _seed_admin() -> None:
    from infrastructure.models.usuario import UsuarioModel

    db = SessionLocal()
    try:
        admin = db.query(UsuarioModel).filter(UsuarioModel.rol == "admin").first()
        if admin is None:
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
        db.close()


app = FastAPI(
    title="Cafetería POS API",
    version="1.0.0",
    description="API para la gestión de productos y ventas de Cafetería POS.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(productos.router)
app.include_router(categorias.router)
app.include_router(proveedores.router)
app.include_router(ventas.router)
app.include_router(compras.router)
app.include_router(reportes.router)
app.include_router(eventos.router)
app.include_router(configuracion.router)


@app.exception_handler(DomainError)
async def domain_error_handler(request, exc: DomainError):
    codigo = 400
    if isinstance(exc, NotFoundError):
        codigo = 404
    elif isinstance(exc, ValidationError):
        codigo = 422
    elif isinstance(exc, ConflictError):
        codigo = 409
    elif isinstance(exc, ForbiddenError):
        codigo = 403
    elif isinstance(exc, UnauthorizedError):
        codigo = 401
    return JSONResponse(status_code=codigo, content={"detail": str(exc)})


@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})
