"""Entidad de dominio ``Configuracion``.

Es un simple par **clave → valor** que guarda ajustes generales del negocio
que no encajan en otras entidades, por ejemplo el logo, el nombre comercial
o el IVA. Es intencionalmente flexible: agregar una nueva configuración no
requiere crear una nueva entidad, solo una nueva clave.
"""

from dataclasses import dataclass


@dataclass
class Configuracion:
    """Par clave-valor de configuración del negocio (p. ej. logo)."""

    # Nombre del ajuste, por ejemplo "nombre_negocio" o "logo".
    clave: str
    # Valor del ajuste, almacenado como texto. Por defecto queda vacío.
    valor: str = ""
