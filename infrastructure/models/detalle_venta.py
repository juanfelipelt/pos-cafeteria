from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class DetalleVentaModel(Base):
    __tablename__ = "detalle_ventas"

    id = Column(String, primary_key=True)
    venta_id = Column(String, ForeignKey("ventas.id"), nullable=False)
    producto_id = Column(String, nullable=False)
    nombre_producto = Column(String, nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    costo_unitario = Column(Float, nullable=True)

    venta = relationship("VentaModel", back_populates="detalles")
