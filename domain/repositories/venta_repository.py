"""Puerto (interfaz) de repositorio para ``Venta``.

Contrato de guardado y consulta de las ventas, con posibilidad de filtrar por
rango de fechas (muy útil para los reportes).
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime

from domain.entities.venta import Venta


class VentaRepository(ABC):
    """Contrato de acceso a datos de las ventas."""

    @abstractmethod
    def get(self, id: str) -> Venta | None:
        """Busca una venta por su id. Devuelve None si no existe."""
        ...

    @abstractmethod
    def list(self, desde: datetime | None = None, hasta: datetime | None = None) -> list[Venta]:
        """Lista ventas, opcionalmente dentro de un rango de fechas.

        ``desde`` y ``hasta`` son el límite inferior y superior; si son None,
        no se filtra por ese extremo.
        """
        ...

    @abstractmethod
    def add(self, venta: Venta) -> Venta:
        """Guarda una nueva venta (con sus líneas y pagos) y la devuelve."""
        ...

    @abstractmethod
    def update(self, venta: Venta) -> Venta:
        """Actualiza una venta existente y devuelve el resultado."""
        ...

    @abstractmethod
    def delete(self, id: str) -> None:
        """Elimina una venta por su id."""
        ...
