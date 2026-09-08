from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.schemas.producto import EstadoRequest
from application.schemas.proveedor import ProveedorCreate, ProveedorUpdate
from application.services.proveedor_service import ProveedorService
from database import get_session
from domain.entities.usuario import Usuario
from infrastructure.api.dependencies import get_current_user, require_admin
from infrastructure.repositories.compra_repository import SQLAlchemyCompraRepository
from infrastructure.repositories.proveedor_repository import (
    SQLAlchemyProveedorRepository,
)

router = APIRouter(prefix="/proveedores", tags=["proveedores"])


def _build_service(db: Session) -> ProveedorService:
    return ProveedorService(
        SQLAlchemyProveedorRepository(db), SQLAlchemyCompraRepository(db), db
    )


@router.get("")
def listar(
    filtro: str | None = None,
    solo_activos: bool = False,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    return [p.to_dict() for p in _build_service(db).listar(filtro, solo_activos)]


@router.post("")
def crear(
    body: ProveedorCreate,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    return _build_service(db).crear(
        body.nombre, body.contacto, body.telefono, body.email, body.direccion
    ).to_dict()


@router.get("/{proveedor_id}")
def obtener(
    proveedor_id: str,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    return _build_service(db).obtener(proveedor_id).to_dict()


@router.put("/{proveedor_id}")
def actualizar(
    proveedor_id: str,
    body: ProveedorUpdate,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    return _build_service(db).actualizar(
        proveedor_id,
        body.nombre,
        body.contacto,
        body.telefono,
        body.email,
        body.direccion,
    ).to_dict()


@router.patch("/{proveedor_id}/estado")
def cambiar_estado(
    proveedor_id: str,
    body: EstadoRequest,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    return _build_service(db).cambiar_estado(proveedor_id, body.estado).to_dict()


@router.delete("/{proveedor_id}")
def eliminar(
    proveedor_id: str,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    _build_service(db).eliminar(proveedor_id)
    return {"detail": "Proveedor eliminado."}
