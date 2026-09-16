from abc import ABC, abstractmethod

from domain.entities.costo_fijo import CostoFijo


class CostoFijoRepository(ABC):
    @abstractmethod
    def get(self, id: str) -> CostoFijo | None:
        ...

    @abstractmethod
    def list(self, solo_activos: bool = False) -> list[CostoFijo]:
        ...

    @abstractmethod
    def add(self, costo: CostoFijo) -> CostoFijo:
        ...

    @abstractmethod
    def update(self, costo: CostoFijo) -> CostoFijo:
        ...

    @abstractmethod
    def delete(self, id: str) -> None:
        ...
