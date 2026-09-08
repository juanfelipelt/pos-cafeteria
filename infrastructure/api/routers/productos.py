from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.schemas.producto import EstadoRequest, ProductoCreate, ProductoUpdate
from application.services.producto_service import ProductoService
from database import get_session
from infrastructure.api.dependencies import get_current_user
from infrastructure.repositories.producto_repository import (
    SQLAlchemyProductoRepository,
)

router = APIRouter(prefix="/productos", tags=["productos"])


@router.get("")
def listar(
    filtro: str | None = None,
    categoria_id: str | None = None,
    solo_activos: bool = False,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    service = ProductoService(SQLAlchemyProductoRepository(db), db)
    return [p.to_dict() for p in service.listar(filtro, categoria_id, solo_activos)]


@router.post("")
def crear(
    body: ProductoCreate,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    service = ProductoService(SQLAlchemyProductoRepository(db), db)
    return service.crear(
        body.nombre,
        body.descripcion,
        body.categoria_id,
        body.imagen,
        body.precio,
        body.stock,
    ).to_dict()


@router.get("/{producto_id}")
def obtener(
    producto_id: str,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    service = ProductoService(SQLAlchemyProductoRepository(db), db)
    return service.obtener(producto_id).to_dict()


@router.put("/{producto_id}")
def actualizar(
    producto_id: str,
    body: ProductoUpdate,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    service = ProductoService(SQLAlchemyProductoRepository(db), db)
    return service.actualizar(
        producto_id,
        body.nombre,
        body.descripcion,
        body.categoria_id,
        body.imagen,
        body.precio,
        body.stock,
    ).to_dict()


@router.patch("/{producto_id}/estado")
def cambiar_estado(
    producto_id: str,
    body: EstadoRequest,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    service = ProductoService(SQLAlchemyProductoRepository(db), db)
    return service.cambiar_estado(producto_id, body.estado).to_dict()
