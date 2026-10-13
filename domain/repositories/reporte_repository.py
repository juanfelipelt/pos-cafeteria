"""Puerto (interfaz) de repositorio para reportes.

Este repositorio no devuelve entidades del dominio sino resúmenes ya
calculados (diccionarios con totales, agrupaciones y rankings). Es la puerta
que usa la aplicación para obtener estadísticas sin conocer las consultas
SQL que hay detrás.
"""

from abc import ABC, abstractmethod
from datetime import datetime


class ReporteRepository(ABC):
    """Contrato de consulta de reportes y estadísticas del negocio."""

    @abstractmethod
    def resumen(self, desde: datetime, hasta: datetime) -> dict:
        """Devuelve un resumen general del negocio en un rango de fechas.

        Normalmente incluye totales de ventas, ganancias y costos.
        """
        ...

    @abstractmethod
    def ventas_por_periodo(
        self, desde: datetime, hasta: datetime, agrupacion: str
    ) -> list[dict]:
        """Agrupa las ventas por periodo dentro del rango indicado.

        ``agrupacion`` define el nivel de detalle (por ejemplo "dia", "mes").
        Devuelve una lista de diccionarios, uno por periodo.
        """
        ...

    @abstractmethod
    def top_productos(
        self, desde: datetime, hasta: datetime, limite: int
    ) -> list[dict]:
        """Devuelve los productos más vendidos dentro del rango.

        ``limite`` indica cuántos productos se quieren como máximo.
        """
        ...
