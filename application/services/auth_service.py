"""Servicio de autenticación y gestión de usuarios (caso de uso: "Auth").

¿Qué resuelve?
- Permitir a un usuario iniciar sesión entregando un token JWT.
- Registrar usuarios nuevos (con rol) de forma controlada.

¿Cómo usa los repositorios?
- Recibe un ``UsuarioRepository`` para leer/crear usuarios sin conocer la
  base de datos directamente (patrón repositorio).
- Recibe una ``Session`` de SQLAlchemy para confirmar (commit) los cambios
  que el repositorio deja preparados.

Este servicio pertenece a la capa de aplicación: orquesta reglas de negocio
y delega la persistencia en los repositorios.
"""

from sqlalchemy.orm import Session

from application.security.hashing import hash_password, verify_password
from application.security.jwt import create_access_token
from application.utils import new_id
from domain.entities.enums import Rol
from domain.entities.usuario import Usuario
from domain.exceptions import ConflictError, UnauthorizedError, ValidationError
from domain.repositories.usuario_repository import UsuarioRepository


class AuthService:
    """Orquesta el inicio de sesión y el registro de usuarios.

    Depende del repositorio de usuarios (para la persistencia) y de una
    sesión de base de datos (para confirmar los cambios).
    """

    def __init__(self, usuarios: UsuarioRepository, session: Session) -> None:
        """Guarda las dependencias del servicio.

        Parámetros:
            usuarios: repositorio que sabe leer y guardar usuarios.
            session: sesión de SQLAlchemy usada para hacer commit.
        """
        self.usuarios = usuarios
        self.session = session

    def login(self, email: str, password: str) -> str:
        """Valida credenciales y devuelve un token de acceso (JWT).

        Reglas de negocio:
        - Se normaliza el email (espacios y mayúsculas) para buscarlo.
        - Si el usuario no existe o está inactivo, se rechaza el acceso.
        - Si la contraseña no coincide con el hash guardado, se rechaza.

        Parámetros:
            email: correo con el que el usuario se identifica.
            password: contraseña en texto plano que se va a verificar.

        Retorna:
            El token JWT (cadena) que el cliente usará en sus peticiones.

        Lanza:
            UnauthorizedError: si las credenciales son inválidas.
        """
        # Se busca el usuario por email normalizado (sin espacios, en minúscula).
        usuario = self.usuarios.get_by_email(email.strip().lower())
        # No existe o está inactivo: por seguridad el mensaje es genérico.
        if usuario is None or not usuario.estado:
            raise UnauthorizedError("Credenciales inválidas.")
        # Se compara la contraseña escrita contra el hash almacenado.
        if not verify_password(password, usuario.contraseña_hash):
            raise UnauthorizedError("Credenciales inválidas.")
        # Credenciales correctas: se firma un token con id y rol del usuario.
        return create_access_token(usuario.id, usuario.rol.value)

    def registrar(
        self, nombre: str, email: str, password: str, rol: Rol = Rol.CAJERO
    ) -> Usuario:
        """Crea un usuario nuevo si los datos son válidos.

        Reglas de negocio:
        - El email se normaliza antes de guardarlo/buscarlo.
        - La contraseña debe tener al menos 8 caracteres.
        - No se permite repetir un email ya registrado.

        Parámetros:
            nombre: nombre visible del usuario.
            email: correo único de la cuenta.
            password: contraseña en texto plano (se guarda hasheada).
            rol: rol del usuario; por defecto es CAJERO.

        Retorna:
            El usuario recién creado y confirmado en base de datos.

        Lanza:
            ValidationError: si la contraseña es muy corta.
            ConflictError: si ya existe un usuario con ese email.
        """
        # Normalizamos el email para comparar y guardar de forma consistente.
        email_norm = email.strip().lower()
        # Validación mínima de seguridad sobre la contraseña.
        if len(password) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres.")
        # Evitamos cuentas duplicadas con el mismo email.
        if self.usuarios.get_by_email(email_norm) is not None:
            raise ConflictError("Ya existe un usuario con ese email.")
        # Se construye la entidad de dominio con la contraseña ya hasheada.
        usuario = Usuario(
            id=new_id(),
            nombre=nombre,
            email=email_norm,
            contraseña_hash=hash_password(password),
            rol=rol,
        )
        # El repositorio deja el usuario preparado y la sesión lo confirma.
        self.usuarios.add(usuario)
        self.session.commit()
        return usuario

    def obtener(self, usuario_id: str) -> Usuario | None:
        """Busca un usuario por su id.

        Parámetros:
            usuario_id: identificador del usuario.

        Retorna:
            El usuario encontrado o ``None`` si no existe.
        """
        return self.usuarios.get(usuario_id)

    def listar(self) -> list[Usuario]:
        """Devuelve todos los usuarios registrados.

        Retorna:
            Lista de usuarios.
        """
        return self.usuarios.list()
