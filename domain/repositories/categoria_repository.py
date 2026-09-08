from abc import ABC, abstractmethod

from domain.entities.categoria import Categoria


class CategoriaRepository(ABC):
    @abstractmethod
    def get(self, id: str) -> Categoria | None:
        ...

    @abstractmethod
    def list(self) -> list[Categoria]:
        ...

    @abstractmethod
    def add(self, categoria: Categoria) -> Categoria:
        ...

    @abstractmethod
    def update(self, categoria: Categoria) -> Categoria:
        ...
