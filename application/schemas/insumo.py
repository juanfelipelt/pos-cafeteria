"""Schemas (DTOs) de insumos.

Los insumos son las materias primas o ingredientes usados para elaborar
productos (harina, queso, etc.). Estos modelos describen los datos de
entrada/salida para gestionarlos.

Son DTOs: solo validan y transportan datos; la lógica de negocio (por ejemplo
descontar stock) se maneja en los casos de uso.
"""

from pydantic import BaseModel


class InsumoCreate(BaseModel):
    """Datos para crear un insumo."""

    # Nombre del insumo.
    nombre: str
    # Unidad de medida (kg, litros, unidades, etc.).
    unidad: str
    # Cantidad disponible; por defecto 0.0.
    stock: float = 0.0
    # Costo por unidad; por defecto 0.0.
    costo_unitario: float = 0.0
    # Proveedor asociado (opcional).
    proveedor_id: str | None = None


class InsumoUpdate(BaseModel):
    """Datos para actualizar un insumo (todos los campos opcionales)."""

    # Cada None indica "no modificar este campo".
    nombre: str | None = None
    unidad: str | None = None
    stock: float | None = None
    costo_unitario: float | None = None
    proveedor_id: str | None = None


class InsumoEstadoRequest(BaseModel):
    """Petición para cambiar el estado (activo/inactivo) de un insumo."""

    # True = activo, False = inactivo.
    estado: bool
