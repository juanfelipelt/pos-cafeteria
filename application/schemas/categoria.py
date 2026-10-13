"""Schemas (DTOs) de categorías de productos.

Una categoría clasifica los productos (por ejemplo: bebidas, comidas).
Aquí solo se describen los datos que entran o salen de la API; la lógica de
negocio se ubica en los casos de uso.

- `CategoriaCreate` se usa al crear una categoría nueva.
- `CategoriaUpdate` se usa al actualizar; todos los campos son opcionales
  para permitir actualizaciones parciales (PATCH).
"""

from pydantic import BaseModel


class CategoriaCreate(BaseModel):
    """Datos para crear una categoría."""

    # Nombre de la categoría (obligatorio).
    nombre: str
    # Descripción opcional; si no se envía queda vacía.
    descripcion: str = ""


class CategoriaUpdate(BaseModel):
    """Datos para actualizar una categoría (todos los campos opcionales)."""

    # None significa "no modificar este campo".
    nombre: str | None = None
    # None significa "no modificar este campo".
    descripcion: str | None = None
