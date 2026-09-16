from abc import ABC, abstractmethod

from domain.entities.detalle_receta import DetalleReceta


class RecetaRepository(ABC):
    @abstractmethod
    def list_by_producto(self, producto_id: str) -> list[DetalleReceta]:
        ...

    @abstractmethod
    def list_all(self) -> list[DetalleReceta]:
        ...

    @abstractmethod
    def set_for_producto(
        self, producto_id: str, detalles: list[DetalleReceta]
    ) -> list[DetalleReceta]:
        ...

    @abstractmethod
    def delete_by_producto(self, producto_id: str) -> None:
        ...

    @abstractmethod
    def has_for_insumo(self, insumo_id: str) -> bool:
        ...
