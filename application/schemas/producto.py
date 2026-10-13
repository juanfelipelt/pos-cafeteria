"""Schemas (DTOs) de productos.

Un producto es lo que se vende (un plato, una bebida, etc.). Estos modelos
describen los datos de entrada/salida para crearlos, actualizarlos y cambiar
su estado.

Son DTOs: solo validan y transportan datos; las reglas de negocio (precios,
stock, recetas) se resuelven en los casos de uso.
"""

from pydantic import BaseModel


class ProductoCreate(BaseModel):
    """Datos para crear un producto."""

    # Nombre del producto.
    nombre: str
    # Descripción opcional; por defecto vacía.
    descripcion: str = ""
    # Categoría a la que pertenece (opcional).
    categoria_id: str | None = None
    # Imagen del producto (URL o base64); por defecto vacía.
    imagen: str = ""
    # Precio de venta; por defecto 0.0.
    precio: float = 0.0
    # Stock disponible (entero); por defecto 0.
    stock: int = 0
    # Tipo de producto; por defecto "comprado".
    tipo: str = "comprado"


class ProductoUpdate(BaseModel):
    """Datos para actualizar un producto (todos los campos opcionales)."""

    # Cada None indica "no modificar este campo".
    nombre: str | None = None
    descripcion: str | None = None
    categoria_id: str | None = None
    imagen: str | None = None
    precio: float | None = None
    stock: int | None = None
    tipo: str | None = None


class EstadoRequest(BaseModel):
    """Petición para cambiar el estado (activo/inactivo) de un producto."""

    # True = activo, False = inactivo.
    estado: bool
