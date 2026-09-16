from sqlalchemy import Boolean, Column, Float, ForeignKey, String

from database import Base


class InsumoModel(Base):
    __tablename__ = "insumos"

    id = Column(String, primary_key=True)
    nombre = Column(String, nullable=False)
    unidad = Column(String, nullable=False, default="")
    stock = Column(Float, nullable=False, default=0.0)
    costo_unitario = Column(Float, nullable=False, default=0.0)
    proveedor_id = Column(String, ForeignKey("proveedores.id"), nullable=True)
    estado = Column(Boolean, nullable=False, default=True)
