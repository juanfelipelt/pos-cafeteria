"""Cálculo de costos de productos (incluyendo recetas y combos).

Este módulo contiene la lógica de negocio para responder la pregunta: **¿cuánto
cuesta producir una unidad de cada producto?** Es la base para calcular márgenes
y precios de venta.

Tipos de producto que maneja:
- ``COMPRADO``: se compra hecho a un proveedor; su costo es el costo promedio
  ponderado que la app mantiene a partir de las compras registradas.
- ``PREPARADO`` / ``COMPUESTO``: se elaboran a partir de otros insumos y/o
  productos (su "receta"), por lo que su costo es la suma de sus componentes.
  Un ``COMPUESTO`` puede incluir otros productos, incluso combos, así que el
  cálculo se resuelve de forma recursiva y detecta ciclos para no colgarse.

Se relaciona con las entidades de dominio ``Producto``, ``DetalleReceta`` y los
enums ``TipoProducto`` / ``TipoComponente``. Lo usan los servicios de costeo y
los reportes.
"""

from domain.entities.detalle_receta import DetalleReceta
from domain.entities.enums import TipoComponente, TipoProducto
from domain.entities.producto import Producto


def costos_productos(
    productos: list[Producto],
    detalles_receta: list[DetalleReceta],
    costos_insumos: dict[str, float],
) -> dict[str, float]:
    """Costo variable unitario de cada producto (resuelve combos recursivamente).

    - COMPRADO: costo promedio ponderado mantenido por las compras.
    - PREPARADO/COMPUESTO: suma de sus componentes (insumos y/o productos).

    Parámetros:
        productos (list[Producto]): todos los productos a costear; de aquí sale
            el mapa de productos por id y el resultado final.
        detalles_receta (list[DetalleReceta]): líneas de receta que indican de
            qué insumos o productos se compone cada producto preparado/compuesto.
        costos_insumos (dict[str, float]): costo por unidad de cada insumo,
            indexado por id de insumo. Se usa cuando un componente es un insumo.

    Retorno:
        dict[str, float]: costo unitario por id de producto. Si no se puede
        determinar un costo, se devuelve 0.0 para ese producto.
    """
    # Agrupa las líneas de receta por producto para consultarlas rápido.
    recetas: dict[str, list[DetalleReceta]] = {}
    for detalle in detalles_receta:
        recetas.setdefault(detalle.producto_id, []).append(detalle)

    # Índice de productos por id, para buscarlos directamente.
    por_id = {p.id: p for p in productos}
    # Memoria (memoización): guarda costos ya calculados para no repetir trabajo.
    memo: dict[str, float] = {}

    def costo(producto_id: str, camino: frozenset[str]) -> float:
        """Calcula el costo de un producto resolviendo su receta recursivamente.

        Parámetros:
            producto_id (str): id del producto cuyo costo se quiere calcular.
            camino (frozenset[str]): conjunto de productos ya visitados en la
                recursión actual; sirve para detectar ciclos (A depende de B y
                B de A) y cortar la recursión.

        Retorno:
            float: costo unitario del producto (0.0 si no existe o hay ciclo).
        """
        # Si ya se calculó antes, se reutiliza el resultado.
        if producto_id in memo:
            return memo[producto_id]
        if producto_id in camino:
            # Ciclo detectado: se corta para no recursar infinito.
            return 0.0
        producto = por_id.get(producto_id)
        if producto is None:
            # Producto desconocido: se asume costo cero.
            return 0.0

        if producto.tipo == TipoProducto.COMPRADO.value:
            # Producto comprado: su costo ya lo mantiene el sistema (promedio de compras).
            valor = producto.costo
        else:
            # Producto preparado o compuesto: se suma el costo de cada componente.
            valor = 0.0
            # Se marca este producto como visitado para las llamadas recursivas.
            siguiente = camino | {producto_id}
            for detalle in recetas.get(producto_id, []):
                if (
                    detalle.tipo == TipoComponente.PRODUCTO.value
                    and detalle.componente_producto_id
                ):
                    # El componente es otro producto: se calcula su costo recursivamente.
                    valor += detalle.cantidad * costo(
                        detalle.componente_producto_id, siguiente
                    )
                else:
                    # El componente es un insumo: se usa su costo unitario conocido.
                    valor += detalle.cantidad * costos_insumos.get(
                        detalle.insumo_id, 0.0
                    )

        # Se guarda el resultado en la memoria y se devuelve.
        memo[producto_id] = valor
        return valor

    # Se calcula el costo de todos los productos, empezando sin camino visitado.
    return {pid: costo(pid, frozenset()) for pid in por_id}
