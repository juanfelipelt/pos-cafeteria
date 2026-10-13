"""Entidad de dominio ``Usuario``.

Representa a una persona que puede entrar al sistema, junto con su rol
(administrador o cajero). Por seguridad, **nunca se guarda la contraseña en
texto plano**: solo se almacena su *hash* (una versión cifrada e irreversible).

Invariantes del negocio:
- El nombre, el email y el hash de la contraseña son obligatorios.
"""

from dataclasses import dataclass

from .enums import Rol


@dataclass
class Usuario:
    """Entidad de dominio para un usuario del sistema."""

    # Identificador único; None mientras no se haya guardado.
    id: str | None = None
    # Nombre completo del usuario (obligatorio).
    nombre: str = ""
    # Correo electrónico, usado como nombre de usuario (obligatorio).
    email: str = ""
    # Contraseña ya cifrada (hash). Nunca se guarda la contraseña original.
    contraseña_hash: str = ""
    # Rol asignado. Por defecto, cajero (el de menores permisos).
    rol: Rol = Rol.CAJERO
    # True = usuario habilitado, False = desactivado.
    estado: bool = True

    def __post_init__(self) -> None:
        """Valida los campos obligatorios y normaliza los textos."""
        if not self.nombre or not self.nombre.strip():
            raise ValueError("El nombre del usuario es obligatorio.")

        if not self.email or not self.email.strip():
            raise ValueError("El email del usuario es obligatorio.")

        # Sin hash no habría forma de validar el inicio de sesión.
        if not self.contraseña_hash or not self.contraseña_hash.strip():
            raise ValueError("La contraseña del usuario es obligatoria.")

        # Se guardan limpios (sin espacios extremos).
        self.nombre = self.nombre.strip()
        self.email = self.email.strip()

    @property
    def esta_activo(self) -> bool:
        """Indica si el usuario está habilitado para usar el sistema."""
        return self.estado

    @property
    def es_admin(self) -> bool:
        """Indica si el usuario tiene el rol de administrador."""
        return self.rol == Rol.ADMIN

    def desactivar(self) -> None:
        """Deshabilita al usuario (por ejemplo, cuando deja la empresa)."""
        self.estado = False

    def activar(self) -> None:
        """Vuelve a habilitar al usuario."""
        self.estado = True

    def cambiar_nombre(self, nuevo_nombre: str) -> None:
        """Cambia el nombre validando que no quede vacío."""
        if not nuevo_nombre or not nuevo_nombre.strip():
            raise ValueError("El nuevo nombre no puede estar vacío.")
        self.nombre = nuevo_nombre.strip()

    def cambiar_email(self, nuevo_email: str) -> None:
        """Cambia el email validando que no quede vacío."""
        if not nuevo_email or not nuevo_email.strip():
            raise ValueError("El nuevo email no puede estar vacío.")
        self.email = nuevo_email.strip()

    def cambiar_contraseña(self, nuevo_hash: str) -> None:
        """Cambia el hash de la contraseña validando que no quede vacío."""
        if not nuevo_hash or not nuevo_hash.strip():
            raise ValueError("La nueva contraseña no puede estar vacía.")
        self.contraseña_hash = nuevo_hash.strip()

    def to_dict(self) -> dict:
        """Serializa el usuario a un diccionario.

        Importante: **no** se incluye ``contraseña_hash`` para no exponer
        información sensible al enviar el usuario a la API.
        """
        return {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            # ``.value`` convierte el enum Rol a su texto ("admin"/"cajero").
            "rol": self.rol.value,
            "estado": self.estado,
        }
