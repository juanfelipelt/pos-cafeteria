"""Schemas (DTOs) de proveedores.

Un proveedor es la empresa o persona que abastece productos o insumos al
negocio. Estos modelos describen los datos de entrada/salida para gestionarlos.

Son DTOs: solo validan y transportan datos; las reglas de negocio viven en los
casos de uso.
"""

from pydantic import BaseModel


class ProveedorCreate(BaseModel):
    """Datos para crear un proveedor."""

    # Nombre o razón social.
    nombre: str
    # Persona de contacto.
    contacto: str
    # Teléfono de contacto.
    telefono: str
    # Correo electrónico; por defecto vacío.
    email: str = ""
    # Dirección física; por defecto vacía.
    direccion: str = ""
    # Tipo de documento (NIT, CC, etc.); por defecto vacío.
    tipo_identificacion: str = ""
    # Número de identificación; por defecto vacío.
    identificacion: str = ""


class ProveedorUpdate(BaseModel):
    """Datos para actualizar un proveedor (todos los campos opcionales)."""

    # Cada None indica "no modificar este campo".
    nombre: str | None = None
    contacto: str | None = None
    telefono: str | None = None
    email: str | None = None
    direccion: str | None = None
    tipo_identificacion: str | None = None
    identificacion: str | None = None
