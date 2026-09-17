from __future__ import annotations
from abc import ABC, abstractmethod

from domain.entities.nota import Nota


class NotaRepository(ABC):
    @abstractmethod
    def get(self, id: str) -> Nota | None:
        ...

    @abstractmethod
    def list(
        self,
        destinatario: str | None = None,
        tipo: str | None = None,
        incluir_archivadas: bool = False,
    ) -> list[Nota]:
        ...

    @abstractmethod
    def add(self, nota: Nota) -> Nota:
        ...

    @abstractmethod
    def update(self, nota: Nota) -> Nota:
        ...

    @abstractmethod
    def delete(self, id: str) -> None:
        ...
