"""Puerto (interfaz) de repositorio para ``Insumo``.

Contrato de guardado y consulta de la materia prima (insumos), incluyendo la
búsqueda por texto para el buscador y el filtro por estado.
"""

from __future__ import annotations
from abc import ABC, abstractmethod

from domain.entities.insumo import Insumo


class InsumoRepository(ABC):
    """Contrato de acceso a datos de los insumos."""

    @abstractmethod
    def get(self, id: str) -> Insumo | None:
        """Busca un insumo por su id. Devuelve None si no existe."""
        ...

    @abstractmethod
    def list(
        self,
        filtro: str | None = None,
        solo_activos: bool = False,
    ) -> list[Insumo]:
        """Lista insumos aplicando filtros opcionales.

        - ``filtro``: texto a buscar (por ejemplo en el nombre).
        - ``solo_activos``: si es True, solo devuelve los habilitados.
        """
        ...

    @abstractmethod
    def add(self, insumo: Insumo) -> Insumo:
        """Guarda un nuevo insumo y lo devuelve con su id asignado."""
        ...

    @abstractmethod
    def update(self, insumo: Insumo) -> Insumo:
        """Actualiza un insumo existente y devuelve el resultado."""
        ...

    @abstractmethod
    def delete(self, id: str) -> None:
        """Elimina un insumo por su id."""
        ...
