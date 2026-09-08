from dataclasses import dataclass


@dataclass
class DetalleCompra:
    """Una línea de producto dentro de una compra a proveedor."""

    producto_id: str
    nombre_producto: str
    cantidad: int
    precio_unitario: float
    id: str | None = None

    def __post_init__(self) -> None:
        if not self.producto_id:
            raise ValueError("El producto es obligatorio.")

        if not self.nombre_producto.strip():
            raise ValueError("El nombre del producto es obligatorio.")

        if self.cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero.")

        if self.precio_unitario < 0:
            raise ValueError("El precio unitario no puede ser negativo.")

    @property
    def subtotal(self) -> float:
        return self.cantidad * self.precio_unitario

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "producto_id": self.producto_id,
            "nombre_producto": self.nombre_producto,
            "cantidad": self.cantidad,
            "precio_unitario": self.precio_unitario,
            "subtotal": self.subtotal,
        }
