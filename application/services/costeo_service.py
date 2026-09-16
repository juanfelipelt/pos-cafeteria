from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from application.costos import costos_productos
from domain.repositories.configuracion_repository import ConfiguracionRepository
from domain.repositories.costo_fijo_repository import CostoFijoRepository
from domain.repositories.insumo_repository import InsumoRepository
from domain.repositories.producto_repository import ProductoRepository
from domain.repositories.receta_repository import RecetaRepository
from domain.repositories.venta_repository import VentaRepository

DIAS_LABORALES_DEFECTO = "1,2,3,4,5,6"  # Lunes a Sábado (ISO 1..7)


class CosteoService:
    def __init__(
        self,
        productos: ProductoRepository,
        insumos: InsumoRepository,
        recetas: RecetaRepository,
        costos_fijos: CostoFijoRepository,
        configuraciones: ConfiguracionRepository,
        ventas: VentaRepository,
        session: Session,
    ) -> None:
        self.productos = productos
        self.insumos = insumos
        self.recetas = recetas
        self.costos_fijos = costos_fijos
        self.configuraciones = configuraciones
        self.ventas = ventas
        self.session = session

    # ----- utilidades de costeo -----

    def _dias_laborales(self) -> set[int]:
        config = self.configuraciones.get("dias_laborales")
        valor = config.valor if config else DIAS_LABORALES_DEFECTO
        dias: set[int] = set()
        for parte in valor.split(","):
            parte = parte.strip()
            if parte.isdigit() and 1 <= int(parte) <= 7:
                dias.add(int(parte))
        return dias or {1, 2, 3, 4, 5, 6}

    def _costos_productos(self) -> dict[str, float]:
        """Mapa producto_id -> costo variable unitario (resuelve combos)."""
        costos_insumos = {i.id: i.costo_unitario for i in self.insumos.list()}
        return costos_productos(
            self.productos.list(), self.recetas.list_all(), costos_insumos
        )

    @staticmethod
    def _contar_dias(dias: set[int], desde: date, hasta: date) -> int:
        if hasta < desde:
            return 0
        total = 0
        actual = desde
        while actual <= hasta:
            if actual.isoweekday() in dias:
                total += 1
            actual += timedelta(days=1)
        return total

    def _costo_fijo_periodo(
        self,
        costos_fijos_mes: float,
        dias: set[int],
        desde: date,
        hasta: date,
    ) -> float:
        """Prorratea el costo fijo mensual por mes calendario.

        Cada mes aporta (CF mensual / días laborables de ese mes) × días
        laborables del rango que caen en ese mes. Así un rango que cruza meses
        queda correcto.
        """
        if hasta < desde or costos_fijos_mes <= 0:
            return 0.0
        total = 0.0
        actual = desde
        while actual <= hasta:
            fin_mes = self._fin_de_mes(actual)
            tramo_fin = min(fin_mes, hasta)
            dias_mes = self._contar_dias(dias, actual.replace(day=1), fin_mes)
            dias_tramo = self._contar_dias(dias, actual, tramo_fin)
            if dias_mes:
                total += costos_fijos_mes * dias_tramo / dias_mes
            actual = fin_mes + timedelta(days=1)
        return total

    # ----- endpoints -----

    def listar_productos(self) -> list[dict]:
        costos = self._costos_productos()
        costos_fijos_mes = sum(
            c.monto for c in self.costos_fijos.list(solo_activos=True)
        )
        dias = self._dias_laborales()
        hoy = date.today()
        dias_mes = self._contar_dias(
            dias, hoy.replace(day=1), self._fin_de_mes(hoy)
        )
        cf_diario = costos_fijos_mes / dias_mes if dias_mes else 0.0

        items = []
        for producto in self.productos.list():
            costo = costos.get(producto.id, 0.0)
            margen = producto.precio - costo
            margen_pct = (margen / producto.precio * 100) if producto.precio else 0.0
            punto_equilibrio_unidades = (
                cf_diario / margen if margen > 0 else None
            )
            items.append(
                {
                    "producto_id": producto.id,
                    "nombre": producto.nombre,
                    "tipo": producto.tipo,
                    "precio": producto.precio,
                    "costo": costo,
                    "margen": margen,
                    "margen_pct": margen_pct,
                    "punto_equilibrio_unidades": punto_equilibrio_unidades,
                }
            )
        return items

    def resumen(self, desde: datetime, hasta: datetime) -> dict:
        ventas = [
            v for v in self.ventas.list(desde, hasta) if not v.anulada
        ]
        ventas_total = sum(v.total for v in ventas)

        costos = self._costos_productos()
        costo_variable = 0.0
        for venta in ventas:
            for detalle in venta.detalles:
                costo = detalle.costo_unitario
                if costo is None:
                    costo = costos.get(detalle.producto_id, 0.0)
                costo_variable += costo * detalle.cantidad

        margen = ventas_total - costo_variable

        costos_fijos_mes = sum(
            c.monto for c in self.costos_fijos.list(solo_activos=True)
        )
        dias = self._dias_laborales()
        fin = hasta.date()
        dias_mes = self._contar_dias(dias, fin.replace(day=1), self._fin_de_mes(fin))
        cf_diario = costos_fijos_mes / dias_mes if dias_mes else 0.0
        dias_rango = self._contar_dias(dias, desde.date(), hasta.date())
        cf_periodo = self._costo_fijo_periodo(
            costos_fijos_mes, dias, desde.date(), hasta.date()
        )

        utilidad = margen - cf_periodo
        margen_ratio = (margen / ventas_total) if ventas_total else 0.0
        punto_equilibrio = (cf_periodo / margen_ratio) if margen_ratio > 0 else None

        return {
            "desde": desde.isoformat(),
            "hasta": hasta.isoformat(),
            "ventas": ventas_total,
            "costo_variable": costo_variable,
            "margen": margen,
            "margen_pct": margen_ratio * 100,
            "costos_fijos_mes": costos_fijos_mes,
            "dias_laborables_mes": dias_mes,
            "dias_laborables_rango": dias_rango,
            "costo_fijo_diario": cf_diario,
            "costo_fijo_periodo": cf_periodo,
            "utilidad": utilidad,
            "punto_equilibrio": punto_equilibrio,
            "faltante_equilibrio": (
                max(0.0, punto_equilibrio - ventas_total)
                if punto_equilibrio is not None
                else None
            ),
        }

    @staticmethod
    def _fin_de_mes(fecha: date) -> date:
        if fecha.month == 12:
            siguiente = fecha.replace(year=fecha.year + 1, month=1, day=1)
        else:
            siguiente = fecha.replace(month=fecha.month + 1, day=1)
        return siguiente - timedelta(days=1)
