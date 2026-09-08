from datetime import datetime

from domain.repositories.reporte_repository import ReporteRepository


class ReporteService:
    def __init__(self, reportes: ReporteRepository) -> None:
        self.reportes = reportes

    def resumen(self, desde: datetime, hasta: datetime) -> dict:
        return self.reportes.resumen(desde, hasta)

    def ventas_por_periodo(
        self, desde: datetime, hasta: datetime, agrupacion: str
    ) -> list[dict]:
        return self.reportes.ventas_por_periodo(desde, hasta, agrupacion)

    def top_productos(
        self, desde: datetime, hasta: datetime, limite: int
    ) -> list[dict]:
        return self.reportes.top_productos(desde, hasta, limite)
