from dataclasses import dataclass


@dataclass
class Configuracion:
    """Par clave-valor de configuración del negocio (p. ej. logo)."""

    clave: str
    valor: str = ""
