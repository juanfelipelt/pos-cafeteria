from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from domain.entities.compra import Compra
from domain.entities.detalle_compra import DetalleCompra
from domain.entities.enums import TipoLineaCompra
from domain.repositories.compra_repository import CompraRepository
from infrastructure.models.compra import CompraModel
from infrastructure.models.detalle_compra import DetalleCompraModel


def _to_entity(m: CompraModel) -> Compra:
    detalles = [
        DetalleCompra(
            id=d.id,
            tipo=d.tipo,
            producto_id=d.producto_id or None,
            nombre_producto=d.nombre_producto or "",
            insumo_id=d.insumo_id or None,
            nombre_insumo=d.nombre_insumo or "",
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
                tipo=d.tipo,
                producto_id=d.producto_id or "",
                nombre_producto=d.nombre_producto or "",
                insumo_id=d.insumo_id,
                nombre_insumo=d.nombre_insumo or "",
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

    def set_detalles(self, compra_id: str, detalles: list[DetalleCompra]) -> None:
        self.session.query(DetalleCompraModel).filter(
            DetalleCompraModel.compra_id == compra_id
        ).delete(synchronize_session=False)
        for d in detalles:
            self.session.add(
                DetalleCompraModel(
                    id=d.id,
                    compra_id=compra_id,
                    tipo=d.tipo,
                    producto_id=d.producto_id or "",
                    nombre_producto=d.nombre_producto or "",
                    insumo_id=d.insumo_id,
                    nombre_insumo=d.nombre_insumo or "",
                    cantidad=d.cantidad,
                    precio_unitario=d.precio_unitario,
                )
            )
        self.session.flush()

    def has_for_proveedor(self, proveedor_id: str) -> bool:
        return (
            self.session.query(CompraModel)
            .filter(CompraModel.proveedor_id == proveedor_id)
            .first()
            is not None
        )

    def _suma(
        self,
        tipo: str,
        columna,
        valor: str,
        excluir_compra: str | None,
    ) -> tuple[float, float]:
        q = (
            self.session.query(
                func.coalesce(
                    func.sum(
                        DetalleCompraModel.cantidad
                        * DetalleCompraModel.precio_unitario
                    ),
                    0.0,
                ),
                func.coalesce(func.sum(DetalleCompraModel.cantidad), 0.0),
            )
            .join(CompraModel, DetalleCompraModel.compra_id == CompraModel.id)
            .filter(
                DetalleCompraModel.tipo == tipo,
                columna == valor,
                CompraModel.anulada.is_(False),
            )
        )
        if excluir_compra:
            q = q.filter(CompraModel.id != excluir_compra)
        total_valor, total_cantidad = q.one()
        return float(total_valor or 0.0), float(total_cantidad or 0.0)

    def suma_compras_insumo(
        self, insumo_id: str, excluir_compra: str | None = None
    ) -> tuple[float, float]:
        return self._suma(
            TipoLineaCompra.INSUMO.value,
            DetalleCompraModel.insumo_id,
            insumo_id,
            excluir_compra,
        )

    def suma_compras_producto(
        self, producto_id: str, excluir_compra: str | None = None
    ) -> tuple[float, float]:
        return self._suma(
            TipoLineaCompra.PRODUCTO.value,
            DetalleCompraModel.producto_id,
            producto_id,
            excluir_compra,
        )

    def delete(self, id: str) -> None:
        m = self.session.get(CompraModel, id)
        if m is not None:
            self.session.delete(m)
            self.session.flush()
