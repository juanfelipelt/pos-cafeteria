"""Puerto (interfaz) de repositorio para ``Usuario``.

Contrato de guardado y consulta de los usuarios. Incluye la búsqueda por
email porque es la forma habitual de identificar a un usuario al iniciar
sesión.
"""

from __future__ import annotations
from abc import ABC, abstractmethod

from domain.entities.usuario import Usuario


class UsuarioRepository(ABC):
    """Contrato de acceso a datos de los usuarios."""

    @abstractmethod
    def get(self, id: str) -> Usuario | None:
        """Busca un usuario por su id. Devuelve None si no existe."""
        ...

    @abstractmethod
    def get_by_email(self, email: str) -> Usuario | None:
        """Busca un usuario por su email. Devuelve None si no existe."""
        ...

    @abstractmethod
    def list(self) -> list[Usuario]:
        """Devuelve la lista completa de usuarios."""
        ...

    @abstractmethod
    def add(self, usuario: Usuario) -> Usuario:
        """Guarda un nuevo usuario y lo devuelve con su id asignado."""
        ...

    @abstractmethod
    def update(self, usuario: Usuario) -> Usuario:
        """Actualiza un usuario existente y devuelve el resultado."""
        ...
