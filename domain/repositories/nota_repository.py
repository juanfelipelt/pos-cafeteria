"""Puerto (interfaz) de repositorio para ``Nota``.

Contrato de guardado y consulta de las notas/tareas de la pizarra, con
filtros por destinatario, tipo y si se incluyen las archivadas.
"""

from __future__ import annotations
from abc import ABC, abstractmethod

from domain.entities.nota import Nota


class NotaRepository(ABC):
    """Contrato de acceso a datos de las notas de la pizarra."""

    @abstractmethod
    def get(self, id: str) -> Nota | None:
        """Busca una nota por su id. Devuelve None si no existe."""
        ...

    @abstractmethod
    def list(
        self,
        destinatario: str | None = None,
        tipo: str | None = None,
        incluir_archivadas: bool = False,
    ) -> list[Nota]:
        """Lista notas aplicando filtros opcionales.

        - ``destinatario``: solo las dirigidas a ese destinatario.
        - ``tipo``: solo "nota" o solo "tarea".
        - ``incluir_archivadas``: si es False, oculta las archivadas.
        """
        ...

    @abstractmethod
    def add(self, nota: Nota) -> Nota:
        """Guarda una nueva nota y la devuelve con su id asignado."""
        ...

    @abstractmethod
    def update(self, nota: Nota) -> Nota:
        """Actualiza una nota existente y devuelve el resultado."""
        ...

    @abstractmethod
    def delete(self, id: str) -> None:
        """Elimina una nota por su id."""
        ...
