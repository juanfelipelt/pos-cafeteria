from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text

from database import Base


class ProductoModel(Base):
    __tablename__ = "productos"

    id = Column(String, primary_key=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=False, default="")
    categoria_id = Column(String, ForeignKey("categorias.id"), nullable=True)
    imagen = Column(Text, nullable=False, default="")
    precio = Column(Float, nullable=False, default=0.0)
    stock = Column(Integer, nullable=False, default=0)
    estado = Column(Boolean, nullable=False, default=True)
