"""Modelo ORM de la tabla `receta_detalles`.

Define la "receta" de un producto preparado: qué componentes (insumos u otros
productos) y en qué cantidad se necesitan para elaborarlo. Cada fila es un
componente de la receta de un producto.
"""

# Column y tipos; ForeignKey enlaza con la tabla de productos.
from sqlalchemy import Column, Float, ForeignKey, String

from database import Base


class RecetaModel(Base):
    """Tabla de componentes (líneas) de las recetas."""

    __tablename__ = "receta_detalles"

    # Identificador único de la línea de receta (clave primaria).
    id = Column(String, primary_key=True)
    # Producto al que pertenece esta receta (llave foránea a `productos.id`).
    producto_id = Column(String, ForeignKey("productos.id"), nullable=False)
    # Tipo de componente: "insumo" o "producto". Por defecto "insumo".
    tipo = Column(String, nullable=False, default="insumo")
    # Id del insumo componente (cuando tipo="insumo"). Por defecto vacío.
    insumo_id = Column(String, nullable=False, default="")
    # Id del producto componente (cuando tipo="producto"). Opcional; no lleva
    # ForeignKey porque puede referenciar productos vendibles usados como
    # ingrediente.
    componente_producto_id = Column(String, nullable=True)
    # Cantidad del componente necesaria para la receta.
    cantidad = Column(Float, nullable=False)
