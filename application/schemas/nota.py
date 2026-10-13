"""Schemas (DTOs) de notas.

Las notas son mensajes o recordatorios internos del negocio. Estos modelos
describen los datos de entrada/salida para crearlas y actualizarlas.

Son DTOs: validan y transportan datos; las reglas de negocio viven en los
casos de uso.
"""

from pydantic import BaseModel


class NotaCreate(BaseModel):
    """Datos para crear una nota."""

    # Texto de la nota.
    texto: str
    # Tipo de nota; por defecto "nota".
    tipo: str = "nota"
    # A quién va dirigida; por defecto "todos".
    destinatario: str = "todos"
    # Prioridad; por defecto "normal".
    prioridad: str = "normal"


class NotaUpdate(BaseModel):
    """Datos para actualizar una nota (campos opcionales)."""

    # Cada None indica "no modificar este campo".
    texto: str | None = None
    tipo: str | None = None
    destinatario: str | None = None
    prioridad: str | None = None
    # Marca si la nota/tarea ya se realizó.
    hecho: bool | None = None
    # Marca si la nota fue archivada.
    archivada: bool | None = None
