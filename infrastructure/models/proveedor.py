from sqlalchemy import Boolean, Column, String

from database import Base


class ProveedorModel(Base):
    __tablename__ = "proveedores"

    id = Column(String, primary_key=True)
    nombre = Column(String, nullable=False)
    contacto = Column(String, nullable=False)
    telefono = Column(String, nullable=False)
    email = Column(String, nullable=False, default="")
    direccion = Column(String, nullable=False, default="")
    estado = Column(Boolean, nullable=False, default=True)
