from __future__ import annotations
from sqlalchemy.orm import Session

from domain.entities.enums import Rol
from domain.entities.usuario import Usuario
from domain.repositories.usuario_repository import UsuarioRepository
from infrastructure.models.usuario import UsuarioModel


def _to_entity(m: UsuarioModel) -> Usuario:
    return Usuario(
        id=m.id,
        nombre=m.nombre,
        email=m.email,
        contraseña_hash=m.contraseña_hash,
        rol=Rol(m.rol),
        estado=m.estado,
    )


class SQLAlchemyUsuarioRepository(UsuarioRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: str) -> Usuario | None:
        m = self.session.get(UsuarioModel, id)
        return _to_entity(m) if m else None

    def get_by_email(self, email: str) -> Usuario | None:
        m = (
            self.session.query(UsuarioModel)
            .filter(UsuarioModel.email == email)
            .first()
        )
        return _to_entity(m) if m else None

    def list(self) -> list[Usuario]:
        return [_to_entity(m) for m in self.session.query(UsuarioModel).all()]

    def add(self, usuario: Usuario) -> Usuario:
        m = UsuarioModel(
            id=usuario.id,
            nombre=usuario.nombre,
            email=usuario.email,
            contraseña_hash=usuario.contraseña_hash,
            rol=usuario.rol.value,
            estado=usuario.estado,
        )
        self.session.add(m)
        self.session.flush()
        return usuario

    def update(self, usuario: Usuario) -> Usuario:
        m = self.session.get(UsuarioModel, usuario.id)
        m.nombre = usuario.nombre
        m.email = usuario.email
        m.contraseña_hash = usuario.contraseña_hash
        m.rol = usuario.rol.value
        m.estado = usuario.estado
        self.session.flush()
        return usuario
