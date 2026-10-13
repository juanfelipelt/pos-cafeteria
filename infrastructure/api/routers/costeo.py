"""
Router de costeo.

Recurso que expone: cálculos de costos y análisis de rentabilidad. Aquí se
combinan productos, insumos, recetas, costos fijos, configuración y ventas
para saber cuánto cuesta producir y cuánto se gana.

Prefijo base de las rutas: `/costeo`

Endpoints:
- GET /costeo/productos -> detalle de costeo por producto.
- GET /costeo/resumen   -> resumen de costos/ganancias en un rango de fechas.

Nivel de acceso: solo administradores (es información sensible del negocio).
"""

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

# Router con prefijo "/costeo".
router = APIRouter(prefix="/costeo", tags=["costeo"])


def _build_service(db: Session) -> CosteoService:
    """
    Función auxiliar que arma el servicio de costeo.

    El costeo es el cálculo más "transversal" del sistema: necesita productos,
    insumos, recetas, costos fijos, configuración y ventas. Por eso esta
    función inyecta todos esos repositorios en el servicio en un solo lugar.

    Parámetros:
        db: Sesión de base de datos.

    Respuesta:
        Una instancia lista de `CosteoService`.
    """
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
    """
    Devuelve el costeo detallado de los productos.

    Parámetros:
        db: Sesión de base de datos.
        _: Exige rol administrador.

    Respuesta:
        Estructura con el costo (y datos asociados) de cada producto.

    Nivel de acceso:
        Solo administradores.
    """
    return _build_service(db).listar_productos()


@router.get("/resumen")
def resumen(
    desde: datetime,
    hasta: datetime,
    db: Session = Depends(get_session),
    _=Depends(require_admin),
):
    """
    Devuelve un resumen de costeo en un rango de fechas.

    Parámetros:
        desde: Fecha/hora inicial del análisis (obligatoria).
        hasta: Fecha/hora final del análisis (obligatoria).
        db: Sesión de base de datos.
        _: Exige rol administrador.

    Respuesta:
        Resumen de costos, ingresos y utilidad del periodo.

    Nivel de acceso:
        Solo administradores.
    """
    # El servicio cruza las fechas con ventas y costos para calcular el resumen.
    return _build_service(db).resumen(desde, hasta)
