from abc import ABC, abstractmethod

from domain.entities.proveedor import Proveedor


class ProveedorRepository(ABC):
    @abstractmethod
    def get(self, id: str) -> Proveedor | None:
        ...

    @abstractmethod
    def list(self, filtro: str | None = None, solo_activos: bool = False) -> list[Proveedor]:
        ...

    @abstractmethod
    def add(self, proveedor: Proveedor) -> Proveedor:
        ...

    @abstractmethod
    def update(self, proveedor: Proveedor) -> Proveedor:
        ...

    @abstractmethod
    def delete(self, id: str) -> None:
        ...
