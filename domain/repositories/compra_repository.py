from abc import ABC, abstractmethod
from datetime import datetime

from domain.entities.compra import Compra


class CompraRepository(ABC):
    @abstractmethod
    def get(self, id: str) -> Compra | None:
        ...

    @abstractmethod
    def list(self, desde: datetime | None = None, hasta: datetime | None = None) -> list[Compra]:
        ...

    @abstractmethod
    def add(self, compra: Compra) -> Compra:
        ...

    @abstractmethod
    def update(self, compra: Compra) -> Compra:
        ...

    @abstractmethod
    def has_for_proveedor(self, proveedor_id: str) -> bool:
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
        ...
