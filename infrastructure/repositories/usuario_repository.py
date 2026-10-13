"""Repositorio SQLAlchemy para los usuarios.

Implementa `UsuarioRepository` del dominio sobre la tabla `usuarios`. Además
de las operaciones básicas, permite buscar por email (usado al iniciar sesión)
y convierte el rol entre texto (BD) y el enum `Rol` (dominio).
"""

from __future__ import annotations
from sqlalchemy.orm import Session

from domain.entities.enums import Rol
from domain.entities.usuario import Usuario
from domain.repositories.usuario_repository import UsuarioRepository
from infrastructure.models.usuario import UsuarioModel


def _to_entity(m: UsuarioModel) -> Usuario:
    """Convierte un modelo ORM `UsuarioModel` en la entidad `Usuario`.

    El rol se guarda en la BD como texto y aquí se transforma al enum `Rol`.
    """
    return Usuario(
        id=m.id,
        nombre=m.nombre,
        email=m.email,
        contraseña_hash=m.contraseña_hash,
        rol=Rol(m.rol),
        estado=m.estado,
    )


class SQLAlchemyUsuarioRepository(UsuarioRepository):
    """Implementación concreta de `UsuarioRepository` con SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: str) -> Usuario | None:
        """Busca un usuario por id. None si no existe."""
        m = self.session.get(UsuarioModel, id)
        return _to_entity(m) if m else None

    def get_by_email(self, email: str) -> Usuario | None:
        """Busca un usuario por email (se usa en el login). None si no existe."""
        m = (
            self.session.query(UsuarioModel)
            .filter(UsuarioModel.email == email)
            .first()
        )
        return _to_entity(m) if m else None

    def list(self) -> list[Usuario]:
        """Devuelve todos los usuarios."""
        return [_to_entity(m) for m in self.session.query(UsuarioModel).all()]

    def add(self, usuario: Usuario) -> Usuario:
        """Registra un nuevo usuario."""
        m = UsuarioModel(
            id=usuario.id,
            nombre=usuario.nombre,
            email=usuario.email,
            contraseña_hash=usuario.contraseña_hash,
            rol=usuario.rol.value,  # El enum se guarda como su texto (ej.: "cajero").
            estado=usuario.estado,
        )
        self.session.add(m)
        self.session.flush()
        return usuario

    def update(self, usuario: Usuario) -> Usuario:
        """Actualiza un usuario existente con los datos de la entidad."""
        m = self.session.get(UsuarioModel, usuario.id)
        m.nombre = usuario.nombre
        m.email = usuario.email
        m.contraseña_hash = usuario.contraseña_hash
        m.rol = usuario.rol.value  # Guardamos el enum como texto en la BD.
        m.estado = usuario.estado
        self.session.flush()
        return usuario
