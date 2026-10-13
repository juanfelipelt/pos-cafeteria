"""
Router de proveedores.

Recurso que expone: las empresas o personas que abastecen de productos e
insumos al negocio (con sus datos de contacto e identificación).

Prefijo base de las rutas: `/proveedores`

Endpoints:
- GET    /proveedores                -> lista proveedores (filtros).
- POST   /proveedores                -> crea un proveedor (solo admin).
- GET    /proveedores/{id}           -> obtiene un proveedor por id.
- PUT    /proveedores/{id}           -> actualiza un proveedor (solo admin).
- PATCH  /proveedores/{id}/estado    -> activa/desactiva un proveedor (solo admin).
- DELETE /proveedores/{id}           -> elimina un proveedor (solo admin).
"""

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

# Router con prefijo "/proveedores".
router = APIRouter(prefix="/proveedores", tags=["proveedores"])


def _build_service(db: Session) -> ProveedorService:
    """
    Función auxiliar que arma el servicio de proveedores.

    Incluye el repositorio de compras porque, al eliminar un proveedor, hay
    que verificar si tiene compras asociadas.

    Parámetros:
        db: Sesión de base de datos.

    Respuesta:
        Una instancia lista de `ProveedorService`.
    """
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
    """
    Lista los proveedores.

    Parámetros:
        filtro: Texto de búsqueda por nombre (opcional).
        solo_activos: Si es True, oculta los inactivos.
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        Lista de proveedores como dict.

    Nivel de acceso:
        Usuario autenticado.
    """
    return [p.to_dict() for p in _build_service(db).listar(filtro, solo_activos)]


@router.post("")
def crear(
    body: ProveedorCreate,
    db: Session = Depends(get_session),
    _=Depends(require_admin),
):
    """
    Crea un nuevo proveedor.

    Parámetros:
        body: Datos de contacto e identificación del proveedor.
        db: Sesión de base de datos.
        _: Exige rol administrador.

    Respuesta:
        El proveedor creado como dict.

    Nivel de acceso:
        Solo administradores.
    """
    return _build_service(db).crear(
        body.nombre,
        body.contacto,
        body.telefono,
        body.email,
        body.direccion,
        body.tipo_identificacion,
        body.identificacion,
    ).to_dict()


@router.get("/{proveedor_id}")
def obtener(
    proveedor_id: str,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    """
    Obtiene un proveedor por su identificador.

    Parámetros:
        proveedor_id: Id del proveedor.
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        El proveedor como dict.

    Nivel de acceso:
        Usuario autenticado.
    """
    return _build_service(db).obtener(proveedor_id).to_dict()


@router.put("/{proveedor_id}")
def actualizar(
    proveedor_id: str,
    body: ProveedorUpdate,
    db: Session = Depends(get_session),
    _=Depends(require_admin),
):
    """
    Actualiza los datos de un proveedor.

    Parámetros:
        proveedor_id: Id del proveedor a modificar.
        body: Nuevos datos del proveedor.
        db: Sesión de base de datos.
        _: Exige rol administrador.

    Respuesta:
        El proveedor actualizado como dict.

    Nivel de acceso:
        Solo administradores.
    """
    return _build_service(db).actualizar(
        proveedor_id,
        body.nombre,
        body.contacto,
        body.telefono,
        body.email,
        body.direccion,
        body.tipo_identificacion,
        body.identificacion,
    ).to_dict()


@router.patch("/{proveedor_id}/estado")
def cambiar_estado(
    proveedor_id: str,
    body: EstadoRequest,
    db: Session = Depends(get_session),
    _=Depends(require_admin),
):
    """
    Cambia el estado (activo/inactivo) de un proveedor.

    Se usa PATCH porque solo cambiamos un campo del recurso.

    Parámetros:
        proveedor_id: Id del proveedor.
        body: Nuevo estado booleano.
        db: Sesión de base de datos.
        _: Exige rol administrador.

    Respuesta:
        El proveedor con su estado actualizado como dict.

    Nivel de acceso:
        Solo administradores.
    """
    return _build_service(db).cambiar_estado(proveedor_id, body.estado).to_dict()


@router.delete("/{proveedor_id}")
def eliminar(
    proveedor_id: str,
    _: Usuario = Depends(require_admin),
    db: Session = Depends(get_session),
):
    """
    Elimina un proveedor.

    Parámetros:
        proveedor_id: Id del proveedor a eliminar.
        _: Exige rol administrador.
        db: Sesión de base de datos.

    Respuesta:
        Mensaje de confirmación.

    Nivel de acceso:
        Solo administradores.
    """
    _build_service(db).eliminar(proveedor_id)
    return {"detail": "Proveedor eliminado."}
