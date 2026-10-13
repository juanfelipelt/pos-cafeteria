"""Servicio de reportes (caso de uso: "Reportes de ventas y productos").

¿Qué resuelve?
- Consultar resúmenes de ventas, ventas agrupadas por período y los productos
  más vendidos para un rango de fechas.

¿Cómo usa los repositorios?
- Recibe un ``ReporteRepository`` que ya contiene las consultas agregadas de
  base de datos (resumen, ventas_por_periodo, top_productos).

Es un servicio de solo lectura que sirve de fachada entre la API y el
repositorio de reportes, sin lógica de negocio adicional. Por eso no recibe
una ``Session``: no modifica datos.
"""

from datetime import datetime

from domain.repositories.reporte_repository import ReporteRepository


class ReporteService:
    """Expone las consultas agregadas de reportes."""

    def __init__(self, reportes: ReporteRepository) -> None:
        """Guarda la dependencia del servicio.

        Parámetros:
            reportes: repositorio con las consultas de reportes.
        """
        self.reportes = reportes

    def resumen(self, desde: datetime, hasta: datetime) -> dict:
        """Resumen general de ventas del período.

        Parámetros:
            desde: fecha/hora inicial.
            hasta: fecha/hora final.

        Retorna:
            Diccionario con los totales y métricas del período.
        """
        return self.reportes.resumen(desde, hasta)

    def ventas_por_periodo(
        self, desde: datetime, hasta: datetime, agrupacion: str
    ) -> list[dict]:
        """Ventas agrupadas por período (día, semana, mes, etc.).

        Parámetros:
            desde: fecha/hora inicial.
            hasta: fecha/hora final.
            agrupacion: unidad de agrupación (por ejemplo "dia", "mes").

        Retorna:
            Lista de grupos con sus totales.
        """
        return self.reportes.ventas_por_periodo(desde, hasta, agrupacion)

    def top_productos(
        self, desde: datetime, hasta: datetime, limite: int
    ) -> list[dict]:
        """Productos más vendidos del período.

        Parámetros:
            desde: fecha/hora inicial.
            hasta: fecha/hora final.
            limite: máximo de productos a devolver.

        Retorna:
            Lista de productos ordenados por cantidad vendida.
        """
        return self.reportes.top_productos(desde, hasta, limite)
