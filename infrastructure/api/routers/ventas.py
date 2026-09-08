from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.schemas.venta import PagoCreate, VentaCreate
from application.services.venta_service import VentaService
from database import get_session
from domain.entities.usuario import Usuario
from infrastructure.api.dependencies import get_current_user, require_admin
from infrastructure.repositories.producto_repository import (
    SQLAlchemyProductoRepository,
)
from infrastructure.repositories.venta_repository import SQLAlchemyVentaRepository

router = APIRouter(prefix="/ventas", tags=["ventas"])


def _build_service(db: Session) -> VentaService:
    return VentaService(
        SQLAlchemyVentaRepository(db), SQLAlchemyProductoRepository(db), db
    )


@router.post("")
def crear(
    body: VentaCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    items = [{"producto_id": i.producto_id, "cantidad": i.cantidad} for i in body.items]
    pagos = [
        {"monto": p.monto, "metodo": p.metodo.value, "referencia": p.referencia}
        for p in body.pagos
    ]
    return _build_service(db).crear(items, pagos, usuario.id).to_dict()


@router.get("")
def listar(
    desde: datetime | None = None,
    hasta: datetime | None = None,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    return [v.to_dict() for v in _build_service(db).listar(desde, hasta)]


@router.get("/{venta_id}")
def obtener(
    venta_id: str,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    return _build_service(db).obtener(venta_id).to_dict()


@router.post("/{venta_id}/pagos")
def registrar_pago(
    venta_id: str,
    body: PagoCreate,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    return _build_service(db).registrar_pago(
        venta_id, body.monto, body.metodo.value, body.referencia
    ).to_dict()


@router.post("/{venta_id}/anular")
def anular(
    venta_id: str,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    return _build_service(db).anular(venta_id).to_dict()


@router.delete("/{venta_id}")
def eliminar(
    venta_id: str,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    _build_service(db).eliminar(venta_id)
    return {"detail": "Venta eliminada."}
