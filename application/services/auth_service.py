from sqlalchemy.orm import Session

from application.security.hashing import hash_password, verify_password
from application.security.jwt import create_access_token
from application.utils import new_id
from domain.entities.enums import Rol
from domain.entities.usuario import Usuario
from domain.exceptions import ConflictError, UnauthorizedError, ValidationError
from domain.repositories.usuario_repository import UsuarioRepository


class AuthService:
    def __init__(self, usuarios: UsuarioRepository, session: Session) -> None:
        self.usuarios = usuarios
        self.session = session

    def login(self, email: str, password: str) -> str:
        usuario = self.usuarios.get_by_email(email.strip().lower())
        if usuario is None or not usuario.estado:
            raise UnauthorizedError("Credenciales inválidas.")
        if not verify_password(password, usuario.contraseña_hash):
            raise UnauthorizedError("Credenciales inválidas.")
        return create_access_token(usuario.id, usuario.rol.value)

    def registrar(
        self, nombre: str, email: str, password: str, rol: Rol = Rol.CAJERO
    ) -> Usuario:
        email_norm = email.strip().lower()
        if len(password) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres.")
        if self.usuarios.get_by_email(email_norm) is not None:
            raise ConflictError("Ya existe un usuario con ese email.")
        usuario = Usuario(
            id=new_id(),
            nombre=nombre,
            email=email_norm,
            contraseña_hash=hash_password(password),
            rol=rol,
        )
        self.usuarios.add(usuario)
        self.session.commit()
        return usuario

    def obtener(self, usuario_id: str) -> Usuario | None:
        return self.usuarios.get(usuario_id)

    def listar(self) -> list[Usuario]:
        return self.usuarios.list()
