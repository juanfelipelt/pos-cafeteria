"""Modelo ORM de la tabla `notas`.

Las notas son mensajes internos o recordatorios (tipo "pizarra") que se dejan
entre los usuarios del sistema. Pueden dirigirse a un destinatario específico
o a "todos", tener prioridad y marcarse como hechas o archivadas.
"""

# Boolean, Column, DateTime, ForeignKey, String y Text.
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text

from database import Base


class NotaModel(Base):
    """Tabla de notas / recordatorios internos."""

    __tablename__ = "notas"

    # Identificador único de la nota (clave primaria).
    id = Column(String, primary_key=True)
    # Contenido de la nota; se usa Text porque puede ser largo.
    texto = Column(Text, nullable=False)
    # Tipo de nota: por ejemplo "nota" o "recordatorio". Por defecto "nota".
    tipo = Column(String, nullable=False, default="nota")
    # A quién va dirigida: un usuario o "todos". Por defecto "todos".
    destinatario = Column(String, nullable=False, default="todos")
    # Prioridad de la nota: "normal" o "alta". Por defecto "normal".
    prioridad = Column(String, nullable=False, default="normal")
    # Autor de la nota (llave foránea a `usuarios.id`). Opcional.
    autor_id = Column(String, ForeignKey("usuarios.id"), nullable=True)
    # Fecha y hora en que se creó la nota.
    fecha_creacion = Column(DateTime, nullable=False)
    # Marca si la nota ya fue atendida/hecha. Por defecto False.
    hecho = Column(Boolean, nullable=False, default=False)
    # Marca si la nota fue archivada. Por defecto False.
    archivada = Column(Boolean, nullable=False, default=False)
