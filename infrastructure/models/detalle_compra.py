"""Modelo ORM de la tabla `detalle_compras`.

Cada fila es UNA línea (producto o insumo) dentro de una compra. Se
relaciona con `CompraModel` mediante la llave foránea `compra_id`.

Nota de diseño: se guardan copias del nombre y del id del producto/insumo
("desnormalización") para conservar el histórico, de modo que aunque luego
cambie o se elimine el producto, la compra siga siendo legible.
"""

# Column y tipos; ForeignKey enlaza con la tabla de compras.
from sqlalchemy import Column, Float, ForeignKey, String
from sqlalchemy.orm import relationship

from database import Base


class DetalleCompraModel(Base):
    """Tabla de líneas o detalles de una compra."""

    __tablename__ = "detalle_compras"

    # Identificador único de la línea (clave primaria).
    id = Column(String, primary_key=True)
    # A qué compra pertenece esta línea (llave foránea a `compras.id`).
    compra_id = Column(String, ForeignKey("compras.id"), nullable=False)
    # Tipo de línea: "producto" o "insumo". Por defecto "producto".
    tipo = Column(String, nullable=False, default="producto")
    # Id del producto comprado (si la línea es de tipo producto).
    producto_id = Column(String, nullable=False, default="")
    # Nombre del producto copiado para conservar el histórico.
    nombre_producto = Column(String, nullable=False, default="")
    # Id del insumo comprado (si la línea es de tipo insumo). Puede ser nulo.
    insumo_id = Column(String, nullable=True)
    # Nombre del insumo copiado para conservar el histórico.
    nombre_insumo = Column(String, nullable=True, default="")
    # Cantidad comprada (decimal, ej.: 2.5 kilos).
    cantidad = Column(Float, nullable=False)
    # Precio por unidad al momento de la compra.
    precio_unitario = Column(Float, nullable=False)

    # Relación muchos-a-uno: muchas líneas pertenecen a una sola compra.
    compra = relationship("CompraModel", back_populates="detalles")
