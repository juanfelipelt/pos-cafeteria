"""
Router de categorías de productos.

Recurso que expone: las categorías que agrupan productos del menú
(por ejemplo: bebidas, postres, platos fuertes).

Prefijo base de las rutas: `/categorias`

Endpoints:
- GET    /categorias              -> lista todas las categorías.
- POST   /categorias              -> crea una categoría (solo admin).
- GET    /categorias/{id}         -> obtiene una categoría por su id.
- PUT    /categorias/{id}         -> actualiza una categoría (solo admin).

Todas las rutas (salvo las de escritura que exigen admin) requieren estar
autenticado.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.schemas.categoria import CategoriaCreate, CategoriaUpdate
from application.services.categoria_service import CategoriaService
from database import get_session
from infrastructure.api.dependencies import get_current_user, require_admin
from infrastructure.repositories.categoria_repository import (
    SQLAlchemyCategoriaRepository,
)

# Router con prefijo "/categorias" para agrupar los endpoints de este recurso.
router = APIRouter(prefix="/categorias", tags=["categorias"])


@router.get("")
def listar(db: Session = Depends(get_session), _=Depends(get_current_user)):
    """
    Lista todas las categorías existentes.

    Parámetros:
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        Lista de categorías en formato dict.

    Nivel de acceso:
        Usuario autenticado.
    """
    # Construimos el servicio con su repositorio y pedimos la lista.
    service = CategoriaService(SQLAlchemyCategoriaRepository(db), db)
    return [c.to_dict() for c in service.listar()]


@router.post("")
def crear(
    body: CategoriaCreate,
    db: Session = Depends(get_session),
    _=Depends(require_admin),
):
    """
    Crea una nueva categoría.

    Parámetros:
        body: Nombre y descripción de la categoría.
        db: Sesión de base de datos.
        _: Exige rol administrador.

    Respuesta:
        La categoría creada como dict.

    Nivel de acceso:
        Solo administradores.
    """
    # El servicio se encarga de validar y persistir la categoría.
    service = CategoriaService(SQLAlchemyCategoriaRepository(db), db)
    return service.crear(body.nombre, body.descripcion).to_dict()


@router.get("/{categoria_id}")
def obtener(
    categoria_id: str,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    """
    Obtiene una categoría por su identificador.

    Parámetros:
        categoria_id: Id de la categoría (parte de la URL).
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        La categoría encontrada como dict.

    Nivel de acceso:
        Usuario autenticado.
    """
    # Si no existe, el servicio lanza una excepción (404).
    service = CategoriaService(SQLAlchemyCategoriaRepository(db), db)
    return service.obtener(categoria_id).to_dict()


@router.put("/{categoria_id}")
def actualizar(
    categoria_id: str,
    body: CategoriaUpdate,
    db: Session = Depends(get_session),
    _=Depends(require_admin),
):
    """
    Actualiza una categoría existente.

    Parámetros:
        categoria_id: Id de la categoría a modificar.
        body: Nuevos valores de nombre y descripción.
        db: Sesión de base de datos.
        _: Exige rol administrador.

    Respuesta:
        La categoría actualizada como dict.

    Nivel de acceso:
        Solo administradores.
    """
    service = CategoriaService(SQLAlchemyCategoriaRepository(db), db)
    # Se actualizan únicamente los campos enviados.
    return service.actualizar(categoria_id, body.nombre, body.descripcion).to_dict()
