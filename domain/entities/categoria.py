from dataclasses import dataclass

@dataclass
class Categoria:
    """Entidad de dominio para una categoría de producto."""

    id: str | None = None
    nombre: str = ""
    descripcion: str = ""
    estado: bool = True

    def __post_init__(self) -> None:
        if self.nombre is None or not self.nombre.strip():
            raise ValueError("El nombre de la categoría es obligatorio.")

    def cambiar_nombre(self, nuevo_nombre: str) -> None:
        if not nuevo_nombre or not nuevo_nombre.strip():
            raise ValueError("El nuevo nombre no puede estar vacío.")
        self.nombre = nuevo_nombre.strip()

    def cambiar_descripcion(self, nueva_descripcion: str) -> None:
        self.descripcion = nueva_descripcion.strip() if nueva_descripcion else ""

    def desactivar(self) -> None:
        self.estado = False

    def activar(self) -> None:
        self.estado = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "estado": self.estado,
        }