"""Servicio de costeo (caso de uso: "Rentabilidad y punto de equilibrio").

¿Qué resuelve?
- Calcular, por cada producto, su costo variable, su margen y el punto de
  equilibrio (cuántas unidades hay que vender para cubrir los costos fijos).
- Entregar un resumen de rentabilidad de un período: ventas, costo variable,
  margen, costos fijos prorrateados, utilidad y punto de equilibrio.

¿Cómo usa los repositorios?
- ``ProductoRepository``, ``InsumoRepository`` y ``RecetaRepository``: se usan
  para calcular el costo variable de cada producto (incluyendo combos).
- ``CostoFijoRepository``: aporta los costos fijos mensuales activos.
- ``ConfiguracionRepository``: de ahí salen los días laborables del negocio.
- ``VentaRepository``: se leen las ventas del período a analizar.
- ``Session``: por consistencia, aunque este servicio es de solo lectura.

Concepto clave: los costos fijos se prorratean por días laborables, no por
días calendario, porque el negocio solo opera ciertos días.
"""

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
    """Calcula costos, márgenes y punto de equilibrio."""

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
        """Guarda las dependencias del servicio.

        Parámetros:
            productos: repositorio de productos.
            insumos: repositorio de insumos.
            recetas: repositorio de recetas.
            costos_fijos: repositorio de costos fijos.
            configuraciones: repositorio de configuración (días laborables).
            ventas: repositorio de ventas.
            session: sesión de SQLAlchemy.
        """
        self.productos = productos
        self.insumos = insumos
        self.recetas = recetas
        self.costos_fijos = costos_fijos
        self.configuraciones = configuraciones
        self.ventas = ventas
        self.session = session

    # ----- utilidades de costeo -----

    def _dias_laborales(self) -> set[int]:
        """Lee los días laborables desde la configuración.

        El valor se guarda como texto separado por comas (por ejemplo
        "1,2,3,4,5,6"). Si la configuración no existe o queda vacía, se usan
        los días por defecto (lunes a sábado).

        Retorna:
            Conjunto de números ISO de día (1 = lunes ... 7 = domingo).
        """
        config = self.configuraciones.get("dias_laborales")
        valor = config.valor if config else DIAS_LABORALES_DEFECTO
        dias: set[int] = set()
        # Se interpreta cada parte y solo se aceptan números entre 1 y 7.
        for parte in valor.split(","):
            parte = parte.strip()
            if parte.isdigit() and 1 <= int(parte) <= 7:
                dias.add(int(parte))
        # Si nada quedó válido, se cae al valor por defecto.
        return dias or {1, 2, 3, 4, 5, 6}

    def _costos_productos(self) -> dict[str, float]:
        """Mapa producto_id -> costo variable unitario (resuelve combos).

        Retorna:
            Diccionario con el costo variable de cada producto. La función
            ``costos_productos`` resuelve preparados y compuestos de forma
            recursiva usando las recetas y los costos de los insumos.
        """
        # Se indexan los costos de insumos por id para resolver las recetas.
        costos_insumos = {i.id: i.costo_unitario for i in self.insumos.list()}
        return costos_productos(
            self.productos.list(), self.recetas.list_all(), costos_insumos
        )

    @staticmethod
    def _contar_dias(dias: set[int], desde: date, hasta: date) -> int:
        """Cuenta cuántos días laborables hay entre dos fechas (inclusive).

        Parámetros:
            dias: conjunto de días ISO considerados laborables.
            desde: fecha inicial (inclusive).
            hasta: fecha final (inclusive).

        Retorna:
            Cantidad de días laborables; 0 si el rango está invertido.
        """
        # Rango inválido (fin antes de inicio): no hay días.
        if hasta < desde:
            return 0
        total = 0
        actual = desde
        # Se recorre día por día y se cuenta solo si es laborable.
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

        Parámetros:
            costos_fijos_mes: suma de los costos fijos mensuales activos.
            dias: conjunto de días laborables.
            desde: fecha inicial del período.
            hasta: fecha final del período.

        Retorna:
            El costo fijo total correspondiente al período.
        """
        # Rango inválido o sin costos fijos: no se aporta nada.
        if hasta < desde or costos_fijos_mes <= 0:
            return 0.0
        total = 0.0
        actual = desde
        # Se recorre el período mes por mes.
        while actual <= hasta:
            fin_mes = self._fin_de_mes(actual)
            # El tramo termina al fin de mes o al fin del rango (el menor).
            tramo_fin = min(fin_mes, hasta)
            # Días laborables de todo el mes y del tramo que cae en el rango.
            dias_mes = self._contar_dias(dias, actual.replace(day=1), fin_mes)
            dias_tramo = self._contar_dias(dias, actual, tramo_fin)
            if dias_mes:
                # Regla de tres: porción proporcional del costo fijo del mes.
                total += costos_fijos_mes * dias_tramo / dias_mes
            # Se avanza al primer día del mes siguiente.
            actual = fin_mes + timedelta(days=1)
        return total

    # ----- endpoints -----

    def listar_productos(self) -> list[dict]:
        """Lista cada producto con su costo, margen y punto de equilibrio.

        El punto de equilibrio del producto indica cuántas unidades diarias
        habría que vender (con el margen de ese producto) para cubrir el costo
        fijo diario del negocio.

        Retorna:
            Lista de diccionarios con los indicadores por producto.
        """
        costos = self._costos_productos()
        # Costos fijos mensuales activos (suma de sus montos).
        costos_fijos_mes = sum(
            c.monto for c in self.costos_fijos.list(solo_activos=True)
        )
        dias = self._dias_laborales()
        hoy = date.today()
        # Días laborables del mes actual para hallar el costo fijo diario.
        dias_mes = self._contar_dias(
            dias, hoy.replace(day=1), self._fin_de_mes(hoy)
        )
        cf_diario = costos_fijos_mes / dias_mes if dias_mes else 0.0

        items = []
        for producto in self.productos.list():
            # Si el producto no tiene costo calculado, se asume 0.
            costo = costos.get(producto.id, 0.0)
            # Margen absoluto = precio de venta menos costo variable.
            margen = producto.precio - costo
            # Margen porcentual sobre el precio (evita división por cero).
            margen_pct = (margen / producto.precio * 100) if producto.precio else 0.0
            # Punto de equilibrio = costo fijo diario / margen unitario.
            # Solo tiene sentido si el margen es positivo.
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
        """Resumen de rentabilidad de un período.

        Calcula ventas, costo variable, margen, costos fijos prorrateados,
        utilidad y punto de equilibrio del rango indicado.

        Parámetros:
            desde: fecha/hora inicial del período.
            hasta: fecha/hora final del período.

        Retorna:
            Diccionario con todos los indicadores del período.
        """
        # Solo se consideran ventas no anuladas dentro del rango.
        ventas = [
            v for v in self.ventas.list(desde, hasta) if not v.anulada
        ]
        ventas_total = sum(v.total for v in ventas)

        costos = self._costos_productos()
        costo_variable = 0.0
        for venta in ventas:
            for detalle in venta.detalles:
                # Se usa el costo congelado al momento de la venta si existe;
                # si no, se recurre al costo actual del producto.
                costo = detalle.costo_unitario
                if costo is None:
                    costo = costos.get(detalle.producto_id, 0.0)
                costo_variable += costo * detalle.cantidad

        # Margen de contribución = ventas - costo variable.
        margen = ventas_total - costo_variable

        # Costos fijos mensuales activos del negocio.
        costos_fijos_mes = sum(
            c.monto for c in self.costos_fijos.list(solo_activos=True)
        )
        dias = self._dias_laborales()
        fin = hasta.date()
        # Días laborables del mes de la fecha final y costo fijo diario.
        dias_mes = self._contar_dias(dias, fin.replace(day=1), self._fin_de_mes(fin))
        cf_diario = costos_fijos_mes / dias_mes if dias_mes else 0.0
        # Días laborables del rango y costo fijo que le corresponde.
        dias_rango = self._contar_dias(dias, desde.date(), hasta.date())
        cf_periodo = self._costo_fijo_periodo(
            costos_fijos_mes, dias, desde.date(), hasta.date()
        )

        # Utilidad = margen de contribución menos costos fijos del período.
        utilidad = margen - cf_periodo
        # Qué fracción de las ventas es margen (ratio de contribución).
        margen_ratio = (margen / ventas_total) if ventas_total else 0.0
        # Punto de equilibrio en dinero: CF / ratio de margen.
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
            # Cuánto falta vender para llegar al equilibrio (nunca negativo).
            "faltante_equilibrio": (
                max(0.0, punto_equilibrio - ventas_total)
                if punto_equilibrio is not None
                else None
            ),
        }

    @staticmethod
    def _fin_de_mes(fecha: date) -> date:
        """Devuelve el último día del mes de la fecha dada.

        Parámetros:
            fecha: cualquier fecha del mes.

        Retorna:
            La fecha del último día de ese mes.
        """
        # Se calcula el primer día del mes siguiente y se resta un día.
        if fecha.month == 12:
            siguiente = fecha.replace(year=fecha.year + 1, month=1, day=1)
        else:
            siguiente = fecha.replace(month=fecha.month + 1, day=1)
        return siguiente - timedelta(days=1)
