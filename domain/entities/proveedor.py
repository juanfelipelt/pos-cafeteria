"""Entidad de dominio ``Proveedor``.

Un proveedor es la persona o empresa a la que se le compran productos e
insumos. Guardamos sus datos de contacto porque son necesarios para hacer
pedidos y para saber a quién reclamar.

Invariantes del negocio:
- El nombre, el contacto y el teléfono son obligatorios.
- El resto de los datos (email, dirección, identificación) son opcionales.
"""

from dataclasses import dataclass


@dataclass
class Proveedor:
    """Entidad de dominio para un proveedor."""

    # Identificador único; None mientras no se haya guardado.
    id: str | None = None
    # Nombre o razón social del proveedor (obligatorio).
    nombre: str = ""
    # Persona de contacto dentro del proveedor (obligatorio).
    contacto: str = ""
    # Teléfono de contacto (obligatorio).
    telefono: str = ""
    # Correo electrónico (opcional).
    email: str = ""
    # Dirección física (opcional).
    direccion: str = ""
    # Tipo de documento: CC, NIT, etc. (opcional).
    tipo_identificacion: str = ""
    # Número de documento (opcional).
    identificacion: str = ""
    # Borrado lógico: True = activo, False = desactivado.
    estado: bool = True

    def __post_init__(self) -> None:
        """Normaliza los textos y valida los campos obligatorios."""
        # Se eliminan espacios sobrantes en todos los campos de texto.
        self.nombre = self.nombre.strip() if self.nombre else ""
        self.contacto = self.contacto.strip() if self.contacto else ""
        self.telefono = self.telefono.strip() if self.telefono else ""
        self.email = self.email.strip() if self.email else ""
        self.direccion = self.direccion.strip() if self.direccion else ""
        self.tipo_identificacion = (
            self.tipo_identificacion.strip() if self.tipo_identificacion else ""
        )
        self.identificacion = self.identificacion.strip() if self.identificacion else ""

        # Datos mínimos para poder contactar al proveedor.
        if not self.nombre:
            raise ValueError("El nombre del proveedor es obligatorio.")
        if not self.contacto:
            raise ValueError("El contacto del proveedor es obligatorio.")
        if not self.telefono:
            raise ValueError("El teléfono del proveedor es obligatorio.")

    def cambiar_nombre(self, nuevo_nombre: str) -> None:
        """Cambia el nombre validando que no quede vacío."""
        if not nuevo_nombre or not nuevo_nombre.strip():
            raise ValueError("El nuevo nombre no puede estar vacío.")
        self.nombre = nuevo_nombre.strip()

    def cambiar_contacto(self, nuevo_contacto: str) -> None:
        """Cambia la persona de contacto validando que no quede vacía."""
        if not nuevo_contacto or not nuevo_contacto.strip():
            raise ValueError("El nuevo contacto no puede estar vacío.")
        self.contacto = nuevo_contacto.strip()

    def cambiar_telefono(self, nuevo_telefono: str) -> None:
        """Cambia el teléfono validando que no quede vacío."""
        if not nuevo_telefono or not nuevo_telefono.strip():
            raise ValueError("El nuevo teléfono no puede estar vacío.")
        self.telefono = nuevo_telefono.strip()

    def cambiar_email(self, nuevo_email: str) -> None:
        """Actualiza el email (opcional, puede quedar vacío)."""
        self.email = nuevo_email.strip() if nuevo_email else ""

    def cambiar_direccion(self, nueva_direccion: str) -> None:
        """Actualiza la dirección (opcional, puede quedar vacía)."""
        self.direccion = nueva_direccion.strip() if nueva_direccion else ""

    def cambiar_tipo_identificacion(self, nuevo_tipo: str) -> None:
        """Actualiza el tipo de identificación (opcional)."""
        self.tipo_identificacion = nuevo_tipo.strip() if nuevo_tipo else ""

    def cambiar_identificacion(self, nueva_identificacion: str) -> None:
        """Actualiza el número de identificación (opcional)."""
        self.identificacion = nueva_identificacion.strip() if nueva_identificacion else ""

    def desactivar(self) -> None:
        """Deshabilita el proveedor sin borrarlo (borrado lógico)."""
        self.estado = False

    def activar(self) -> None:
        """Vuelve a habilitar el proveedor."""
        self.estado = True

    def to_dict(self) -> dict:
        """Serializa el proveedor a un diccionario."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "contacto": self.contacto,
            "telefono": self.telefono,
            "email": self.email,
            "direccion": self.direccion,
            "tipo_identificacion": self.tipo_identificacion,
            "identificacion": self.identificacion,
            "estado": self.estado,
        }
