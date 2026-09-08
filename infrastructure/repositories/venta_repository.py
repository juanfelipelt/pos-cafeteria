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
    detalles = [
        DetalleVenta(
            id=d.id,
            producto_id=d.producto_id,
            nombre_producto=d.nombre_producto,
            cantidad=d.cantidad,
            precio_unitario=d.precio_unitario,
        )
        for d in m.detalles
    ]
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
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: str) -> Venta | None:
        m = self.session.get(VentaModel, id)
        return _to_entity(m) if m else None

    def list(
        self, desde: datetime | None = None, hasta: datetime | None = None
    ) -> list[Venta]:
        q = self.session.query(VentaModel).order_by(VentaModel.fecha.desc())
        if desde:
            q = q.filter(VentaModel.fecha >= desde)
        if hasta:
            q = q.filter(VentaModel.fecha <= hasta)
        return [_to_entity(m) for m in q.all()]

    def add(self, venta: Venta) -> Venta:
        m = VentaModel(
            id=venta.id,
            usuario_id=venta.usuario_id,
            fecha=venta.fecha,
            anulada=venta.anulada,
        )
        from infrastructure.models.detalle_venta import DetalleVentaModel

        m.detalles = [
            DetalleVentaModel(
                id=d.id,
                producto_id=d.producto_id,
                nombre_producto=d.nombre_producto,
                cantidad=d.cantidad,
                precio_unitario=d.precio_unitario,
            )
            for d in venta.detalles
        ]
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
        m = self.session.get(VentaModel, venta.id)
        m.anulada = venta.anulada
        m.usuario_id = venta.usuario_id

        existing_ids = {p.id for p in m.pagos}
        for p in venta.pagos:
            if p.id not in existing_ids:
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
        m = self.session.get(VentaModel, id)
        if m is not None:
            self.session.delete(m)
            self.session.flush()
