"""Entidad de dominio ``DetalleVenta``.

Es una **línea** dentro de una ``Venta``: indica qué producto se vendió,
cuántas unidades y a qué precio. Guardar el ``nombre_producto`` y el
``precio_unitario`` en la propia línea es clave: aunque después cambie el
precio del producto, la venta histórica conserva el valor con el que se
vendió.

Invariantes del negocio:
- Debe indicar un producto y su nombre.
- La cantidad debe ser mayor que cero.
- El precio unitario no puede ser negativo.
"""

from dataclasses import dataclass


@dataclass
class DetalleVenta:
    """Una línea de producto dentro de una venta."""

    # Producto vendido (obligatorio).
    producto_id: str
    # Nombre del producto "congelado" al momento de la venta.
    nombre_producto: str
    # Unidades vendidas. Debe ser > 0 (entero: no se venden fracciones).
    cantidad: int
    # Precio de una unidad al momento de la venta.
    precio_unitario: float
    # Identificador único de la línea; None si aún no se guardó.
    id: str | None = None
    # Costo de una unidad (opcional); sirve para calcular la ganancia.
    costo_unitario: float | None = None

    def __post_init__(self) -> None:
        """Valida los datos de la línea al crearla."""
        if not self.producto_id:
            raise ValueError("El producto es obligatorio.")

        if not self.nombre_producto.strip():
            raise ValueError("El nombre del producto es obligatorio.")

        if self.cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero.")

        # El precio puede ser cero (obsequio) pero nunca negativo.
        if self.precio_unitario < 0:
            raise ValueError("El precio unitario no puede ser negativo.")

    @property
    def subtotal(self) -> float:
        """Valor de la línea: cantidad por precio unitario."""
        return self.cantidad * self.precio_unitario

    def to_dict(self) -> dict:
        """Serializa la línea de venta a un diccionario."""
        return {
            "id": self.id,
            "producto_id": self.producto_id,
            "nombre_producto": self.nombre_producto,
            "cantidad": self.cantidad,
            "precio_unitario": self.precio_unitario,
            "costo_unitario": self.costo_unitario,
            "subtotal": self.subtotal,
        }
