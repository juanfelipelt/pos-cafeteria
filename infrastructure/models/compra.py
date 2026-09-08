from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from database import Base


class CompraModel(Base):
    __tablename__ = "compras"

    id = Column(String, primary_key=True)
    proveedor_id = Column(String, ForeignKey("proveedores.id"), nullable=False)
    fecha = Column(DateTime, nullable=False)
    anulada = Column(Boolean, nullable=False, default=False)

    detalles = relationship(
        "DetalleCompraModel",
        back_populates="compra",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
