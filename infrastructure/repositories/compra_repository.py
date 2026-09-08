from datetime import datetime

from sqlalchemy.orm import Session

from domain.entities.compra import Compra
from domain.entities.detalle_compra import DetalleCompra
from domain.repositories.compra_repository import CompraRepository
from infrastructure.models.compra import CompraModel
from infrastructure.models.detalle_compra import DetalleCompraModel


def _to_entity(m: CompraModel) -> Compra:
    detalles = [
        DetalleCompra(
            id=d.id,
            producto_id=d.producto_id,
            nombre_producto=d.nombre_producto,
            cantidad=d.cantidad,
            precio_unitario=d.precio_unitario,
        )
        for d in m.detalles
    ]
    return Compra(
        id=m.id,
        proveedor_id=m.proveedor_id,
        fecha=m.fecha,
        detalles=detalles,
        anulada=m.anulada,
    )


class SQLAlchemyCompraRepository(CompraRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: str) -> Compra | None:
        m = self.session.get(CompraModel, id)
        return _to_entity(m) if m else None

    def list(
        self, desde: datetime | None = None, hasta: datetime | None = None
    ) -> list[Compra]:
        q = self.session.query(CompraModel).order_by(CompraModel.fecha.desc())
        if desde:
            q = q.filter(CompraModel.fecha >= desde)
        if hasta:
            q = q.filter(CompraModel.fecha <= hasta)
        return [_to_entity(m) for m in q.all()]

    def add(self, compra: Compra) -> Compra:
        m = CompraModel(
            id=compra.id,
            proveedor_id=compra.proveedor_id,
            fecha=compra.fecha,
            anulada=compra.anulada,
        )
        m.detalles = [
            DetalleCompraModel(
                id=d.id,
                producto_id=d.producto_id,
                nombre_producto=d.nombre_producto,
                cantidad=d.cantidad,
                precio_unitario=d.precio_unitario,
            )
            for d in compra.detalles
        ]
        self.session.add(m)
        self.session.flush()
        return compra

    def update(self, compra: Compra) -> Compra:
        m = self.session.get(CompraModel, compra.id)
        m.anulada = compra.anulada
        m.proveedor_id = compra.proveedor_id
        self.session.flush()
        return compra

    def has_for_proveedor(self, proveedor_id: str) -> bool:
        return (
            self.session.query(CompraModel)
            .filter(CompraModel.proveedor_id == proveedor_id)
            .first()
            is not None
        )
