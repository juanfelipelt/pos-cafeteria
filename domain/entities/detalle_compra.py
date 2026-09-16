from dataclasses import dataclass

from .enums import TipoLineaCompra


@dataclass
class DetalleCompra:
    """Una línea dentro de una compra: un producto terminado o un insumo."""

    tipo: str
    cantidad: float
    precio_unitario: float
    id: str | None = None
    producto_id: str | None = None
    nombre_producto: str = ""
    insumo_id: str | None = None
    nombre_insumo: str = ""

    def __post_init__(self) -> None:
        if self.tipo not in (
            TipoLineaCompra.PRODUCTO.value,
            TipoLineaCompra.INSUMO.value,
        ):
            raise ValueError("El tipo de línea de compra no es válido.")

        if self.tipo == TipoLineaCompra.PRODUCTO.value:
            if not self.producto_id:
                raise ValueError("El producto es obligatorio.")
            if not self.nombre_producto.strip():
                raise ValueError("El nombre del producto es obligatorio.")
        else:
            if not self.insumo_id:
                raise ValueError("El insumo es obligatorio.")
            if not self.nombre_insumo.strip():
                raise ValueError("El nombre del insumo es obligatorio.")

        if self.cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero.")

        if self.precio_unitario < 0:
            raise ValueError("El precio unitario no puede ser negativo.")

    @property
    def nombre(self) -> str:
        return self.nombre_producto or self.nombre_insumo

    @property
    def subtotal(self) -> float:
        return self.cantidad * self.precio_unitario

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "producto_id": self.producto_id,
            "nombre_producto": self.nombre_producto,
            "insumo_id": self.insumo_id,
            "nombre_insumo": self.nombre_insumo,
            "nombre": self.nombre,
            "cantidad": self.cantidad,
            "precio_unitario": self.precio_unitario,
            "subtotal": self.subtotal,
        }
