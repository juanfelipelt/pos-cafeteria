"""
Router de costos fijos.

Recurso que expone: los costos que NO dependen de cuánto se venda (por
ejemplo: arriendo, servicios, nómina). Se usan en el costeo para repartir
esos gastos entre las ventas o los productos.

Prefijo base de las rutas: `/costos-fijos`

Endpoints:
- GET    /costos-fijos            -> lista costos fijos (filtro opcional de activos).
- POST   /costos-fijos            -> crea un costo fijo (solo admin).
- GET    /costos-fijos/{id}       -> obtiene un costo fijo por id.
- PUT    /costos-fijos/{id}       -> actualiza un costo fijo (solo admin).
- DELETE /costos-fijos/{id}       -> elimina un costo fijo (solo admin).
"""

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

# Router con prefijo "/costos-fijos".
router = APIRouter(prefix="/costos-fijos", tags=["costos-fijos"])


def _build_service(db: Session) -> CostoFijoService:
    """
    Función auxiliar que arma el servicio de costos fijos.

    Parámetros:
        db: Sesión de base de datos.

    Respuesta:
        Una instancia lista de `CostoFijoService`.
    """
    return CostoFijoService(SQLAlchemyCostoFijoRepository(db), db)


@router.get("")
def listar(
    solo_activos: bool = False,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    """
    Lista los costos fijos.

    Parámetros:
        solo_activos: Si es True, devuelve únicamente los que están activos.
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        Lista de costos fijos como dict.

    Nivel de acceso:
        Usuario autenticado.
    """
    return [c.to_dict() for c in _build_service(db).listar(solo_activos)]


@router.post("")
def crear(
    body: CostoFijoCreate,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    """
    Crea un nuevo costo fijo.

    Parámetros:
        body: Nombre y monto del costo fijo.
        _: Exige rol administrador.
        db: Sesión de base de datos.

    Respuesta:
        El costo fijo creado como dict.

    Nivel de acceso:
        Solo administradores.
    """
    return _build_service(db).crear(body.nombre, body.monto).to_dict()


@router.get("/{costo_id}")
def obtener(
    costo_id: str,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    """
    Obtiene un costo fijo por su identificador.

    Parámetros:
        costo_id: Id del costo fijo.
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        El costo fijo como dict.

    Nivel de acceso:
        Usuario autenticado.
    """
    return _build_service(db).obtener(costo_id).to_dict()


@router.put("/{costo_id}")
def actualizar(
    costo_id: str,
    body: CostoFijoUpdate,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    """
    Actualiza un costo fijo.

    Parámetros:
        costo_id: Id del costo a modificar.
        body: Nuevos valores (nombre, monto, activo).
        _: Exige rol administrador.
        db: Sesión de base de datos.

    Respuesta:
        El costo fijo actualizado como dict.

    Nivel de acceso:
        Solo administradores.
    """
    # Se permite activar o desactivar el costo con el campo `activo`.
    return _build_service(db).actualizar(
        costo_id, body.nombre, body.monto, body.activo
    ).to_dict()


@router.delete("/{costo_id}")
def eliminar(
    costo_id: str,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    """
    Elimina un costo fijo.

    Parámetros:
        costo_id: Id del costo a eliminar.
        _: Exige rol administrador.
        db: Sesión de base de datos.

    Respuesta:
        Mensaje de confirmación.

    Nivel de acceso:
        Solo administradores.
    """
    _build_service(db).eliminar(costo_id)
    return {"detail": "Costo fijo eliminado."}
