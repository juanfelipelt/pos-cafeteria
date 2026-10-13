"""Entidad de dominio ``DetalleCompra``.

Es una **línea** dentro de una ``Compra``. Cada línea representa lo que se
compró: o bien un producto terminado, o bien un insumo (materia prima). El
campo ``tipo`` decide cuál de los dos juegos de datos se usa.

Invariantes del negocio:
- ``tipo`` solo puede ser "producto" o "insumo".
- Si es producto: deben venir ``producto_id`` y ``nombre_producto``.
- Si es insumo: deben venir ``insumo_id`` y ``nombre_insumo``.
- La cantidad debe ser mayor que cero.
- El precio unitario no puede ser negativo.
"""

from dataclasses import dataclass

from .enums import TipoLineaCompra


@dataclass
class DetalleCompra:
    """Una línea dentro de una compra: un producto terminado o un insumo."""

    # Define la clase de artículo: "producto" o "insumo" (ver TipoLineaCompra).
    tipo: str
    # Cuántas unidades se compraron. Debe ser > 0.
    cantidad: float
    # Precio de una unidad. No puede ser negativo.
    precio_unitario: float
    # Identificador único de la línea; None si aún no se guardó.
    id: str | None = None
    # Datos usados cuando ``tipo`` es "producto".
    producto_id: str | None = None
    nombre_producto: str = ""
    # Datos usados cuando ``tipo`` es "insumo".
    insumo_id: str | None = None
    nombre_insumo: str = ""

    def __post_init__(self) -> None:
        """Valida la línea según su tipo y sus cantidades."""
        # El tipo debe ser uno de los permitidos por el enum.
        if self.tipo not in (
            TipoLineaCompra.PRODUCTO.value,
            TipoLineaCompra.INSUMO.value,
        ):
            raise ValueError("El tipo de línea de compra no es válido.")

        # Validaciones específicas para una línea de producto.
        if self.tipo == TipoLineaCompra.PRODUCTO.value:
            if not self.producto_id:
                raise ValueError("El producto es obligatorio.")
            if not self.nombre_producto.strip():
                raise ValueError("El nombre del producto es obligatorio.")
        # Para cualquier otro caso válido, la línea es de insumo.
        else:
            if not self.insumo_id:
                raise ValueError("El insumo es obligatorio.")
            if not self.nombre_insumo.strip():
                raise ValueError("El nombre del insumo es obligatorio.")

        # No se pueden comprar cantidades nulas o negativas.
        if self.cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero.")

        # El precio unitario puede ser cero (cortesía), pero nunca negativo.
        if self.precio_unitario < 0:
            raise ValueError("El precio unitario no puede ser negativo.")

    @property
    def nombre(self) -> str:
        """Devuelve el nombre correcto según el tipo (producto o insumo)."""
        return self.nombre_producto or self.nombre_insumo

    @property
    def subtotal(self) -> float:
        """Valor de la línea: cantidad multiplicada por el precio unitario."""
        return self.cantidad * self.precio_unitario

    def to_dict(self) -> dict:
        """Serializa la línea de compra a un diccionario."""
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
