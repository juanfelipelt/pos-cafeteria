"""Utilidades generales reutilizables por toda la aplicación.

Por ahora contiene una única función de apoyo: ``new_id()``, que genera
identificadores únicos para las entidades (productos, usuarios, etc.).

Se relaciona con prácticamente todos los módulos que necesitan crear registros
con un identificador nuevo (por ejemplo, ``app.py`` al crear el admin inicial o
los servicios al dar de alta entidades).
"""

import uuid


def new_id() -> str:
    """Genera un identificador único en formato de 32 caracteres hexadecimales.

    Usa ``uuid.uuid4()`` (UUID versión 4, aleatorio) y lo convierte a cadena sin
    guiones mediante ``.hex``. Es la forma estándar de crear IDs de negocio en
    esta aplicación.

    Retorno:
        str: cadena hexadecimal de 32 caracteres (sin guiones) que identifica
        un registro de forma única.
    """
    return uuid.uuid4().hex
