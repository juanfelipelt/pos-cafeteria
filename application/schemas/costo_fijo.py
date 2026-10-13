"""Schemas (DTOs) de costos fijos.

Los costos fijos son gastos que no dependen de cuánto se venda (arriendo,
servicios, sueldos, etc.). Estos modelos describen los datos de entrada/salida
para administrarlos.

Como todos los schemas del proyecto, son DTOs: solo validan y transportan
datos; las reglas de negocio viven en los casos de uso.
"""

from pydantic import BaseModel


class CostoFijoCreate(BaseModel):
    """Datos para crear un costo fijo."""

    # Nombre descriptivo (p. ej. "Arriendo").
    nombre: str
    # Monto del costo; por defecto 0.0.
    monto: float = 0.0


class CostoFijoUpdate(BaseModel):
    """Datos para actualizar un costo fijo (campos opcionales)."""

    # None = no modificar.
    nombre: str | None = None
    # None = no modificar.
    monto: float | None = None
    # None = no modificar; permite activar o desactivar el costo.
    activo: bool | None = None
