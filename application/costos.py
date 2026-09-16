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
    """
    recetas: dict[str, list[DetalleReceta]] = {}
    for detalle in detalles_receta:
        recetas.setdefault(detalle.producto_id, []).append(detalle)

    por_id = {p.id: p for p in productos}
    memo: dict[str, float] = {}

    def costo(producto_id: str, camino: frozenset[str]) -> float:
        if producto_id in memo:
            return memo[producto_id]
        if producto_id in camino:
            # Ciclo detectado: se corta para no recursar infinito.
            return 0.0
        producto = por_id.get(producto_id)
        if producto is None:
            return 0.0

        if producto.tipo == TipoProducto.COMPRADO.value:
            valor = producto.costo
        else:
            valor = 0.0
            siguiente = camino | {producto_id}
            for detalle in recetas.get(producto_id, []):
                if (
                    detalle.tipo == TipoComponente.PRODUCTO.value
                    and detalle.componente_producto_id
                ):
                    valor += detalle.cantidad * costo(
                        detalle.componente_producto_id, siguiente
                    )
                else:
                    valor += detalle.cantidad * costos_insumos.get(
                        detalle.insumo_id, 0.0
                    )

        memo[producto_id] = valor
        return valor

    return {pid: costo(pid, frozenset()) for pid in por_id}
