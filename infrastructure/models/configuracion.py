from sqlalchemy import Column, String, Text

from database import Base


class ConfiguracionModel(Base):
    __tablename__ = "configuraciones"

    clave = Column(String, primary_key=True)
    valor = Column(Text, nullable=False, default="")
