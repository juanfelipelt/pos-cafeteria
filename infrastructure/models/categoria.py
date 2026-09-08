from sqlalchemy import Boolean, Column, String

from database import Base


class CategoriaModel(Base):
    __tablename__ = "categorias"

    id = Column(String, primary_key=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=False, default="")
    estado = Column(Boolean, nullable=False, default=True)
