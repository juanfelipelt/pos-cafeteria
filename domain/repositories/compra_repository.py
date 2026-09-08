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
    def delete(self, id: str) -> None:
        ...
