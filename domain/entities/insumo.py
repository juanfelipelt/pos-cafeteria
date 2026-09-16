from dataclasses import dataclass


@dataclass
class Insumo:
    """Entidad de dominio para un insumo (materia prima)."""

    id: str | None = None
    nombre: str = ""
    unidad: str = ""
    stock: float = 0.0
    costo_unitario: float = 0.0
    proveedor_id: str | None = None
    estado: bool = True

    def __post_init__(self) -> None:
        self.nombre = self.nombre.strip() if self.nombre else ""
        self.unidad = self.unidad.strip() if self.unidad else ""
        self.proveedor_id = self.proveedor_id.strip() if self.proveedor_id else None

        if not self.nombre:
            raise ValueError("El nombre del insumo es obligatorio.")
        if not self.unidad:
            raise ValueError("La unidad del insumo es obligatoria.")
        if self.stock < 0:
            raise ValueError("El stock del insumo no puede ser negativo.")
        if self.costo_unitario < 0:
            raise ValueError("El costo del insumo no puede ser negativo.")

    def cambiar_nombre(self, nuevo_nombre: str) -> None:
        if not nuevo_nombre or not nuevo_nombre.strip():
            raise ValueError("El nombre del insumo no puede estar vacío.")
        self.nombre = nuevo_nombre.strip()

    def cambiar_unidad(self, nueva_unidad: str) -> None:
        if not nueva_unidad or not nueva_unidad.strip():
            raise ValueError("La unidad del insumo no puede estar vacía.")
        self.unidad = nueva_unidad.strip()

    def cambiar_proveedor_id(self, nuevo_proveedor_id: str | None) -> None:
        self.proveedor_id = (
            nuevo_proveedor_id.strip() if nuevo_proveedor_id else None
        )

    def desactivar(self) -> None:
        self.estado = False

    def activar(self) -> None:
        self.estado = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "unidad": self.unidad,
            "stock": self.stock,
            "costo_unitario": self.costo_unitario,
            "proveedor_id": self.proveedor_id,
            "estado": self.estado,
        }
