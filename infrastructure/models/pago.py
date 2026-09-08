from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import relationship

from database import Base


class PagoModel(Base):
    __tablename__ = "pagos"

    id = Column(String, primary_key=True)
    venta_id = Column(String, ForeignKey("ventas.id"), nullable=False)
    monto = Column(Float, nullable=False)
    metodo = Column(String, nullable=False)
    fecha = Column(DateTime, nullable=False)
    referencia = Column(String, nullable=True)

    venta = relationship("VentaModel", back_populates="pagos")
