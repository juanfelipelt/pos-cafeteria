"""Puerto (interfaz) de repositorio para ``CostoFijo``.

Contrato de guardado y consulta de los gastos fijos mensuales. La
implementación concreta la aporta la capa de infraestructura.
"""

from __future__ import annotations
from abc import ABC, abstractmethod

from domain.entities.costo_fijo import CostoFijo


class CostoFijoRepository(ABC):
    """Contrato de acceso a datos de los costos fijos."""

    @abstractmethod
    def get(self, id: str) -> CostoFijo | None:
        """Busca un costo fijo por su id. Devuelve None si no existe."""
        ...

    @abstractmethod
    def list(self, solo_activos: bool = False) -> list[CostoFijo]:
        """Lista los costos fijos.

        Si ``solo_activos`` es True, omite los que están desactivados.
        """
        ...

    @abstractmethod
    def add(self, costo: CostoFijo) -> CostoFijo:
        """Guarda un nuevo costo fijo y lo devuelve con su id asignado."""
        ...

    @abstractmethod
    def update(self, costo: CostoFijo) -> CostoFijo:
        """Actualiza un costo fijo existente y devuelve el resultado."""
        ...

    @abstractmethod
    def delete(self, id: str) -> None:
        """Elimina un costo fijo por su id."""
        ...
