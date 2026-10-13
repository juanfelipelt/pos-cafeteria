"""Modelo ORM de la tabla `detalle_ventas`.

Cada fila es UNA línea (producto vendido) dentro de una venta. Guarda el
precio y el costo del momento de la venta para conservar el histórico aunque
el producto cambie después.
"""

# Column y tipos; ForeignKey enlaza con la tabla de ventas.
from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class DetalleVentaModel(Base):
    """Tabla de líneas o detalles de una venta."""

    __tablename__ = "detalle_ventas"

    # Identificador único de la línea (clave primaria).
    id = Column(String, primary_key=True)
    # A qué venta pertenece esta línea (llave foránea a `ventas.id`).
    venta_id = Column(String, ForeignKey("ventas.id"), nullable=False)
    # Id del producto vendido.
    producto_id = Column(String, nullable=False)
    # Nombre del producto copiado para conservar el histórico.
    nombre_producto = Column(String, nullable=False)
    # Cantidad vendida; se usa Integer porque se cuentan unidades enteras.
    cantidad = Column(Integer, nullable=False)
    # Precio unitario cobrado al cliente en esta venta.
    precio_unitario = Column(Float, nullable=False)
    # Costo unitario del producto en ese momento (para calcular la ganancia).
    # Puede ser nulo si no se pudo determinar.
    costo_unitario = Column(Float, nullable=True)

    # Relación muchos-a-uno: muchas líneas pertenecen a una sola venta.
    venta = relationship("VentaModel", back_populates="detalles")
