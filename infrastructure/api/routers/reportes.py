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

router = APIRouter(prefix="/reportes", tags=["reportes"])


@router.get("/resumen")
def resumen(
    desde: datetime,
    hasta: datetime,
    db: Session = Depends(get_session),
    _=Depends(get_current_user),
):
    return ReporteService(SQLAlchemyReporteRepository(db)).resumen(desde, hasta)


@router.get("/ventas")
def ventas_por_periodo(
    desde: datetime,
    hasta: datetime,
    agrupacion: str = "dia",
    db: Session = Depends(get_session),
    _=Depends(require_admin),
):
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
    return ReporteService(SQLAlchemyReporteRepository(db)).top_productos(
        desde, hasta, limite
    )
