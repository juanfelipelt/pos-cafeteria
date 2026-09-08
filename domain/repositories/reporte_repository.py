from abc import ABC, abstractmethod
from datetime import datetime


class ReporteRepository(ABC):
    @abstractmethod
    def resumen(self, desde: datetime, hasta: datetime) -> dict:
        ...

    @abstractmethod
    def ventas_por_periodo(
        self, desde: datetime, hasta: datetime, agrupacion: str
    ) -> list[dict]:
        ...

    @abstractmethod
    def top_productos(
        self, desde: datetime, hasta: datetime, limite: int
    ) -> list[dict]:
        ...
