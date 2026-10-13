"""Repositorio SQLAlchemy para reportes de ventas.

Implementa `ReporteRepository` del dominio con consultas de agregación sobre
las tablas `ventas` y `detalle_ventas` (totales, ventas por periodo y
productos más vendidos).

Nota importante: las funciones de fecha cambian según el motor de base de
datos (SQLite en desarrollo, PostgreSQL en producción), por eso `_PATRONES`
guarda el formato de fecha de cada motor y `_grupo_dialecto` detecta cuál está
en uso.
"""

from datetime import datetime

# `func` = funciones SQL (sum, count, strftime, to_char...).
from sqlalchemy import func
from sqlalchemy.orm import Session

from domain.repositories.reporte_repository import ReporteRepository
from infrastructure.models.venta import VentaModel
from infrastructure.models.detalle_venta import DetalleVentaModel

# Patrones de formato de fecha por dialecto/motor de base de datos.
# Cada agrupación ("hora", "dia", "semana", "mes", "año") tiene su formato.
_PATRONES = {
    "sqlite": {
        "hora": "%H",
        "dia": "%Y-%m-%d",
        "semana": "%Y-W%W",
        "mes": "%Y-%m",
        "año": "%Y",
        "year": "%Y",
    },
    "postgresql": {
        "hora": "HH24",
        "dia": "YYYY-MM-DD",
        "semana": 'IYYY"-W"IW',
        "mes": "YYYY-MM",
        "año": "YYYY",
        "year": "YYYY",
    },
}


def _grupo_dialecto(session: Session) -> str:
    """Devuelve "postgresql" o "sqlite" según el motor de la conexión actual."""
    nombre = session.get_bind().dialect.name
    return "postgresql" if nombre.startswith("postgres") else "sqlite"


class SQLAlchemyReporteRepository(ReporteRepository):
    """Implementación concreta de `ReporteRepository` con SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def resumen(self, desde: datetime, hasta: datetime) -> dict:
        """Devuelve el total vendido y la cantidad de ventas en un rango.

        Solo considera ventas NO anuladas dentro de [desde, hasta].
        """
        # Suma del valor de cada línea vendida en el periodo.
        total = (
            self.session.query(
                func.coalesce(
                    func.sum(
                        DetalleVentaModel.cantidad * DetalleVentaModel.precio_unitario
                    ),
                    0.0,
                )
            )
            .join(VentaModel, DetalleVentaModel.venta_id == VentaModel.id)
            .filter(
                VentaModel.anulada.is_(False),
                VentaModel.fecha >= desde,
                VentaModel.fecha <= hasta,
            )
            .scalar()  # Un único valor de retorno.
        )
        # Cuenta cuántas ventas (cabeceras) hay en el periodo.
        num_ventas = (
            self.session.query(func.count(VentaModel.id))
            .filter(
                VentaModel.anulada.is_(False),
                VentaModel.fecha >= desde,
                VentaModel.fecha <= hasta,
            )
            .scalar()
        )
        # Normalizamos a float/int y tratamos None como cero.
        return {"total": float(total or 0.0), "num_ventas": int(num_ventas or 0)}

    def ventas_por_periodo(
        self, desde: datetime, hasta: datetime, agrupacion: str
    ) -> list[dict]:
        """Agrupa las ventas por hora, día, semana, mes o año.

        `agrupacion` debe ser una clave válida de `_PATRONES`; si no, lanza
        ValueError.
        """
        grupo = _grupo_dialecto(self.session)  # "sqlite" o "postgresql".
        patron = _PATRONES[grupo].get(agrupacion)
        if patron is None:
            raise ValueError(f"Agrupación no válida: {agrupacion}")

        # Cada motor formatea la fecha distinto:
        # - PostgreSQL usa to_char(fecha, patron).
        # - SQLite usa strftime(patron, fecha).
        if grupo == "postgresql":
            periodo = func.to_char(VentaModel.fecha, patron).label("periodo")
        else:
            periodo = func.strftime(patron, VentaModel.fecha).label("periodo")
        # Total monetario y número de ventas distintas por periodo.
        total = func.coalesce(
            func.sum(DetalleVentaModel.cantidad * DetalleVentaModel.precio_unitario),
            0.0,
        )
        cantidad = func.count(func.distinct(VentaModel.id))

        rows = (
            self.session.query(periodo, total, cantidad)
            .join(VentaModel, DetalleVentaModel.venta_id == VentaModel.id)
            .filter(
                VentaModel.anulada.is_(False),
                VentaModel.fecha >= desde,
                VentaModel.fecha <= hasta,
            )
            .group_by(periodo)   # Un resultado por periodo.
            .order_by(periodo)   # En orden cronológico.
            .all()
        )
        # Convertimos cada fila en un diccionario listo para la API.
        return [
            {"periodo": r[0], "total": float(r[1]), "num_ventas": int(r[2])}
            for r in rows
        ]

    def top_productos(
        self, desde: datetime, hasta: datetime, limite: int
    ) -> list[dict]:
        """Devuelve los `limite` productos más vendidos en un rango de fechas."""
        # Cantidad total vendida y monto total por producto.
        cantidad = func.sum(DetalleVentaModel.cantidad)
        monto = func.sum(
            DetalleVentaModel.cantidad * DetalleVentaModel.precio_unitario
        )

        rows = (
            self.session.query(
                DetalleVentaModel.producto_id,
                DetalleVentaModel.nombre_producto,
                cantidad,
                monto,
            )
            .join(VentaModel, DetalleVentaModel.venta_id == VentaModel.id)
            .filter(
                VentaModel.anulada.is_(False),
                VentaModel.fecha >= desde,
                VentaModel.fecha <= hasta,
            )
            .group_by(
                DetalleVentaModel.producto_id, DetalleVentaModel.nombre_producto
            )
            .order_by(cantidad.desc())  # Los más vendidos primero.
            .limit(limite)              # Solo el top solicitado.
            .all()
        )
        return [
            {
                "producto_id": r[0],
                "nombre": r[1],
                "cantidad": int(r[2] or 0),
                "monto": float(r[3] or 0.0),
            }
            for r in rows
        ]
