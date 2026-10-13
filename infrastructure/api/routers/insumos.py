"""
Router de insumos (materias primas).

Recurso que expone: los insumos o ingredientes que se usan para preparar
productos (por ejemplo: harina, queso, carne). Tienen stock, unidad de medida,
costo unitario y proveedor.

Prefijo base de las rutas: `/insumos`

Endpoints:
- GET    /insumos                -> lista insumos (filtro y solo-activos).
- POST   /insumos                -> crea un insumo (solo admin).
- GET    /insumos/{id}           -> obtiene un insumo por id.
- PUT    /insumos/{id}           -> actualiza un insumo (solo admin).
- PATCH  /insumos/{id}/estado    -> activa/desactiva un insumo (solo admin).
- DELETE /insumos/{id}           -> elimina un insumo (solo admin).
"""

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

# Router con prefijo "/insumos".
router = APIRouter(prefix="/insumos", tags=["insumos"])


def _build_service(db: Session) -> InsumoService:
    """
    Función auxiliar que arma el servicio de insumos.

    Incluye el repositorio de recetas porque un insumo puede estar siendo
    usado en recetas: al eliminar o modificar hay que poder comprobarlo.

    Parámetros:
        db: Sesión de base de datos.

    Respuesta:
        Una instancia lista de `InsumoService`.
    """
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
    """
    Lista los insumos registrados.

    Parámetros:
        filtro: Texto para buscar por nombre (opcional).
        solo_activos: Si es True, oculta los inactivos.
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        Lista de insumos como dict.

    Nivel de acceso:
        Usuario autenticado.
    """
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
    """
    Crea un nuevo insumo.

    Parámetros:
        body: Nombre, unidad, stock inicial, costo unitario y proveedor.
        _: Exige rol administrador.
        db: Sesión de base de datos.

    Respuesta:
        El insumo creado como dict.

    Nivel de acceso:
        Solo administradores.
    """
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
    """
    Obtiene un insumo por su identificador.

    Parámetros:
        insumo_id: Id del insumo.
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        El insumo como dict.

    Nivel de acceso:
        Usuario autenticado.
    """
    return _build_service(db).obtener(insumo_id).to_dict()


@router.put("/{insumo_id}")
def actualizar(
    insumo_id: str,
    body: InsumoUpdate,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    """
    Actualiza los datos de un insumo.

    Parámetros:
        insumo_id: Id del insumo a modificar.
        body: Nuevos valores del insumo.
        _: Exige rol administrador.
        db: Sesión de base de datos.

    Respuesta:
        El insumo actualizado como dict.

    Nivel de acceso:
        Solo administradores.
    """
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
    """
    Cambia el estado (activo/inactivo) de un insumo.

    Se usa PATCH porque solo modificamos una parte del recurso (su estado),
    no todos sus campos.

    Parámetros:
        insumo_id: Id del insumo.
        body: Nuevo estado booleano.
        _: Exige rol administrador.
        db: Sesión de base de datos.

    Respuesta:
        El insumo con su estado actualizado como dict.

    Nivel de acceso:
        Solo administradores.
    """
    return _build_service(db).cambiar_estado(insumo_id, body.estado).to_dict()


@router.delete("/{insumo_id}")
def eliminar(
    insumo_id: str,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    """
    Elimina un insumo.

    Parámetros:
        insumo_id: Id del insumo a eliminar.
        _: Exige rol administrador.
        db: Sesión de base de datos.

    Respuesta:
        Mensaje de confirmación.

    Nivel de acceso:
        Solo administradores.
    """
    _build_service(db).eliminar(insumo_id)
    return {"detail": "Insumo eliminado."}
