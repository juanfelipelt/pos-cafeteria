"""Puerto (interfaz) de repositorio para ``Configuracion``.

Contrato para leer y escribir los ajustes clave-valor del negocio. Se usa un
método ``set`` (en vez de ``add``/``update``) porque una configuración es
idempotente: guardar la misma clave dos veces simplemente sobrescribe el valor.
"""

from __future__ import annotations
from abc import ABC, abstractmethod

from domain.entities.configuracion import Configuracion


class ConfiguracionRepository(ABC):
    """Contrato de acceso a datos de la configuración del negocio."""

    @abstractmethod
    def get(self, clave: str) -> Configuracion | None:
        """Busca una configuración por su clave. Devuelve None si no existe."""
        ...

    @abstractmethod
    def set(self, clave: str, valor: str) -> Configuracion:
        """Crea o actualiza el valor asociado a una clave y lo devuelve."""
        ...

    @abstractmethod
    def list(self) -> list[Configuracion]:
        """Devuelve todas las configuraciones guardadas."""
        ...
