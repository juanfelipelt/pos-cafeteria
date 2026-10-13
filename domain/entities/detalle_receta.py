"""Entidad de dominio ``DetalleReceta``.

Representa **un componente** de la receta de un producto. La receta explica
con qué se prepara o de qué se compone un producto. Un componente puede ser:

- Un insumo (materia prima), cuando ``tipo`` es "insumo": se usa ``insumo_id``.
- Otro producto, cuando ``tipo`` es "producto": sirve para armar combos y se
  usa ``componente_producto_id``.

Invariantes del negocio:
- Toda línea debe indicar a qué producto pertenece (``producto_id``).
- La cantidad debe ser mayor que cero.
- Según el ``tipo``, debe venir el id del insumo o el del producto componente.
"""

from dataclasses import dataclass

from .enums import TipoComponente


@dataclass
class DetalleReceta:
    """Un componente (insumo o producto) que compone un producto.

    - tipo "insumo": se guarda ``insumo_id``.
    - tipo "producto": se guarda ``componente_producto_id`` (para combos).
    """

    # Producto dueño de esta línea de receta (obligatorio).
    producto_id: str
    # Cuánto de este componente se necesita. Debe ser > 0.
    cantidad: float
    # Clase de componente; por defecto, un insumo.
    tipo: str = TipoComponente.INSUMO.value
    # Id del insumo cuando el componente es materia prima.
    insumo_id: str | None = None
    # Id del producto incluido cuando el componente es otro producto (combo).
    componente_producto_id: str | None = None
    # Identificador único de la línea; None si aún no se guardó.
    id: str | None = None

    def __post_init__(self) -> None:
        """Valida la línea de receta según su tipo."""
        if not self.producto_id:
            raise ValueError("El producto es obligatorio.")
        if self.cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero.")

        # Un componente de tipo insumo exige un ``insumo_id`` válido.
        if self.tipo == TipoComponente.INSUMO.value:
            if not self.insumo_id:
                raise ValueError("El insumo es obligatorio.")
        # Un componente de tipo producto exige el id del producto componente.
        elif self.tipo == TipoComponente.PRODUCTO.value:
            if not self.componente_producto_id:
                raise ValueError("El producto componente es obligatorio.")
        else:
            # Cualquier otro tipo no está permitido.
            raise ValueError("El tipo de componente no es válido.")

    @property
    def componente_id(self) -> str | None:
        """Devuelve el id del componente sin importar de qué tipo sea.

        Se usa cuando otra parte del código solo necesita "el id" del
        componente y no le importa si es un insumo o un producto.
        """
        if self.tipo == TipoComponente.PRODUCTO.value:
            return self.componente_producto_id
        return self.insumo_id

    def to_dict(self) -> dict:
        """Serializa la línea de receta a un diccionario."""
        return {
            "id": self.id,
            "producto_id": self.producto_id,
            "tipo": self.tipo,
            "insumo_id": self.insumo_id,
            "componente_producto_id": self.componente_producto_id,
            "cantidad": self.cantidad,
        }
