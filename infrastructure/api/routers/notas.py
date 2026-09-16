from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.schemas.nota import NotaCreate, NotaUpdate
from application.services.nota_service import NotaService
from database import get_session
from domain.entities.usuario import Usuario
from infrastructure.api.dependencies import get_current_user
from infrastructure.repositories.nota_repository import (
    SQLAlchemyNotaRepository,
)

router = APIRouter(prefix="/notas", tags=["notas"])


def _build_service(db: Session) -> NotaService:
    return NotaService(SQLAlchemyNotaRepository(db), db)


@router.get("")
def listar(
    destinatario: str | None = None,
    tipo: str | None = None,
    incluir_archivadas: bool = False,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    return [
        n.to_dict()
        for n in _build_service(db).listar(destinatario, tipo, incluir_archivadas)
    ]


@router.get("/resumen")
def resumen(
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    return _build_service(db).resumen()


@router.post("")
def crear(
    body: NotaCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    return _build_service(db).crear(
        body.texto,
        body.tipo,
        body.destinatario,
        body.prioridad,
        usuario,
    ).to_dict()


@router.patch("/{nota_id}")
def actualizar(
    nota_id: str,
    body: NotaUpdate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    return _build_service(db).actualizar(
        nota_id,
        usuario,
        texto=body.texto,
        tipo=body.tipo,
        destinatario=body.destinatario,
        prioridad=body.prioridad,
        hecho=body.hecho,
        archivada=body.archivada,
    ).to_dict()


@router.delete("/{nota_id}")
def eliminar(
    nota_id: str,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    _build_service(db).eliminar(nota_id, usuario)
    return {"detail": "Nota eliminada."}
