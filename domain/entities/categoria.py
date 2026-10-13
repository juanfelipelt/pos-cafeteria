"""Entidad de dominio ``Categoria``.

Una categoría agrupa productos del negocio (por ejemplo: bebidas, postres,
almuerzos). Invariante principal: **toda categoría debe tener un nombre no
vacío**; esta regla se valida al crear el objeto en ``__post_init__`` y también
cada vez que se cambia el nombre.
"""

from dataclasses import dataclass


# ``@dataclass`` genera automáticamente el constructor, la igualdad, etc., a
# partir de los atributos declarados abajo.
@dataclass
class Categoria:
    """Representa una categoría a la que se pueden asociar productos."""

    # Identificador único. Es None mientras la categoría aún no se ha guardado.
    id: str | None = None
    # Nombre visible de la categoría (obligatorio).
    nombre: str = ""
    # Texto libre opcional que describe la categoría.
    descripcion: str = ""
    # Bandera de borrado lógico: True = activa, False = desactivada.
    estado: bool = True

    def __post_init__(self) -> None:
        """Valida las invariantes justo después de construir la categoría.

        Se ejecuta solo al crear el objeto. Comprueba que el nombre exista y no
        sea solo espacios en blanco.
        """
        # ``strip()`` quita espacios al inicio y al final; si queda vacío, es error.
        if self.nombre is None or not self.nombre.strip():
            raise ValueError("El nombre de la categoría es obligatorio.")

    def cambiar_nombre(self, nuevo_nombre: str) -> None:
        """Cambia el nombre de la categoría garantizando que no quede vacío."""
        if not nuevo_nombre or not nuevo_nombre.strip():
            raise ValueError("El nuevo nombre no puede estar vacío.")
        # Se guarda el nombre ya "limpio" (sin espacios extremos).
        self.nombre = nuevo_nombre.strip()

    def cambiar_descripcion(self, nueva_descripcion: str) -> None:
        """Actualiza la descripción. Si viene vacía o None, se deja en blanco."""
        self.descripcion = nueva_descripcion.strip() if nueva_descripcion else ""

    def desactivar(self) -> None:
        """Marca la categoría como inactiva (borrado lógico, no se elimina)."""
        self.estado = False

    def activar(self) -> None:
        """Vuelve a marcar la categoría como activa."""
        self.estado = True

    def to_dict(self) -> dict:
        """Convierte la categoría a un diccionario simple (para APIs/persistencia)."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "estado": self.estado,
        }