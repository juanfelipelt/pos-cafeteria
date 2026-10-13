"""Puerto (interfaz) de repositorio para las recetas.

A diferencia de otros repositorios, aquí no se trabaja con una "cabecera" y
un id propio, sino con el conjunto de componentes (``DetalleReceta``) que
forman la receta de un producto. Por eso las operaciones se agrupan por
``producto_id`` (listar, reemplazar, borrar) en lugar de por id de receta.
"""

from abc import ABC, abstractmethod

from domain.entities.detalle_receta import DetalleReceta


class RecetaRepository(ABC):
    """Contrato de acceso a datos de los componentes de receta."""

    @abstractmethod
    def list_by_producto(self, producto_id: str) -> list[DetalleReceta]:
        """Devuelve los componentes de la receta de un producto."""
        ...

    @abstractmethod
    def list_all(self) -> list[DetalleReceta]:
        """Devuelve los componentes de todas las recetas (útil para reportes)."""
        ...

    @abstractmethod
    def set_for_producto(
        self, producto_id: str, detalles: list[DetalleReceta]
    ) -> list[DetalleReceta]:
        """Reemplaza por completo la receta de un producto.

        Sobrescribe los componentes anteriores por la nueva lista y devuelve
        los que quedaron guardados.
        """
        ...

    @abstractmethod
    def delete_by_producto(self, producto_id: str) -> None:
        """Elimina toda la receta de un producto."""
        ...

    @abstractmethod
    def has_for_insumo(self, insumo_id: str) -> bool:
        """Indica si un insumo se usa en alguna receta.

        Se usa para impedir borrar un insumo que todavía es necesario para
        preparar algún producto.
        """
        ...
