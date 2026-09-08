from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from domain.repositories.reporte_repository import ReporteRepository
from infrastructure.models.venta import VentaModel
from infrastructure.models.detalle_venta import DetalleVentaModel

_PATRONES = {
    "dia": "%Y-%m-%d",
    "semana": "%Y-W%W",
    "mes": "%Y-%m",
    "año": "%Y",
    "year": "%Y",
}


class SQLAlchemyReporteRepository(ReporteRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def resumen(self, desde: datetime, hasta: datetime) -> dict:
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
            .scalar()
        )
        num_ventas = (
            self.session.query(func.count(VentaModel.id))
            .filter(
                VentaModel.anulada.is_(False),
                VentaModel.fecha >= desde,
                VentaModel.fecha <= hasta,
            )
            .scalar()
        )
        return {"total": float(total or 0.0), "num_ventas": int(num_ventas or 0)}

    def ventas_por_periodo(
        self, desde: datetime, hasta: datetime, agrupacion: str
    ) -> list[dict]:
        patron = _PATRONES.get(agrupacion)
        if patron is None:
            raise ValueError(f"Agrupación no válida: {agrupacion}")

        periodo = func.strftime(patron, VentaModel.fecha).label("periodo")
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
            .group_by(periodo)
            .order_by(periodo)
            .all()
        )
        return [
            {"periodo": r[0], "total": float(r[1]), "num_ventas": int(r[2])}
            for r in rows
        ]

    def top_productos(
        self, desde: datetime, hasta: datetime, limite: int
    ) -> list[dict]:
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
            .order_by(cantidad.desc())
            .limit(limite)
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
