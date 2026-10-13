"""Modelo ORM de la tabla `compras`.

Una compra representa el ingreso de mercancía (productos o insumos) que la
tienda hace a un proveedor. Aquí se guarda la cabecera de la compra; las
líneas de detalle viven en la tabla `detalle_compras`.
"""

# Column y los tipos de datos; ForeignKey = llave foránea hacia otra tabla.
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
# `relationship` permite navegar en Python de una compra a sus detalles.
from sqlalchemy.orm import relationship

from database import Base


class CompraModel(Base):
    """Tabla de compras realizadas a proveedores."""

    __tablename__ = "compras"

    # Identificador único de la compra (clave primaria).
    id = Column(String, primary_key=True)
    # Proveedor al que se le hizo la compra. Es obligatorio y apunta a
    # `proveedores.id` (llave foránea).
    proveedor_id = Column(String, ForeignKey("proveedores.id"), nullable=False)
    # Fecha y hora en que se registró la compra.
    fecha = Column(DateTime, nullable=False)
    # Marca si la compra fue anulada. Por defecto False (no anulada).
    anulada = Column(Boolean, nullable=False, default=False)

    # Relación uno-a-muchos: una compra tiene varios detalles.
    # - back_populates="compra": el lado inverso en DetalleCompraModel.
    # - cascade="all, delete-orphan": al borrar la compra se borran sus detalles.
    # - lazy="selectin": carga los detalles junto con la compra (evita consultas
    #   extra más adelante, es decir, evita el problema "N+1").
    detalles = relationship(
        "DetalleCompraModel",
        back_populates="compra",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
