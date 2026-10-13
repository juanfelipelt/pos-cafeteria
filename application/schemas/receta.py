"""Schemas (DTOs) de recetas.

Una receta define de qué está hecho un producto: qué insumos y en qué
cantidad se necesitan (y también componentes que son otros productos). Estos
modelos describen los datos de entrada/salida para gestionar la receta.

Son DTOs: solo validan y transportan datos; las reglas de negocio (cálculo de
costos, descuento de insumos) viven en los casos de uso.
"""

from pydantic import BaseModel


class ItemReceta(BaseModel):
    """Un componente (línea) de la receta de un producto."""

    # Tipo de componente: "insumo" (por defecto) u otro.
    tipo: str = "insumo"
    # Identificador del insumo cuando el componente es un insumo.
    insumo_id: str | None = None
    # Identificador de otro producto usado como componente.
    componente_producto_id: str | None = None
    # Cantidad necesaria del componente.
    cantidad: float


class RecetaUpdate(BaseModel):
    """Datos para reemplazar/actualizar la receta de un producto."""

    # Lista completa de ítems que componen la receta.
    items: list[ItemReceta]
