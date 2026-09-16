from sqlalchemy import Boolean, Column, Float, String

from database import Base


class CostoFijoModel(Base):
    __tablename__ = "costos_fijos"

    id = Column(String, primary_key=True)
    nombre = Column(String, nullable=False)
    monto = Column(Float, nullable=False, default=0.0)
    activo = Column(Boolean, nullable=False, default=True)
