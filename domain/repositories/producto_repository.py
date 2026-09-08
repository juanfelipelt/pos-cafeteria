from abc import ABC, abstractmethod

from domain.entities.producto import Producto


class ProductoRepository(ABC):
    @abstractmethod
    def get(self, id: str) -> Producto | None:
        ...

    @abstractmethod
    def list(
        self,
        filtro: str | None = None,
        categoria_id: str | None = None,
        solo_activos: bool = False,
    ) -> list[Producto]:
        ...

    @abstractmethod
    def add(self, producto: Producto) -> Producto:
        ...

    @abstractmethod
    def update(self, producto: Producto) -> Producto:
        ...
