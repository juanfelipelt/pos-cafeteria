"""
Router de reportes.

Recurso que expone: consultas analíticas sobre las ventas y la actividad del
negocio (resúmenes, ventas por periodo, productos más vendidos, etc.). Son
solo de lectura: no crean ni modifican datos.

Prefijo base de las rutas: `/reportes`

Endpoints:
- GET /reportes/resumen        -> resumen general en un rango de fechas.
- GET /reportes/ventas         -> ventas agrupadas por periodo (solo admin).
- GET /reportes/actividad      -> actividad agrupada por hora/día/semana/mes.
- GET /reportes/top-productos  -> productos más vendidos (con un límite).
"""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from application.services.reporte_service import ReporteService
from database import get_session
from infrastructure.api.dependencies import get_current_user, require_admin
from infrastructure.repositories.reporte_repository import (
    SQLAlchemyReporteRepository,
)

# Router con prefijo "/reportes".
router = APIRouter(prefix="/reportes", tags=["reportes"])


@router.get("/resumen")
def resumen(
    desde: datetime,
    hasta: datetime,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    """
    Devuelve un resumen general de ventas en un rango de fechas.

    Parámetros:
        desde: Fecha/hora inicial (obligatoria).
        hasta: Fecha/hora final (obligatoria).
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        Resumen con totales del periodo.

    Nivel de acceso:
        Usuario autenticado.
    """
    return ReporteService(SQLAlchemyReporteRepository(db)).resumen(desde, hasta)


@router.get("/ventas")
def ventas_por_periodo(
    desde: datetime,
    hasta: datetime,
    agrupacion: str = "dia",
    db: Session = Depends(get_session),
    _=Depends(require_admin),
):
    """
    Devuelve las ventas agrupadas por periodo.

    Parámetros:
        desde: Fecha/hora inicial (obligatoria).
        hasta: Fecha/hora final (obligatoria).
        agrupacion: Unidad de agrupación ("dia" por defecto).
        db: Sesión de base de datos.
        _: Exige rol administrador.

    Respuesta:
        Serie de ventas agrupadas según la unidad elegida.

    Nivel de acceso:
        Solo administradores.
    """
    return ReporteService(SQLAlchemyReporteRepository(db)).ventas_por_periodo(
        desde, hasta, agrupacion
    )


@router.get("/actividad")
def actividad(
    desde: datetime,
    hasta: datetime,
    agrupacion: Literal["hora", "dia", "semana", "mes"] = "hora",
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    """
    Devuelve la actividad del negocio agrupada por periodo.

    Parámetros:
        desde: Fecha/hora inicial (obligatoria).
        hasta: Fecha/hora final (obligatoria).
        agrupacion: Solo admite "hora", "dia", "semana" o "mes" (por defecto
                    "hora"). El tipo `Literal` hace que FastAPI valide el valor
                    automáticamente.
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        Serie de actividad agrupada.

    Nivel de acceso:
        Usuario autenticado.
    """
    # Reutiliza la misma consulta de ventas por periodo con la agrupación dada.
    return ReporteService(SQLAlchemyReporteRepository(db)).ventas_por_periodo(
        desde, hasta, agrupacion
    )


@router.get("/top-productos")
def top_productos(
    desde: datetime,
    hasta: datetime,
    limite: int = 10,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    """
    Devuelve los productos más vendidos en un rango de fechas.

    Parámetros:
        desde: Fecha/hora inicial (obligatoria).
        hasta: Fecha/hora final (obligatoria).
        limite: Cuántos productos devolver (por defecto 10).
        db: Sesión de base de datos.
        _: Exige usuario autenticado.

    Respuesta:
        Lista con los productos más vendidos y sus cantidades/totales.

    Nivel de acceso:
        Usuario autenticado.
    """
    return ReporteService(SQLAlchemyReporteRepository(db)).top_productos(
        desde, hasta, limite
    )
