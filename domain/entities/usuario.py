from dataclasses import dataclass

from .enums import Rol


@dataclass
class Usuario:
    """Entidad de dominio para un usuario del sistema."""

    id: str | None = None
    nombre: str = ""
    email: str = ""
    contraseña_hash: str = ""
    rol: Rol = Rol.CAJERO
    estado: bool = True

    def __post_init__(self) -> None:
        if not self.nombre or not self.nombre.strip():
            raise ValueError("El nombre del usuario es obligatorio.")

        if not self.email or not self.email.strip():
            raise ValueError("El email del usuario es obligatorio.")

        if not self.contraseña_hash or not self.contraseña_hash.strip():
            raise ValueError("La contraseña del usuario es obligatoria.")

        self.nombre = self.nombre.strip()
        self.email = self.email.strip()

    @property
    def esta_activo(self) -> bool:
        return self.estado

    @property
    def es_admin(self) -> bool:
        return self.rol == Rol.ADMIN

    def desactivar(self) -> None:
        self.estado = False

    def activar(self) -> None:
        self.estado = True

    def cambiar_nombre(self, nuevo_nombre: str) -> None:
        if not nuevo_nombre or not nuevo_nombre.strip():
            raise ValueError("El nuevo nombre no puede estar vacío.")
        self.nombre = nuevo_nombre.strip()

    def cambiar_email(self, nuevo_email: str) -> None:
        if not nuevo_email or not nuevo_email.strip():
            raise ValueError("El nuevo email no puede estar vacío.")
        self.email = nuevo_email.strip()

    def cambiar_contraseña(self, nuevo_hash: str) -> None:
        if not nuevo_hash or not nuevo_hash.strip():
            raise ValueError("La nueva contraseña no puede estar vacía.")
        self.contraseña_hash = nuevo_hash.strip()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            "rol": self.rol.value,
            "estado": self.estado,
        }
