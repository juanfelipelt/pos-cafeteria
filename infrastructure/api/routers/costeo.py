from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.services.costeo_service import CosteoService
from database import get_session
from infrastructure.api.dependencies import require_admin
from infrastructure.repositories.configuracion_repository import (
    SQLAlchemyConfiguracionRepository,
)
from infrastructure.repositories.costo_fijo_repository import (
    SQLAlchemyCostoFijoRepository,
)
from infrastructure.repositories.insumo_repository import (
    SQLAlchemyInsumoRepository,
)
from infrastructure.repositories.producto_repository import (
    SQLAlchemyProductoRepository,
)
from infrastructure.repositories.receta_repository import (
    SQLAlchemyRecetaRepository,
)
from infrastructure.repositories.venta_repository import SQLAlchemyVentaRepository

router = APIRouter(prefix="/costeo", tags=["costeo"])


def _build_service(db: Session) -> CosteoService:
    return CosteoService(
        SQLAlchemyProductoRepository(db),
        SQLAlchemyInsumoRepository(db),
        SQLAlchemyRecetaRepository(db),
        SQLAlchemyCostoFijoRepository(db),
        SQLAlchemyConfiguracionRepository(db),
        SQLAlchemyVentaRepository(db),
        db,
    )


@router.get("/productos")
def productos(
    db: Session = Depends(get_session),
    _=Depends(require_admin),
):
    return _build_service(db).listar_productos()


@router.get("/resumen")
def resumen(
    desde: datetime,
    hasta: datetime,
    db: Session = Depends(get_session),
    _=Depends(require_admin),
):
    return _build_service(db).resumen(desde, hasta)
