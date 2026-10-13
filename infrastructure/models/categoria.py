"""Modelo ORM de la tabla `categorias`.

Una categoría sirve para agrupar productos (por ejemplo: "Bebidas",
"Comidas", "Postres"). Aquí definimos la tabla y sus columnas con SQLAlchemy.
"""

# Boolean = tipo de dato booleano (verdadero/falso).
# Column = representa una columna de la tabla.
# String = tipo de dato texto de longitud variable.
from sqlalchemy import Boolean, Column, String

# `Base` es la clase base declarativa: todas las tablas heredan de ella y así
# SQLAlchemy las reconoce como tablas de la base de datos.
from database import Base


class CategoriaModel(Base):
    """Tabla de categorías de productos.

    Hereda de `Base`, por lo que SQLAlchemy la mapea a una tabla real.
    """

    # Nombre físico que tendrá la tabla en la base de datos.
    __tablename__ = "categorias"

    # Identificador único de la categoría (clave primaria).
    id = Column(String, primary_key=True)
    # Nombre visible de la categoría. No puede quedar vacío (nullable=False).
    nombre = Column(String, nullable=False)
    # Texto descriptivo; por defecto cadena vacía si no se envía.
    descripcion = Column(String, nullable=False, default="")
    # Indica si la categoría está activa (True) o deshabilitada (False).
    estado = Column(Boolean, nullable=False, default=True)
