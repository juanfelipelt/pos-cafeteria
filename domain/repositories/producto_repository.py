"""Puerto (interfaz) de repositorio para ``Producto``.

Contrato de guardado y consulta de los productos, con filtros por texto, por
categoría y por estado. La implementación concreta la aporta la infraestructura.
"""

from __future__ import annotations
from abc import ABC, abstractmethod

from domain.entities.producto import Producto


class ProductoRepository(ABC):
    """Contrato de acceso a datos de los productos."""

    @abstractmethod
    def get(self, id: str) -> Producto | None:
        """Busca un producto por su id. Devuelve None si no existe."""
        ...

    @abstractmethod
    def list(
        self,
        filtro: str | None = None,
        categoria_id: str | None = None,
        solo_activos: bool = False,
    ) -> list[Producto]:
        """Lista productos aplicando filtros opcionales.

        - ``filtro``: texto a buscar (por ejemplo en el nombre).
        - ``categoria_id``: solo los de esa categoría.
        - ``solo_activos``: si es True, solo devuelve los habilitados.
        """
        ...

    @abstractmethod
    def add(self, producto: Producto) -> Producto:
        """Guarda un nuevo producto y lo devuelve con su id asignado."""
        ...

    @abstractmethod
    def update(self, producto: Producto) -> Producto:
        """Actualiza un producto existente y devuelve el resultado."""
        ...
