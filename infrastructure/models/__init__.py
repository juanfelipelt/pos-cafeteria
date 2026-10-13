"""Modelos ORM (tablas) de la base de datos del proyecto Cafetería POS.

Cada archivo de este paquete define una clase que representa UNA tabla de la
base de datos usando SQLAlchemy (el ORM = Object Relational Mapper). Gracias al
ORM escribimos clases de Python y SQLAlchemy se encarga de traducirlas a tablas
y consultas SQL.

Este `__init__.py` reúne (importa) todos los modelos en un solo lugar para que,
al importar el paquete, SQLAlchemy conozca todas las tablas y pueda resolver
las relaciones entre ellas (por ejemplo, una venta con sus detalles y pagos).
"""

# --- Importación de cada modelo (una clase = una tabla) ---
from infrastructure.models.usuario import UsuarioModel
from infrastructure.models.categoria import CategoriaModel
from infrastructure.models.producto import ProductoModel
from infrastructure.models.proveedor import ProveedorModel
from infrastructure.models.venta import VentaModel
from infrastructure.models.detalle_venta import DetalleVentaModel
from infrastructure.models.pago import PagoModel
from infrastructure.models.compra import CompraModel
from infrastructure.models.detalle_compra import DetalleCompraModel
from infrastructure.models.configuracion import ConfiguracionModel
from infrastructure.models.insumo import InsumoModel
from infrastructure.models.receta import RecetaModel
from infrastructure.models.costo_fijo import CostoFijoModel
from infrastructure.models.nota import NotaModel

# `__all__` indica qué nombres se exportan cuando alguien hace:
# `from infrastructure.models import *`. Así se documenta la lista pública.
__all__ = [
    "UsuarioModel",
    "CategoriaModel",
    "ProductoModel",
    "ProveedorModel",
    "VentaModel",
    "DetalleVentaModel",
    "PagoModel",
    "CompraModel",
    "DetalleCompraModel",
    "ConfiguracionModel",
    "InsumoModel",
    "RecetaModel",
    "CostoFijoModel",
    "NotaModel",
]
