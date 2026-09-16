from abc import ABC, abstractmethod

from domain.entities.insumo import Insumo


class InsumoRepository(ABC):
    @abstractmethod
    def get(self, id: str) -> Insumo | None:
        ...

    @abstractmethod
    def list(
        self,
        filtro: str | None = None,
        solo_activos: bool = False,
    ) -> list[Insumo]:
        ...

    @abstractmethod
    def add(self, insumo: Insumo) -> Insumo:
        ...

    @abstractmethod
    def update(self, insumo: Insumo) -> Insumo:
        ...

    @abstractmethod
    def delete(self, id: str) -> None:
        ...
