"""Puerto (interfaz) de repositorio para ``Compra``.

Contrato que describe cómo se consultan y guardan las compras a proveedor,
incluyendo operaciones de negocio como sumar lo comprado de un insumo o
comprobar si un proveedor tiene compras. La implementación concreta queda
para la capa de infraestructura.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime

from domain.entities.compra import Compra
from domain.entities.detalle_compra import DetalleCompra


class CompraRepository(ABC):
    """Contrato de acceso a datos de las compras a proveedor."""

    @abstractmethod
    def get(self, id: str) -> Compra | None:
        """Busca una compra por su id. Devuelve None si no existe."""
        ...

    @abstractmethod
    def list(self, desde: datetime | None = None, hasta: datetime | None = None) -> list[Compra]:
        """Lista compras, opcionalmente filtrando por rango de fechas.

        ``desde`` y ``hasta`` son el límite inferior y superior; si son None,
        no se filtra por ese extremo.
        """
        ...

    @abstractmethod
    def add(self, compra: Compra) -> Compra:
        """Guarda una nueva compra (con sus líneas) y la devuelve con su id."""
        ...

    @abstractmethod
    def update(self, compra: Compra) -> Compra:
        """Actualiza una compra existente y devuelve el resultado."""
        ...

    @abstractmethod
    def set_detalles(
        self, compra_id: str, detalles: list[DetalleCompra]
    ) -> None:
        """Reemplaza las líneas de una compra existente."""
        ...

    @abstractmethod
    def has_for_proveedor(self, proveedor_id: str) -> bool:
        """Indica si el proveedor tiene compras asociadas.

        Se usa para impedir borrar un proveedor que ya tenga historial.
        """
        ...

    @abstractmethod
    def suma_compras_insumo(
        self, insumo_id: str, excluir_compra: str | None = None
    ) -> tuple[float, float]:
        """Devuelve (valor_total, cantidad_total) de las compras no anuladas
        de un insumo. ``excluir_compra`` omite una compra concreta."""
        ...

    @abstractmethod
    def suma_compras_producto(
        self, producto_id: str, excluir_compra: str | None = None
    ) -> tuple[float, float]:
        """Igual que ``suma_compras_insumo`` pero para productos comprados."""
        ...

    @abstractmethod
    def delete(self, id: str) -> None:
        """Elimina una compra por su id."""
        ...
