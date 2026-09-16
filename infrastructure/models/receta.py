from sqlalchemy import Column, Float, ForeignKey, String

from database import Base


class RecetaModel(Base):
    __tablename__ = "receta_detalles"

    id = Column(String, primary_key=True)
    producto_id = Column(String, ForeignKey("productos.id"), nullable=False)
    tipo = Column(String, nullable=False, default="insumo")
    insumo_id = Column(String, nullable=False, default="")
    componente_producto_id = Column(String, nullable=True)
    cantidad = Column(Float, nullable=False)
