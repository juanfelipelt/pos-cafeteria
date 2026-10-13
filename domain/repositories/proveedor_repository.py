"""Puerto (interfaz) de repositorio para ``Proveedor``.

Contrato de guardado y consulta de los proveedores, con búsqueda por texto y
filtro por estado.
"""

from __future__ import annotations
from abc import ABC, abstractmethod

from domain.entities.proveedor import Proveedor


class ProveedorRepository(ABC):
    """Contrato de acceso a datos de los proveedores."""

    @abstractmethod
    def get(self, id: str) -> Proveedor | None:
        """Busca un proveedor por su id. Devuelve None si no existe."""
        ...

    @abstractmethod
    def list(self, filtro: str | None = None, solo_activos: bool = False) -> list[Proveedor]:
        """Lista proveedores aplicando filtros opcionales.

        - ``filtro``: texto a buscar (por ejemplo en el nombre).
        - ``solo_activos``: si es True, solo devuelve los habilitados.
        """
        ...

    @abstractmethod
    def add(self, proveedor: Proveedor) -> Proveedor:
        """Guarda un nuevo proveedor y lo devuelve con su id asignado."""
        ...

    @abstractmethod
    def update(self, proveedor: Proveedor) -> Proveedor:
        """Actualiza un proveedor existente y devuelve el resultado."""
        ...

    @abstractmethod
    def delete(self, id: str) -> None:
        """Elimina un proveedor por su id."""
        ...
