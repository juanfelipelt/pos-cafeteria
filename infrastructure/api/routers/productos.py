"""
Router de productos.

Recurso que expone: el catálogo de productos que se venden (platos, bebidas,
etc.) y la receta de cada producto (qué insumos/componentes lo componen y en
qué cantidades).

Prefijo base de las rutas: `/productos`

Endpoints:
- GET    /productos                    -> lista productos (filtros).
- POST   /productos                    -> crea un producto (solo admin).
- GET    /productos/{id}               -> obtiene un producto por id.
- PUT    /productos/{id}               -> actualiza un producto (solo admin).
- PATCH  /productos/{id}/estado        -> activa/desactiva un producto (solo admin).
- GET    /productos/{id}/receta        -> obtiene la receta del producto.
- PUT    /productos/{id}/receta        -> define la receta del producto (solo admin).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.schemas.producto import EstadoRequest, ProductoCreate, ProductoUpdate
from application.schemas.receta import RecetaUpdate
from application.services.producto_service import ProductoService
from application.services.receta_service import RecetaService
from database import get_session
from infrastructure.api.dependencies import get_current_user, require_admin
from infrastructure.repositories.insumo_repository import (
    SQLAlchemyInsumoRepository,
)
from infrastructure.repositories.producto_repository import (
    SQLAlchemyProductoRepository,
)
from infrastructure.repositories.receta_repository import (
    SQLAlchemyRecetaRepository,
)

# Router con prefijo "/productos".
router = APIRouter(prefix="/productos", tags=["productos"])


def _receta_service(db: Session) -> RecetaService:
    """
    Función auxiliar que arma el servicio de recetas.

    Una receta relaciona un producto con insumos (o con otros productos como
    componentes), por eso el servicio necesita esos repositorios.

    Parámetros:
        db: Sesión de base de datos.

    Respuesta:
        Una instancia lista de `RecetaService`.
    """
    return RecetaService(
        SQLAlchemyRecetaRepository(db),
        SQLAlchemyProductoRepository(db),
        SQLAlchemyInsumoRepository(db),
        db,
    )


@router.get("")
def listar(
    filtro: str | None = None,
    categoria_id: str | None = None,
    solo_activos: bool = False,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    """
    Lista los productos del catálogo.

    Parámetros:
        filtro: Texto de búsqueda por nombre (opcional).
        categoria_id: Filtrar por categoría (opcional).
        solo_activos: Si es True, oculta los inactivos.
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        Lista de productos como dict.

    Nivel de acceso:
        Usuario autenticado.
    """
    service = ProductoService(SQLAlchemyProductoRepository(db), db)
    return [p.to_dict() for p in service.listar(filtro, categoria_id, solo_activos)]


@router.post("")
def crear(
    body: ProductoCreate,
    db: Session = Depends(get_session),
    _=Depends(require_admin),
):
    """
    Crea un nuevo producto.

    Parámetros:
        body: Datos del producto (nombre, descripción, categoría, imagen,
              precio, stock y tipo).
        db: Sesión de base de datos.
        _: Exige rol administrador.

    Respuesta:
        El producto creado como dict.

    Nivel de acceso:
        Solo administradores.
    """
    service = ProductoService(SQLAlchemyProductoRepository(db), db)
    return service.crear(
        body.nombre,
        body.descripcion,
        body.categoria_id,
        body.imagen,
        body.precio,
        body.stock,
        body.tipo,
    ).to_dict()


@router.get("/{producto_id}")
def obtener(
    producto_id: str,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    """
    Obtiene un producto por su identificador.

    Parámetros:
        producto_id: Id del producto.
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        El producto como dict.

    Nivel de acceso:
        Usuario autenticado.
    """
    service = ProductoService(SQLAlchemyProductoRepository(db), db)
    return service.obtener(producto_id).to_dict()


@router.put("/{producto_id}")
def actualizar(
    producto_id: str,
    body: ProductoUpdate,
    db: Session = Depends(get_session),
    _=Depends(require_admin),
):
    """
    Actualiza un producto existente.

    Parámetros:
        producto_id: Id del producto a modificar.
        body: Nuevos valores del producto.
        db: Sesión de base de datos.
        _: Exige rol administrador.

    Respuesta:
        El producto actualizado como dict.

    Nivel de acceso:
        Solo administradores.
    """
    service = ProductoService(SQLAlchemyProductoRepository(db), db)
    return service.actualizar(
        producto_id,
        body.nombre,
        body.descripcion,
        body.categoria_id,
        body.imagen,
        body.precio,
        body.stock,
        body.tipo,
    ).to_dict()


@router.patch("/{producto_id}/estado")
def cambiar_estado(
    producto_id: str,
    body: EstadoRequest,
    db: Session = Depends(get_session),
    _=Depends(require_admin),
):
    """
    Cambia el estado (activo/inactivo) de un producto.

    Se usa PATCH porque solo cambiamos un campo del recurso.

    Parámetros:
        producto_id: Id del producto.
        body: Nuevo estado booleano.
        db: Sesión de base de datos.
        _: Exige rol administrador.

    Respuesta:
        El producto con su estado actualizado como dict.

    Nivel de acceso:
        Solo administradores.
    """
    service = ProductoService(SQLAlchemyProductoRepository(db), db)
    return service.cambiar_estado(producto_id, body.estado).to_dict()


@router.get("/{producto_id}/receta")
def obtener_receta(
    producto_id: str,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    """
    Obtiene la receta de un producto.

    Parámetros:
        producto_id: Id del producto.
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        La receta (lista de componentes y cantidades).

    Nivel de acceso:
        Usuario autenticado.
    """
    # El servicio de recetas devuelve la estructura ya preparada.
    return _receta_service(db).obtener(producto_id)


@router.put("/{producto_id}/receta")
def establecer_receta(
    producto_id: str,
    body: RecetaUpdate,
    db: Session = Depends(get_session),
    _=Depends(require_admin),
):
    """
    Define (crea o reemplaza) la receta de un producto.

    Parámetros:
        producto_id: Id del producto.
        body: Lista de items de la receta (tipo, insumo o componente,
              cantidad).
        db: Sesión de base de datos.
        _: Exige rol administrador.

    Respuesta:
        La receta guardada.

    Nivel de acceso:
        Solo administradores.
    """
    # Normalizamos cada item a un diccionario simple para el servicio.
    items = [
        {
            "tipo": i.tipo,
            "insumo_id": i.insumo_id,
            "componente_producto_id": i.componente_producto_id,
            "cantidad": i.cantidad,
        }
        for i in body.items
    ]
    return _receta_service(db).establecer(producto_id, items)
