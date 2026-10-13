"""Modelo ORM de la tabla `ventas`.

Una venta es el registro de una operación de venta al cliente. Aquí se guarda
la cabecera (quién vendió, cuándo, si está anulada); las líneas de productos y
los pagos viven en `detalle_ventas` y `pagos` respectivamente.
"""

# Column define columnas; Boolean/DateTime/String son tipos de datos.
# ForeignKey enlaza con la tabla de usuarios.
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from database import Base


class VentaModel(Base):
    """Tabla de ventas."""

    __tablename__ = "ventas"

    # Identificador único de la venta (clave primaria).
    id = Column(String, primary_key=True)
    # Usuario que realizó la venta (llave foránea a `usuarios.id`). Es OPTATIVO
    # (nullable=True) porque una venta puede quedar sin usuario (ej.: histórico).
    usuario_id = Column(String, ForeignKey("usuarios.id"), nullable=True)
    # Fecha y hora de la venta.
    fecha = Column(DateTime, nullable=False)
    # Marca si la venta fue anulada. Por defecto False (no anulada).
    anulada = Column(Boolean, nullable=False, default=False)

    # Relación uno-a-muchos: una venta tiene varias líneas de detalle.
    # - cascade="all, delete-orphan": al borrar la venta se borran sus detalles.
    # - lazy="selectin": carga los detalles junto con la venta (evita el N+1).
    detalles = relationship(
        "DetalleVentaModel",
        back_populates="venta",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    # Relación uno-a-muchos: una venta puede tener varios pagos (pago mixto).
    pagos = relationship(
        "PagoModel",
        back_populates="venta",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
