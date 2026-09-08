from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class DetalleCompraModel(Base):
    __tablename__ = "detalle_compras"

    id = Column(String, primary_key=True)
    compra_id = Column(String, ForeignKey("compras.id"), nullable=False)
    producto_id = Column(String, nullable=False)
    nombre_producto = Column(String, nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)

    compra = relationship("CompraModel", back_populates="detalles")
