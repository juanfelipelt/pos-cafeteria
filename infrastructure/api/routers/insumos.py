from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.schemas.insumo import (
    InsumoCreate,
    InsumoEstadoRequest,
    InsumoUpdate,
)
from application.services.insumo_service import InsumoService
from database import get_session
from domain.entities.usuario import Usuario
from infrastructure.api.dependencies import get_current_user, require_admin
from infrastructure.repositories.insumo_repository import (
    SQLAlchemyInsumoRepository,
)
from infrastructure.repositories.receta_repository import (
    SQLAlchemyRecetaRepository,
)

router = APIRouter(prefix="/insumos", tags=["insumos"])


def _build_service(db: Session) -> InsumoService:
    return InsumoService(
        SQLAlchemyInsumoRepository(db), SQLAlchemyRecetaRepository(db), db
    )


@router.get("")
def listar(
    filtro: str | None = None,
    solo_activos: bool = False,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    return [
        i.to_dict()
        for i in _build_service(db).listar(filtro, solo_activos)
    ]


@router.post("")
def crear(
    body: InsumoCreate,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    return _build_service(db).crear(
        body.nombre,
        body.unidad,
        body.stock,
        body.costo_unitario,
        body.proveedor_id,
    ).to_dict()


@router.get("/{insumo_id}")
def obtener(
    insumo_id: str,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    return _build_service(db).obtener(insumo_id).to_dict()


@router.put("/{insumo_id}")
def actualizar(
    insumo_id: str,
    body: InsumoUpdate,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    return _build_service(db).actualizar(
        insumo_id,
        body.nombre,
        body.unidad,
        body.stock,
        body.costo_unitario,
        body.proveedor_id,
    ).to_dict()


@router.patch("/{insumo_id}/estado")
def cambiar_estado(
    insumo_id: str,
    body: InsumoEstadoRequest,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    return _build_service(db).cambiar_estado(insumo_id, body.estado).to_dict()


@router.delete("/{insumo_id}")
def eliminar(
    insumo_id: str,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    _build_service(db).eliminar(insumo_id)
    return {"detail": "Insumo eliminado."}
