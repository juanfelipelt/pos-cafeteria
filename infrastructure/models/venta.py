from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from database import Base


class VentaModel(Base):
    __tablename__ = "ventas"

    id = Column(String, primary_key=True)
    usuario_id = Column(String, ForeignKey("usuarios.id"), nullable=True)
    fecha = Column(DateTime, nullable=False)
    anulada = Column(Boolean, nullable=False, default=False)

    detalles = relationship(
        "DetalleVentaModel",
        back_populates="venta",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    pagos = relationship(
        "PagoModel",
        back_populates="venta",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
