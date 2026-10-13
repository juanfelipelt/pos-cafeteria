"""Modelo ORM de la tabla `pagos`.

Cada fila es un pago aplicado a una venta. Una venta puede tener uno o varios
pagos (pago mixto): por ejemplo, parte en efectivo y parte en transferencia.
"""

# Column y tipos; ForeignKey enlaza con la tabla de ventas.
from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import relationship

from database import Base


class PagoModel(Base):
    """Tabla de pagos asociados a las ventas."""

    __tablename__ = "pagos"

    # Identificador único del pago (clave primaria).
    id = Column(String, primary_key=True)
    # A qué venta pertenece este pago (llave foránea a `ventas.id`).
    venta_id = Column(String, ForeignKey("ventas.id"), nullable=False)
    # Monto pagado en este movimiento.
    monto = Column(Float, nullable=False)
    # Método de pago usado (ej.: "efectivo", "tarjeta", "transferencia").
    metodo = Column(String, nullable=False)
    # Fecha y hora en que se hizo el pago.
    fecha = Column(DateTime, nullable=False)
    # Referencia o número de comprobante del pago. Opcional (nullable=True).
    referencia = Column(String, nullable=True)

    # Relación muchos-a-uno: muchos pagos pertenecen a una sola venta.
    venta = relationship("VentaModel", back_populates="pagos")
