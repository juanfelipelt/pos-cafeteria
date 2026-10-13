"""Modelo ORM de la tabla `configuraciones`.

Guarda parámetros de configuración del sistema en formato clave-valor
(por ejemplo: nombre del negocio, IVA, moneda, etc.). Cada fila es un ajuste.
"""

# Column define columnas; String y Text son tipos de texto.
# Text permite textos largos (sin límite fijo), a diferencia de String.
from sqlalchemy import Column, String, Text

from database import Base


class ConfiguracionModel(Base):
    """Tabla de configuración clave-valor del sistema."""

    __tablename__ = "configuraciones"

    # La clave es el nombre del ajuste y además su clave primaria (única).
    clave = Column(String, primary_key=True)
    # El valor del ajuste; por defecto cadena vacía. Se usa Text porque puede
    # contener textos largos.
    valor = Column(Text, nullable=False, default="")
