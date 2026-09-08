from sqlalchemy import Boolean, Column, String

from database import Base


class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id = Column(String, primary_key=True)
    nombre = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    contraseña_hash = Column(String, nullable=False)
    rol = Column(String, nullable=False, default="cajero")
    estado = Column(Boolean, nullable=False, default=True)
