"""Repositorio SQLAlchemy para las ventas.

Implementa `VentaRepository` del dominio sobre las tablas `ventas`, `detalle_ventas`
y `pagos`. Al agregar una venta se guardan sus líneas y sus pagos; al
actualizarla solo se agregan los pagos nuevos (sin duplicar los existentes).
"""

from __future__ import annotations
from datetime import datetime

from sqlalchemy.orm import Session

from domain.entities.detalle_venta import DetalleVenta
from domain.entities.enums import MetodoPago
from domain.entities.pago import Pago
from domain.entities.venta import Venta
from domain.repositories.venta_repository import VentaRepository
from infrastructure.models.venta import VentaModel
from infrastructure.models.pago import PagoModel


def _to_entity(m: VentaModel) -> Venta:
    """Convierte un `VentaModel` (con detalles y pagos) en la entidad `Venta`.

    El método de pago se guarda como texto en la BD y aquí se transforma al
    enum `MetodoPago`.
    """
    # Líneas de la venta (productos vendidos).
    detalles = [
        DetalleVenta(
            id=d.id,
            producto_id=d.producto_id,
            nombre_producto=d.nombre_producto,
            cantidad=d.cantidad,
            precio_unitario=d.precio_unitario,
            costo_unitario=d.costo_unitario,
        )
        for d in m.detalles
    ]
    # Pagos aplicados a la venta (puede haber más de uno).
    pagos = [
        Pago(
            id=p.id,
            monto=p.monto,
            metodo=MetodoPago(p.metodo),
            fecha=p.fecha,
            referencia=p.referencia,
        )
        for p in m.pagos
    ]
    return Venta(
        id=m.id,
        usuario_id=m.usuario_id,
        fecha=m.fecha,
        detalles=detalles,
        pagos=pagos,
        anulada=m.anulada,
    )


class SQLAlchemyVentaRepository(VentaRepository):
    """Implementación concreta de `VentaRepository` con SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: str) -> Venta | None:
        """Busca una venta por id (con detalles y pagos). None si no existe."""
        m = self.session.get(VentaModel, id)
        return _to_entity(m) if m else None

    def list(
        self, desde: datetime | None = None, hasta: datetime | None = None
    ) -> list[Venta]:
        """Lista ventas de la más reciente a la más antigua.

        `desde` y `hasta` son filtros opcionales por rango de fechas.
        """
        # Orden descendente por fecha (las últimas ventas primero).
        q = self.session.query(VentaModel).order_by(VentaModel.fecha.desc())
        if desde:
            q = q.filter(VentaModel.fecha >= desde)
        if hasta:
            q = q.filter(VentaModel.fecha <= hasta)
        return [_to_entity(m) for m in q.all()]

    def add(self, venta: Venta) -> Venta:
        """Registra una nueva venta con sus líneas de detalle y sus pagos."""
        m = VentaModel(
            id=venta.id,
            usuario_id=venta.usuario_id,
            fecha=venta.fecha,
            anulada=venta.anulada,
        )
        # Import local para evitar dependencias circulares en el módulo.
        from infrastructure.models.detalle_venta import DetalleVentaModel

        # Construimos las líneas (detalles) de la venta.
        m.detalles = [
            DetalleVentaModel(
                id=d.id,
                producto_id=d.producto_id,
                nombre_producto=d.nombre_producto,
                cantidad=d.cantidad,
                precio_unitario=d.precio_unitario,
                costo_unitario=d.costo_unitario,
            )
            for d in venta.detalles
        ]
        # Construimos los pagos (el enum se guarda como texto).
        m.pagos = [
            PagoModel(
                id=p.id,
                monto=p.monto,
                metodo=p.metodo.value,
                fecha=p.fecha,
                referencia=p.referencia,
            )
            for p in venta.pagos
        ]
        self.session.add(m)
        self.session.flush()
        return venta

    def update(self, venta: Venta) -> Venta:
        """Actualiza una venta y agrega solo los pagos que aún no existen."""
        m = self.session.get(VentaModel, venta.id)
        m.anulada = venta.anulada
        m.usuario_id = venta.usuario_id

        # Ids de los pagos que ya están guardados (para no duplicarlos).
        existing_ids = {p.id for p in m.pagos}
        for p in venta.pagos:
            if p.id not in existing_ids:
                # Es un pago nuevo: se agrega a la relación.
                m.pagos.append(
                    PagoModel(
                        id=p.id,
                        monto=p.monto,
                        metodo=p.metodo.value,
                        fecha=p.fecha,
                        referencia=p.referencia,
                    )
                )
        self.session.flush()
        return venta

    def delete(self, id: str) -> None:
        """Elimina una venta si existe (detalles y pagos caen por cascada)."""
        m = self.session.get(VentaModel, id)
        if m is not None:
            self.session.delete(m)
            self.session.flush()
