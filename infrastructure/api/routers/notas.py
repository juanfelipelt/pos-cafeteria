"""
Router de notas.

Recurso que expone: notas o mensajes internos (tipo tablero o post-it) con
destinatario, prioridad y estado (hecha/archivada). Sirven para la
comunicación entre el personal.

Prefijo base de las rutas: `/notas`

Endpoints:
- GET    /notas          -> lista notas (filtros por destinatario, tipo y archivadas).
- GET    /notas/resumen  -> conteo/resumen de notas.
- POST   /notas          -> crea una nota (el autor es el usuario conectado).
- PATCH  /notas/{id}     -> actualiza una nota.
- DELETE /notas/{id}     -> elimina una nota.

Nivel de acceso: usuario autenticado. En crear/editar/eliminar, el servicio
valida los permisos según el usuario (por ejemplo, quién puede modificar).
"""

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

# Router con prefijo "/notas".
router = APIRouter(prefix="/notas", tags=["notas"])


def _build_service(db: Session) -> NotaService:
    """
    Función auxiliar que arma el servicio de notas.

    Parámetros:
        db: Sesión de base de datos.

    Respuesta:
        Una instancia lista de `NotaService`.
    """
    return NotaService(SQLAlchemyNotaRepository(db), db)


@router.get("")
def listar(
    destinatario: str | None = None,
    tipo: str | None = None,
    incluir_archivadas: bool = False,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    """
    Lista las notas.

    Parámetros:
        destinatario: Filtrar por destinatario (opcional).
        tipo: Filtrar por tipo de nota (opcional).
        incluir_archivadas: Si es True, incluye también las archivadas.
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        Lista de notas como dict.

    Nivel de acceso:
        Usuario autenticado.
    """
    return [
        n.to_dict()
        for n in _build_service(db).listar(destinatario, tipo, incluir_archivadas)
    ]


@router.get("/resumen")
def resumen(
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    """
    Devuelve un resumen (por ejemplo, conteos) de las notas.

    Parámetros:
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        Estructura con totales/agrupaciones de notas.

    Nivel de acceso:
        Usuario autenticado.
    """
    return _build_service(db).resumen()


@router.post("")
def crear(
    body: NotaCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    Crea una nueva nota.

    Parámetros:
        body: Texto, tipo, destinatario y prioridad de la nota.
        usuario: Usuario autenticado, que será el autor.
        db: Sesión de base de datos.

    Respuesta:
        La nota creada como dict.

    Nivel de acceso:
        Usuario autenticado.
    """
    # Pasamos el usuario como autor de la nota.
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
    """
    Actualiza parcialmente una nota.

    Se usa PATCH porque se pueden modificar solo algunos campos (texto, tipo,
    destinatario, prioridad, hecho o archivada).

    Parámetros:
        nota_id: Id de la nota a modificar.
        body: Campos a actualizar (los no enviados se dejan igual).
        usuario: Usuario autenticado (se valida que tenga permiso).
        db: Sesión de base de datos.

    Respuesta:
        La nota actualizada como dict.

    Nivel de acceso:
        Usuario autenticado con permiso sobre la nota.
    """
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
    """
    Elimina una nota.

    Parámetros:
        nota_id: Id de la nota a eliminar.
        usuario: Usuario autenticado (se valida que tenga permiso).
        db: Sesión de base de datos.

    Respuesta:
        Mensaje de confirmación.

    Nivel de acceso:
        Usuario autenticado con permiso sobre la nota.
    """
    _build_service(db).eliminar(nota_id, usuario)
    return {"detail": "Nota eliminada."}
