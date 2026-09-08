from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.schemas.categoria import CategoriaCreate, CategoriaUpdate
from application.services.categoria_service import CategoriaService
from database import get_session
from infrastructure.api.dependencies import get_current_user
from infrastructure.repositories.categoria_repository import (
    SQLAlchemyCategoriaRepository,
)

router = APIRouter(prefix="/categorias", tags=["categorias"])


@router.get("")
def listar(db: Session = Depends(get_session), _=Depends(get_current_user)):
    service = CategoriaService(SQLAlchemyCategoriaRepository(db), db)
    return [c.to_dict() for c in service.listar()]


@router.post("")
def crear(
    body: CategoriaCreate,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    service = CategoriaService(SQLAlchemyCategoriaRepository(db), db)
    return service.crear(body.nombre, body.descripcion).to_dict()


@router.get("/{categoria_id}")
def obtener(
    categoria_id: str,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    service = CategoriaService(SQLAlchemyCategoriaRepository(db), db)
    return service.obtener(categoria_id).to_dict()


@router.put("/{categoria_id}")
def actualizar(
    categoria_id: str,
    body: CategoriaUpdate,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    service = CategoriaService(SQLAlchemyCategoriaRepository(db), db)
    return service.actualizar(categoria_id, body.nombre, body.descripcion).to_dict()
