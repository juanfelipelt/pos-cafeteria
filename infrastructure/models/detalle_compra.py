from sqlalchemy import Column, Float, ForeignKey, String
from sqlalchemy.orm import relationship

from database import Base


class DetalleCompraModel(Base):
    __tablename__ = "detalle_compras"

    id = Column(String, primary_key=True)
    compra_id = Column(String, ForeignKey("compras.id"), nullable=False)
    tipo = Column(String, nullable=False, default="producto")
    producto_id = Column(String, nullable=False, default="")
    nombre_producto = Column(String, nullable=False, default="")
    insumo_id = Column(String, nullable=True)
    nombre_insumo = Column(String, nullable=True, default="")
    cantidad = Column(Float, nullable=False)
    precio_unitario = Column(Float, nullable=False)

    compra = relationship("CompraModel", back_populates="detalles")
