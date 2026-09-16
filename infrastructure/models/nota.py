from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text

from database import Base


class NotaModel(Base):
    __tablename__ = "notas"

    id = Column(String, primary_key=True)
    texto = Column(Text, nullable=False)
    tipo = Column(String, nullable=False, default="nota")
    destinatario = Column(String, nullable=False, default="todos")
    prioridad = Column(String, nullable=False, default="normal")
    autor_id = Column(String, ForeignKey("usuarios.id"), nullable=True)
    fecha_creacion = Column(DateTime, nullable=False)
    hecho = Column(Boolean, nullable=False, default=False)
    archivada = Column(Boolean, nullable=False, default=False)
