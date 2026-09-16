from dataclasses import dataclass


@dataclass
class CostoFijo:
    """Entidad de dominio para un costo fijo mensual del negocio."""

    nombre: str
    monto: float = 0.0
    id: str | None = None
    activo: bool = True

    def __post_init__(self) -> None:
        self.nombre = self.nombre.strip() if self.nombre else ""
        if not self.nombre:
            raise ValueError("El nombre del costo fijo es obligatorio.")
        if self.monto < 0:
            raise ValueError("El monto del costo fijo no puede ser negativo.")

    def cambiar_nombre(self, nuevo_nombre: str) -> None:
        if not nuevo_nombre or not nuevo_nombre.strip():
            raise ValueError("El nombre del costo fijo no puede estar vacío.")
        self.nombre = nuevo_nombre.strip()

    def cambiar_monto(self, nuevo_monto: float) -> None:
        if nuevo_monto < 0:
            raise ValueError("El monto del costo fijo no puede ser negativo.")
        self.monto = nuevo_monto

    def activar(self) -> None:
        self.activo = True

    def desactivar(self) -> None:
        self.activo = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "monto": self.monto,
            "activo": self.activo,
        }
