from abc import ABC, abstractmethod

from domain.entities.usuario import Usuario


class UsuarioRepository(ABC):
    @abstractmethod
    def get(self, id: str) -> Usuario | None:
        ...

    @abstractmethod
    def get_by_email(self, email: str) -> Usuario | None:
        ...

    @abstractmethod
    def list(self) -> list[Usuario]:
        ...

    @abstractmethod
    def add(self, usuario: Usuario) -> Usuario:
        ...

    @abstractmethod
    def update(self, usuario: Usuario) -> Usuario:
        ...
