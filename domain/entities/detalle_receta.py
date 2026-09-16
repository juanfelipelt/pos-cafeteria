from dataclasses import dataclass

from .enums import TipoComponente


@dataclass
class DetalleReceta:
    """Un componente (insumo o producto) que compone un producto.

    - tipo "insumo": se guarda ``insumo_id``.
    - tipo "producto": se guarda ``componente_producto_id`` (para combos).
    """

    producto_id: str
    cantidad: float
    tipo: str = TipoComponente.INSUMO.value
    insumo_id: str | None = None
    componente_producto_id: str | None = None
    id: str | None = None

    def __post_init__(self) -> None:
        if not self.producto_id:
            raise ValueError("El producto es obligatorio.")
        if self.cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero.")

        if self.tipo == TipoComponente.INSUMO.value:
            if not self.insumo_id:
                raise ValueError("El insumo es obligatorio.")
        elif self.tipo == TipoComponente.PRODUCTO.value:
            if not self.componente_producto_id:
                raise ValueError("El producto componente es obligatorio.")
        else:
            raise ValueError("El tipo de componente no es válido.")

    @property
    def componente_id(self) -> str | None:
        if self.tipo == TipoComponente.PRODUCTO.value:
            return self.componente_producto_id
        return self.insumo_id

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "producto_id": self.producto_id,
            "tipo": self.tipo,
            "insumo_id": self.insumo_id,
            "componente_producto_id": self.componente_producto_id,
            "cantidad": self.cantidad,
        }
