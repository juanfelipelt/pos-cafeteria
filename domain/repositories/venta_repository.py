from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime

from domain.entities.venta import Venta


class VentaRepository(ABC):
    @abstractmethod
    def get(self, id: str) -> Venta | None:
        ...

    @abstractmethod
    def list(self, desde: datetime | None = None, hasta: datetime | None = None) -> list[Venta]:
        ...

    @abstractmethod
    def add(self, venta: Venta) -> Venta:
        ...

    @abstractmethod
    def update(self, venta: Venta) -> Venta:
        ...

    @abstractmethod
    def delete(self, id: str) -> None:
        ...
