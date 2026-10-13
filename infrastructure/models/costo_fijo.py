"""Modelo ORM de la tabla `costos_fijos`.

Un costo fijo es un gasto que no cambia según cuánto se venda (por ejemplo:
arriendo, servicios, sueldos). Sirve para calcular el punto de equilibrio y
los costos del negocio.
"""

# Boolean (true/false), Column (columna), Float (número decimal), String (texto).
from sqlalchemy import Boolean, Column, Float, String

from database import Base


class CostoFijoModel(Base):
    """Tabla de costos fijos del negocio."""

    __tablename__ = "costos_fijos"

    # Identificador único del costo fijo (clave primaria).
    id = Column(String, primary_key=True)
    # Nombre o descripción del gasto fijo (ej.: "Arriendo").
    nombre = Column(String, nullable=False)
    # Monto (valor en dinero) del costo fijo. Por defecto 0.0.
    # Se usa Float por ser un número decimal.
    monto = Column(Float, nullable=False, default=0.0)
    # Indica si el costo fijo está vigente/activo (True) o no (False).
    activo = Column(Boolean, nullable=False, default=True)
