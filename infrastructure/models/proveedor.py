"""Modelo ORM de la tabla `proveedores`.

Un proveedor es la empresa o persona a la que se le compran productos o
insumos. Aquí se guardan sus datos de contacto e identificación.
"""

# Boolean y String.
from sqlalchemy import Boolean, Column, String

from database import Base


class ProveedorModel(Base):
    """Tabla de proveedores."""

    __tablename__ = "proveedores"

    # Identificador único del proveedor (clave primaria).
    id = Column(String, primary_key=True)
    # Nombre o razón social del proveedor.
    nombre = Column(String, nullable=False)
    # Nombre de la persona de contacto.
    contacto = Column(String, nullable=False)
    # Teléfono de contacto.
    telefono = Column(String, nullable=False)
    # Correo electrónico; por defecto vacío.
    email = Column(String, nullable=False, default="")
    # Dirección física; por defecto vacío.
    direccion = Column(String, nullable=False, default="")
    # Tipo de identificación (ej.: "CC", "NIT"); por defecto vacío.
    tipo_identificacion = Column(String, nullable=False, default="")
    # Número de identificación; por defecto vacío.
    identificacion = Column(String, nullable=False, default="")
    # Indica si el proveedor está activo (True) o inactivo (False).
    estado = Column(Boolean, nullable=False, default=True)
