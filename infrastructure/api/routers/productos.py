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

router = APIRouter(prefix="/productos", tags=["productos"])


def _receta_service(db: Session) -> RecetaService:
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
    service = ProductoService(SQLAlchemyProductoRepository(db), db)
    return [p.to_dict() for p in service.listar(filtro, categoria_id, solo_activos)]


@router.post("")
def crear(
    body: ProductoCreate,
    db: Session = Depends(get_session),
    _=Depends(require_admin),
):
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
    service = ProductoService(SQLAlchemyProductoRepository(db), db)
    return service.obtener(producto_id).to_dict()


@router.put("/{producto_id}")
def actualizar(
    producto_id: str,
    body: ProductoUpdate,
    db: Session = Depends(get_session),
    _=Depends(require_admin),
):
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
    service = ProductoService(SQLAlchemyProductoRepository(db), db)
    return service.cambiar_estado(producto_id, body.estado).to_dict()


@router.get("/{producto_id}/receta")
def obtener_receta(
    producto_id: str,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    return _receta_service(db).obtener(producto_id)


@router.put("/{producto_id}/receta")
def establecer_receta(
    producto_id: str,
    body: RecetaUpdate,
    db: Session = Depends(get_session),
    _=Depends(require_admin),
):
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
