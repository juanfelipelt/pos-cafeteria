"""Schemas (DTOs) de configuración del sistema.

Se usan para actualizar valores de configuración general del negocio, por
ejemplo el logo o parámetros almacenados como texto.

Son DTOs simples: transportan y validan datos de entrada/salida sin contener
reglas de negocio.
"""

from pydantic import BaseModel


class LogoUpdate(BaseModel):
    """Datos para actualizar el logo del negocio."""

    # Contenido del logo (por ejemplo, una cadena en base64 o una URL).
    logo: str


class ConfiguracionUpdate(BaseModel):
    """Actualización de un valor de configuración cualquiera."""

    # Nuevo valor que se asignará a la configuración.
    valor: str
