"""Modelo ORM de la tabla `insumos`.

Un insumo es una materia prima que se usa para preparar productos (por
ejemplo: harina, queso, café en grano). Se lleva su stock y su costo unitario.
"""

# Boolean, Column, Float, ForeignKey y String.
from sqlalchemy import Boolean, Column, Float, ForeignKey, String

from database import Base


class InsumoModel(Base):
    """Tabla de insumos (materias primas)."""

    __tablename__ = "insumos"

    # Identificador único del insumo (clave primaria).
    id = Column(String, primary_key=True)
    # Nombre del insumo (ej.: "Harina de trigo").
    nombre = Column(String, nullable=False)
    # Unidad de medida (ej.: "kg", "litro", "unidad"). Por defecto vacío.
    unidad = Column(String, nullable=False, default="")
    # Cantidad disponible en inventario. Por defecto 0.0.
    stock = Column(Float, nullable=False, default=0.0)
    # Costo por unidad del insumo. Por defecto 0.0.
    costo_unitario = Column(Float, nullable=False, default=0.0)
    # Proveedor principal del insumo. Es OPCIONAL (nullable=True) y apunta a
    # `proveedores.id`.
    proveedor_id = Column(String, ForeignKey("proveedores.id"), nullable=True)
    # Indica si el insumo está activo (True) o deshabilitado (False).
    estado = Column(Boolean, nullable=False, default=True)
