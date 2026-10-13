"""Repositorio SQLAlchemy para las compras.

Implementa `CompraRepository` del dominio usando las tablas `compras` y
`detalle_compras`. Incluye consultas de agregación (sumas) que sirven para
calcular costos: cuánto se ha comprado de un insumo o producto.
"""

from __future__ import annotations
from datetime import datetime

# `func` nos permite usar funciones SQL (suma, coalesce, etc.).
from sqlalchemy import func
from sqlalchemy.orm import Session

from domain.entities.compra import Compra
from domain.entities.detalle_compra import DetalleCompra
from domain.entities.enums import TipoLineaCompra
from domain.repositories.compra_repository import CompraRepository
from infrastructure.models.compra import CompraModel
from infrastructure.models.detalle_compra import DetalleCompraModel


def _to_entity(m: CompraModel) -> Compra:
    """Convierte un `CompraModel` (con sus detalles) en la entidad `Compra`."""
    # Transformamos cada línea ORM en su entidad de dominio equivalente.
    # Nota: los campos opcionales se normalizan con `or None` / `or ""`.
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
    """Implementación concreta de `CompraRepository` con SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: str) -> Compra | None:
        """Busca una compra por id (incluye sus detalles). None si no existe."""
        m = self.session.get(CompraModel, id)
        return _to_entity(m) if m else None

    def list(
        self, desde: datetime | None = None, hasta: datetime | None = None
    ) -> list[Compra]:
        """Lista compras ordenadas de la más reciente a la más antigua.

        `desde` y `hasta` son filtros opcionales por rango de fechas.
        """
        # Orden descendente por fecha (las últimas compras primero).
        q = self.session.query(CompraModel).order_by(CompraModel.fecha.desc())
        if desde:
            q = q.filter(CompraModel.fecha >= desde)  # Fecha mínima.
        if hasta:
            q = q.filter(CompraModel.fecha <= hasta)  # Fecha máxima.
        return [_to_entity(m) for m in q.all()]

    def add(self, compra: Compra) -> Compra:
        """Registra una nueva compra junto con sus líneas de detalle."""
        m = CompraModel(
            id=compra.id,
            proveedor_id=compra.proveedor_id,
            fecha=compra.fecha,
            anulada=compra.anulada,
        )
        # Construimos los detalles ORM; `tipo` se mantiene tal cual viene.
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
        """Actualiza los datos básicos de una compra (proveedor y anulada)."""
        m = self.session.get(CompraModel, compra.id)
        m.anulada = compra.anulada
        m.proveedor_id = compra.proveedor_id
        self.session.flush()
        return compra

    def set_detalles(self, compra_id: str, detalles: list[DetalleCompra]) -> None:
        """Reemplaza todas las líneas de una compra por las nuevas recibidas."""
        # Primero borramos los detalles actuales (patrón "borrar y reinsertar").
        # synchronize_session=False evita que SQLAlchemy rastree cada objeto.
        self.session.query(DetalleCompraModel).filter(
            DetalleCompraModel.compra_id == compra_id
        ).delete(synchronize_session=False)
        # Luego insertamos las líneas nuevas.
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
        """Indica si el proveedor tiene al menos una compra registrada."""
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
        """Suma valor y cantidad de líneas de compra de un tipo y valor dados.

        Devuelve una tupla `(total_valor, total_cantidad)`:
        - total_valor = suma de (cantidad * precio_unitario).
        - total_cantidad = suma de cantidades.
        Solo cuenta compras NO anuladas. `excluir_compra` permite ignorar una
        compra concreta (útil al recalcular costos sin contar la actual).
        """
        # coalesce(...,0.0) convierte el resultado NULL en 0.0 cuando no hay filas.
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
            # Unimos detalle con cabecera para poder filtrar por `anulada`.
            .join(CompraModel, DetalleCompraModel.compra_id == CompraModel.id)
            .filter(
                DetalleCompraModel.tipo == tipo,
                columna == valor,  # columna puede ser insumo_id o producto_id.
                CompraModel.anulada.is_(False),  # Ignorar compras anuladas.
            )
        )
        if excluir_compra:
            q = q.filter(CompraModel.id != excluir_compra)
        total_valor, total_cantidad = q.one()  # Una sola fila de resultado.
        # Garantizamos floats y tratamos None como 0.0.
        return float(total_valor or 0.0), float(total_cantidad or 0.0)

    def suma_compras_insumo(
        self, insumo_id: str, excluir_compra: str | None = None
    ) -> tuple[float, float]:
        """Totales de compra de un insumo concreto (valor y cantidad)."""
        return self._suma(
            TipoLineaCompra.INSUMO.value,
            DetalleCompraModel.insumo_id,
            insumo_id,
            excluir_compra,
        )

    def suma_compras_producto(
        self, producto_id: str, excluir_compra: str | None = None
    ) -> tuple[float, float]:
        """Totales de compra de un producto concreto (valor y cantidad)."""
        return self._suma(
            TipoLineaCompra.PRODUCTO.value,
            DetalleCompraModel.producto_id,
            producto_id,
            excluir_compra,
        )

    def delete(self, id: str) -> None:
        """Elimina una compra si existe (sus detalles caen por cascada)."""
        m = self.session.get(CompraModel, id)
        if m is not None:
            self.session.delete(m)
            self.session.flush()
