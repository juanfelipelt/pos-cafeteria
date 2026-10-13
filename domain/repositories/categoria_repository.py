"""Puerto (interfaz) de repositorio para ``Categoria``.

Define **qué** operaciones de guardado y consulta se pueden hacer con las
categorías, sin decir **cómo**. La implementación real (por ejemplo, en
PostgreSQL o en memoria) vivirá en la capa de infraestructura y deberá
respetar esta interfaz.

Al ser una clase abstracta (``ABC``), no se puede instanciar directamente:
solo sirve como contrato para sus implementaciones.
"""

from __future__ import annotations
from abc import ABC, abstractmethod

from domain.entities.categoria import Categoria


class CategoriaRepository(ABC):
    """Contrato de acceso a datos de las categorías."""

    # ``@abstractmethod`` obliga a cada implementación a definir este método.
    @abstractmethod
    def get(self, id: str) -> Categoria | None:
        """Busca una categoría por su id. Devuelve None si no existe."""
        ...

    @abstractmethod
    def list(self) -> list[Categoria]:
        """Devuelve la lista completa de categorías."""
        ...

    @abstractmethod
    def add(self, categoria: Categoria) -> Categoria:
        """Guarda una nueva categoría y la devuelve con su id asignado."""
        ...

    @abstractmethod
    def update(self, categoria: Categoria) -> Categoria:
        """Actualiza una categoría existente y devuelve el resultado."""
        ...
