from dataclasses import dataclass, field
from datetime import datetime

from .detalle_venta import DetalleVenta
from .pago import Pago


@dataclass
class Venta:
    """Entidad de dominio para una venta en el sistema."""

    detalles: list[DetalleVenta] = field(default_factory=list)
    id: str | None = None
    usuario_id: str | None = None
    fecha: datetime = field(default_factory=datetime.now)
    pagos: list[Pago] = field(default_factory=list)
    anulada: bool = False

    def __post_init__(self) -> None:
        if not self.detalles:
            raise ValueError("La venta debe tener al menos un detalle.")

    @property
    def total(self) -> float:
        return sum(detalle.subtotal for detalle in self.detalles)

    @property
    def total_pagado(self) -> float:
        return sum(pago.monto for pago in self.pagos)

    @property
    def pendiente(self) -> float:
        return max(0.0, self.total - self.total_pagado)

    @property
    def esta_pagada(self) -> bool:
        return self.total_pagado >= self.total

    def agregar_detalle(self, detalle: DetalleVenta) -> None:
        self.detalles.append(detalle)

    def registrar_pago(self, pago: Pago) -> None:
        if self.anulada:
            raise ValueError("No se puede registrar un pago a una venta anulada.")
        if pago.monto <= 0:
            raise ValueError("El monto del pago debe ser mayor que cero.")
        if self.total_pagado + pago.monto > self.total:
            raise ValueError("El pago excede el total de la venta.")
        self.pagos.append(pago)

    def anular(self) -> None:
        if self.anulada:
            raise ValueError("La venta ya está anulada.")
        self.anulada = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "fecha": self.fecha.isoformat(),
            "detalles": [detalle.to_dict() for detalle in self.detalles],
            "pagos": [pago.to_dict() for pago in self.pagos],
            "total": self.total,
            "total_pagado": self.total_pagado,
            "pendiente": self.pendiente,
            "esta_pagada": self.esta_pagada,
            "anulada": self.anulada,
        }
