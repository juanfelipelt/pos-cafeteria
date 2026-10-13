"""Modelo ORM de la tabla `productos`.

Un producto es lo que se ofrece en el menú / catálogo y se vende a los
clientes. Puede ser de tipo "comprado" (se revende tal cual) o "preparado"
(se elabora con insumos según una receta).
"""

# Boolean, Column y varios tipos; ForeignKey enlaza con la tabla de categorías.
# Text se usa para la imagen en formato base64 o texto largo.
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text

from database import Base


class ProductoModel(Base):
    """Tabla de productos del catálogo / menú."""

    __tablename__ = "productos"

    # Identificador único del producto (clave primaria).
    id = Column(String, primary_key=True)
    # Nombre del producto (ej.: "Café con leche").
    nombre = Column(String, nullable=False)
    # Descripción del producto; por defecto cadena vacía.
    descripcion = Column(String, nullable=False, default="")
    # Categoría a la que pertenece. Es OPCIONAL (nullable=True) y apunta a
    # `categorias.id`.
    categoria_id = Column(String, ForeignKey("categorias.id"), nullable=True)
    # Imagen del producto (normalmente en base64). Por defecto vacío.
    imagen = Column(Text, nullable=False, default="")
    # Precio de venta al público. Por defecto 0.0.
    precio = Column(Float, nullable=False, default=0.0)
    # Unidades disponibles en inventario; entero. Por defecto 0.
    stock = Column(Integer, nullable=False, default=0)
    # Indica si el producto está activo (True) o deshabilitado (False).
    estado = Column(Boolean, nullable=False, default=True)
    # Tipo de producto: "comprado" o "preparado". Por defecto "comprado".
    tipo = Column(String, nullable=False, default="comprado")
    # Costo del producto (costo directo o calculado por receta). Por defecto 0.0.
    costo = Column(Float, nullable=False, default=0.0)
