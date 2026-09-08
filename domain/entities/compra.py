from dataclasses import dataclass, field
from datetime import datetime

from .detalle_compra import DetalleCompra


@dataclass
class Compra:
    """Entidad de dominio para una compra a proveedor."""

    proveedor_id: str
    detalles: list[DetalleCompra] = field(default_factory=list)
    id: str | None = None
    fecha: datetime = field(default_factory=datetime.now)
    anulada: bool = False

    def __post_init__(self) -> None:
        if not self.proveedor_id:
            raise ValueError("El proveedor es obligatorio.")

        if not self.detalles:
            raise ValueError("La compra debe tener al menos un detalle.")

    @property
    def total(self) -> float:
        return sum(detalle.subtotal for detalle in self.detalles)

    def agregar_detalle(self, detalle: DetalleCompra) -> None:
        self.detalles.append(detalle)

    def anular(self) -> None:
        if self.anulada:
            raise ValueError("La compra ya está anulada.")
        self.anulada = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "proveedor_id": self.proveedor_id,
            "fecha": self.fecha.isoformat(),
            "detalles": [detalle.to_dict() for detalle in self.detalles],
            "total": self.total,
            "anulada": self.anulada,
        }
