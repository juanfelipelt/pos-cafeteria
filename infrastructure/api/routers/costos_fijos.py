from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.schemas.costo_fijo import CostoFijoCreate, CostoFijoUpdate
from application.services.costo_fijo_service import CostoFijoService
from database import get_session
from domain.entities.usuario import Usuario
from infrastructure.api.dependencies import get_current_user, require_admin
from infrastructure.repositories.costo_fijo_repository import (
    SQLAlchemyCostoFijoRepository,
)

router = APIRouter(prefix="/costos-fijos", tags=["costos-fijos"])


def _build_service(db: Session) -> CostoFijoService:
    return CostoFijoService(SQLAlchemyCostoFijoRepository(db), db)


@router.get("")
def listar(
    solo_activos: bool = False,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    return [c.to_dict() for c in _build_service(db).listar(solo_activos)]


@router.post("")
def crear(
    body: CostoFijoCreate,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    return _build_service(db).crear(body.nombre, body.monto).to_dict()


@router.get("/{costo_id}")
def obtener(
    costo_id: str,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    return _build_service(db).obtener(costo_id).to_dict()


@router.put("/{costo_id}")
def actualizar(
    costo_id: str,
    body: CostoFijoUpdate,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    return _build_service(db).actualizar(
        costo_id, body.nombre, body.monto, body.activo
    ).to_dict()


@router.delete("/{costo_id}")
def eliminar(
    costo_id: str,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    _build_service(db).eliminar(costo_id)
    return {"detail": "Costo fijo eliminado."}
