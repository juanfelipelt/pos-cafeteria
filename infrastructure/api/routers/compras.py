from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.schemas.compra import CompraCreate
from application.services.compra_service import CompraService
from database import get_session
from domain.entities.usuario import Usuario
from infrastructure.api.dependencies import get_current_user, require_admin
from infrastructure.repositories.compra_repository import SQLAlchemyCompraRepository
from infrastructure.repositories.insumo_repository import (
    SQLAlchemyInsumoRepository,
)
from infrastructure.repositories.producto_repository import (
    SQLAlchemyProductoRepository,
)

router = APIRouter(prefix="/compras", tags=["compras"])


def _build_service(db: Session) -> CompraService:
    return CompraService(
        SQLAlchemyCompraRepository(db),
        SQLAlchemyProductoRepository(db),
        SQLAlchemyInsumoRepository(db),
        db,
    )


@router.post("")
def crear(
    body: CompraCreate,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    items = [
        {
            "tipo": i.tipo,
            "producto_id": i.producto_id,
            "insumo_id": i.insumo_id,
            "cantidad": i.cantidad,
            "precio_unitario": i.precio_unitario,
        }
        for i in body.items
    ]
    return _build_service(db).crear(body.proveedor_id, items).to_dict()


@router.get("")
def listar(
    desde: datetime | None = None,
    hasta: datetime | None = None,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    return [c.to_dict() for c in _build_service(db).listar(desde, hasta)]


@router.get("/{compra_id}")
def obtener(
    compra_id: str,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    return _build_service(db).obtener(compra_id).to_dict()


@router.post("/{compra_id}/anular")
def anular(
    compra_id: str,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    return _build_service(db).anular(compra_id).to_dict()


@router.delete("/{compra_id}")
def eliminar(
    compra_id: str,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    _build_service(db).eliminar(compra_id)
    return {"detail": "Compra eliminada."}
