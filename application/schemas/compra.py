"""Schemas (DTOs) de compras.

Agrupa los modelos Pydantic que describen cómo se registra una compra a un
proveedor, incluyendo el detalle de los productos o insumos comprados.

Los schemas son DTOs: solo transportan y validan datos de entrada/salida.
Las reglas de negocio (por ejemplo, calcular totales o actualizar stock) se
resuelven en los casos de uso correspondientes.

Relación con el dominio:
- `ItemCompra.tipo` permite distinguir si la línea corresponde a un producto
  terminado o a un insumo (materia prima), usando campos opcionales para cada
  caso.
"""

from pydantic import BaseModel


class ItemCompra(BaseModel):
    """Una línea (detalle) dentro de una compra."""

    # Tipo de ítem: "producto" o "insumo". Por defecto, producto.
    tipo: str = "producto"
    # Identificador del producto cuando tipo == "producto".
    producto_id: str | None = None
    # Identificador del insumo cuando tipo == "insumo".
    insumo_id: str | None = None
    # Cantidad comprada (puede ser decimal, p. ej. insumos a granel).
    cantidad: float
    # Precio por unidad al momento de la compra.
    precio_unitario: float


class CompraCreate(BaseModel):
    """Datos para registrar una compra completa."""

    # Proveedor al que se le compra.
    proveedor_id: str
    # Lista de líneas/ítems que componen la compra.
    items: list[ItemCompra]
