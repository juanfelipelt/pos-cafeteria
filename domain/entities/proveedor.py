from dataclasses import dataclass


@dataclass
class Proveedor:
    """Entidad de dominio para un proveedor."""

    id: str | None = None
    nombre: str = ""
    contacto: str = ""
    telefono: str = ""
    email: str = ""
    direccion: str = ""
    estado: bool = True

    def __post_init__(self) -> None:
        self.nombre = self.nombre.strip() if self.nombre else ""
        self.contacto = self.contacto.strip() if self.contacto else ""
        self.telefono = self.telefono.strip() if self.telefono else ""
        self.email = self.email.strip() if self.email else ""
        self.direccion = self.direccion.strip() if self.direccion else ""

        if not self.nombre:
            raise ValueError("El nombre del proveedor es obligatorio.")
        if not self.contacto:
            raise ValueError("El contacto del proveedor es obligatorio.")
        if not self.telefono:
            raise ValueError("El teléfono del proveedor es obligatorio.")

    def cambiar_nombre(self, nuevo_nombre: str) -> None:
        if not nuevo_nombre or not nuevo_nombre.strip():
            raise ValueError("El nuevo nombre no puede estar vacío.")
        self.nombre = nuevo_nombre.strip()

    def cambiar_contacto(self, nuevo_contacto: str) -> None:
        if not nuevo_contacto or not nuevo_contacto.strip():
            raise ValueError("El nuevo contacto no puede estar vacío.")
        self.contacto = nuevo_contacto.strip()

    def cambiar_telefono(self, nuevo_telefono: str) -> None:
        if not nuevo_telefono or not nuevo_telefono.strip():
            raise ValueError("El nuevo teléfono no puede estar vacío.")
        self.telefono = nuevo_telefono.strip()

    def cambiar_email(self, nuevo_email: str) -> None:
        self.email = nuevo_email.strip() if nuevo_email else ""

    def cambiar_direccion(self, nueva_direccion: str) -> None:
        self.direccion = nueva_direccion.strip() if nueva_direccion else ""

    def desactivar(self) -> None:
        self.estado = False

    def activar(self) -> None:
        self.estado = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "contacto": self.contacto,
            "telefono": self.telefono,
            "email": self.email,
            "direccion": self.direccion,
            "estado": self.estado,
        }
